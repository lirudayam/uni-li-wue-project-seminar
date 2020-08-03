import logging
import os
import re
import threading

from google.cloud import bigquery
from requests import Session

from DWConfigs import DWConfigs
from KafkaConnector import catch_request_error, KafkaConnector, get_unix_timestamp

os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = "/home/pjs/python_fetchers/googlebigquerytoken.json"


class GoogleBigQueryDataFetcher:
    fetcher_name = "Google Big Query Data Fetcher"
    kafka_topic = "RAW_G_GINI"
    sub_kafka_topic = "RAW_G_RICH_ACC"

    def __init__(self):
        self.client = bigquery.Client()
        self.trigger_health_pings()
        self.process_data_fetch()
        logging.info('Successful init')

    # Supporting methods
    def send_health_pings(self):
        KafkaConnector().send_health_ping(self.fetcher_name)
        self.trigger_health_pings()

    def trigger_health_pings(self):
        s = threading.Timer(DWConfigs().get_health_ping_interval(self.kafka_topic), self.send_health_pings, [], {})
        s.start()

    def calc_eth_gini(self):
        query_job = self.client.query("""with
double_entry_book as (
    -- debits
    select to_address as address, value as value, block_timestamp
    from `bigquery-public-data.crypto_ethereum.traces`
    where to_address is not null
    and status = 1
    and (call_type not in ('delegatecall', 'callcode', 'staticcall') or call_type is null)
    union all
    -- credits
    select from_address as address, -value as value, block_timestamp
    from `bigquery-public-data.crypto_ethereum.traces`
    where from_address is not null
    and status = 1
    and (call_type not in ('delegatecall', 'callcode', 'staticcall') or call_type is null)
    union all
    -- transaction fees debits
    select miner as address, sum(cast(receipt_gas_used as numeric) * cast(gas_price as numeric)) as value, block_timestamp
    from `bigquery-public-data.crypto_ethereum.transactions` as transactions
    join `bigquery-public-data.crypto_ethereum.blocks` as blocks on blocks.number = transactions.block_number
    group by blocks.miner, block_timestamp
    union all
    -- transaction fees credits
    select from_address as address, -(cast(receipt_gas_used as numeric) * cast(gas_price as numeric)) as value, block_timestamp
    from `bigquery-public-data.crypto_ethereum.transactions`
)
,double_entry_book_by_date as (
    select
        date(block_timestamp) as date,
        address,
        sum(value / POWER(10,0)) as value
    from double_entry_book
    group by address, date
)
,daily_balances_with_gaps as (
    select
        address,
        date,
        sum(value) over (partition by address order by date) as balance,
        lead(date, 1, current_date()) over (partition by address order by date) as next_date
        from double_entry_book_by_date
)
,calendar as (
    select date from unnest(generate_date_array(DATE_SUB(current_date(), INTERVAL 1 WEEK), current_date())) as date
)
,daily_balances as (
    select address, calendar.date, balance
    from daily_balances_with_gaps
    join calendar on daily_balances_with_gaps.date <= calendar.date and calendar.date < daily_balances_with_gaps.next_date
)
,supply as (
    select
        date,
        sum(balance) as daily_supply
    from daily_balances
    group by date
)
,ranked_daily_balances as (
    select
        daily_balances.date,
        balance,
        row_number() over (partition by daily_balances.date order by balance desc) as rank
    from daily_balances
    join supply on daily_balances.date = supply.date
    where safe_divide(balance, daily_supply) >= 0.0001
    ORDER BY safe_divide(balance, daily_supply) DESC
)

select
    date,
    1 - 2 * sum((balance * (rank - 1) + balance / 2)) / count(*) / sum(balance) as gini
from ranked_daily_balances
group by date
order by date asc""")
        results = query_job.result()  # Waits for job to complete.

        for row in results:
            try:
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "date": row.date.strftime("%Y-%m-%d"),
                    "coin": "ETH",
                    "gini": row.gini * 1.0
                })
            except Exception:
                catch_request_error({
                    "error": "Couldn't calculate Gini for Ethereum"
                }, self.kafka_topic)

    def calc_btc_gini(self):
        query_job = self.client.query("""with
double_entry_book as (
    select
        array_to_string(outputs.addresses,',') as address,
        value, block_timestamp
    from `bigquery-public-data.crypto_bitcoin.transactions` join unnest(outputs) as outputs
    union all
    select
        array_to_string(inputs.addresses,',') as address,
        -value as value, block_timestamp
    from `bigquery-public-data.crypto_bitcoin.transactions` join unnest(inputs) as inputs
),
double_entry_book_by_date as (
    select
        date(block_timestamp) as date,
        address,
        sum(value * 0.00000001) as value
    from double_entry_book
    group by address, date
),
daily_balances_with_gaps as (
    select
        address,
        date,
        sum(value) over (partition by address order by date) as balance,
        lead(date, 1, current_date()) over (partition by address order by date) as next_date
        from double_entry_book_by_date
),
calendar as (
    select date from unnest(generate_date_array(DATE_SUB(current_date(), INTERVAL 1 WEEK), current_date())) as date
),
daily_balances as (
    select address, calendar.date, balance
    from daily_balances_with_gaps
    join calendar on daily_balances_with_gaps.date <= calendar.date and calendar.date < daily_balances_with_gaps.next_date
    where balance > 1
),
address_counts as (
    select
        date,
        count(*) as address_count
    from
        daily_balances
    group by date
),
daily_balances_sampled as (
    select address, daily_balances.date, balance
    from daily_balances
    join address_counts on daily_balances.date = address_counts.date
    where mod(abs(farm_fingerprint(address)), 100000000)/100000000 <= safe_divide(10000, address_count)
),
ranked_daily_balances as (
    select
        date,
        balance,
        row_number() over (partition by date order by balance desc) as rank
    from daily_balances_sampled
)
select
    date,
    1 - 2 * sum((balance * (rank - 1) + balance / 2)) / count(*) / sum(balance) as gini
from ranked_daily_balances
group by date
having sum(balance) > 0
order by date asc""")
        results = query_job.result()  # Waits for job to complete.

        for row in results:
            try:
                KafkaConnector().send_to_kafka(self.kafka_topic, {
                    "date": row.date.strftime("%Y-%m-%d"),
                    "coin": "BTC",
                    "gini": float(row.gini)  # avoid decimal object
                })
            except Exception:
                catch_request_error({
                    "error": "Couldn't calculate Gini for Bitcoin"
                }, self.kafka_topic)
                pass

    def get_richest_eth_account(self):
        query_job = self.client.query("""with 
        double_entry_book as (
            -- debits
            select to_address as address, value as value
            from `bigquery-public-data.crypto_ethereum.traces`
            where to_address is not null
            and status = 1
            and (call_type not in ('delegatecall', 'callcode', 'staticcall') or call_type is null)
            union all
            -- credits
            select from_address as address, -value as value
            from `bigquery-public-data.crypto_ethereum.traces`
            where from_address is not null
            and status = 1
            and (call_type not in ('delegatecall', 'callcode', 'staticcall') or call_type is null)
            union all
            -- transaction fees debits
            select miner as address, sum(cast(receipt_gas_used as numeric) * cast(gas_price as numeric)) as value
            from `bigquery-public-data.crypto_ethereum.transactions` as transactions
            join `bigquery-public-data.crypto_ethereum.blocks` as blocks on blocks.number = transactions.block_number
            group by blocks.miner
            union all
            -- transaction fees credits
            select from_address as address, -(cast(receipt_gas_used as numeric) * cast(gas_price as numeric)) as value
            from `bigquery-public-data.crypto_ethereum.transactions`
        )
        select
        address, sum(value) as balance from double_entry_book
        group by address order by balance desc limit 1""")
        results = query_job.result()  # Waits for job to complete.

        for row in results:
            try:
                KafkaConnector().send_to_kafka(self.sub_kafka_topic, {
                    "timestamp": get_unix_timestamp(),
                    "coin": "ETH",
                    "accountAddress": row.address,
                    "balance": float(row.balance)
                })
            except Exception:
                catch_request_error({
                    "error": "Couldn't get richest ETH account"
                }, self.sub_kafka_topic)
                pass

    def get_richest_btc_account(self):
        session = Session()
        response = session.get("https://bitinfocharts.com/de/top-100-richest-bitcoin-addresses.html")
        m = re.match(
            r"id=\"tblOne\"(.+)>((.|\s)+?(?=tbody))((.|\s)+?(?=<a href))((.|\s)+?(?=>))>(.+)</a>((.|\s)+?(?=<td "
            r"))<td (.+)data-val=\"(.+)\">",
            response.text)
        address = m[8]
        balance = m[12]
        if address and balance:
            try:
                KafkaConnector().send_to_kafka(self.sub_kafka_topic, {
                    "timestamp": get_unix_timestamp(),
                    "coin": "BTC",
                    "accountAddress": address,
                    "balance": float(balance)
                })
            except Exception:
                catch_request_error({
                    "error": "Couldn't get richest BTC account"
                }, self.sub_kafka_topic)
                pass

    def process_data_fetch(self):
        self.calc_eth_gini()
        self.calc_btc_gini()
        self.get_richest_eth_account()
        self.get_richest_btc_account()

        s = threading.Timer(DWConfigs().get_fetch_interval(self.kafka_topic), self.process_data_fetch, [], {})
        s.start()


GoogleBigQueryDataFetcher()
