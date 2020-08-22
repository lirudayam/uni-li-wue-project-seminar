using {uni_li_wue.dw as dw} from '../db/schema';

namespace uni_li_wue.dw.service;

service SACSlowLayerDataService {
  /* readonly enum */
  entity KPI_ENUM_COINS @readonly          as projection on dw.KPI_ENUM_COIN;
  entity KPI_ENUM_STOCK_MARKETS @readonly  as projection on dw.KPI_ENUM_STOCK_MARKET;
  entity KPI_ENUM_EVENTS @readonly         as projection on dw.KPI_ENUM_EVENT;
  entity KPI_ENUM_ETHEREUM_TOKEN @readonly as projection on dw.KPI_ENUM_ETHEREUM_TOKEN;

  /* logs tables */
  entity HEALTH_STATUS @readonly           as
    select
      api,
      timestamp as last_ping,
      (
        case
          when
            SECONDS_BETWEEN(
              timestamp, $now
            ) > (
        select TO_INT(
          value
        ) as delta from dw.API_CONFIG
        where
          name = 'health_ping_interval'
      )
      then
        'down'
      else
        'up'
    end
  )             as status : String
from dw.LOG_HEALTH_CHECK;

/* configs tables */
entity KPI_CONFIG @readonly                as projection on dw.KPI_STREAM_TYPE_CONFIG;
/* kpi readonly */
entity KPI_G_RICH_ACC @readonly            as projection on dw.KPI_G_RICH_ACC;
entity KPI_G_N_PER_TIME @readonly          as projection on dw.KPI_G_N_PER_TIME;
entity KPI_G_PRICE_VOLA @readonly          as projection on dw.KPI_G_PRICE_VOLA;

entity KPI_G_PRICE_DIFF @readonly          as
  select
    key timestamp,
    key coin,
        MIN(
          price
        ) as Minimum : Double,
        MAX(
          price
        ) as Maximum : Double,
        AVG(
          price
        ) as Average : Double
  from dw.KPI_G_PRICE_VOLA
  group by
    timestamp,
    coin;

entity KPI_G_PRICES @readonly              as projection on dw.KPI_G_PRICES;

entity KPI_E_BLOCK @readonly               as
  select
    key identifier,
        timestamp,
        size,
        difficulty,
        gasLimit,
        gasUsed,
        safeGasPrice,
        blockTime,
        noOfTransactions
  from dw.KPI_E_BLOCK
  inner join dw.KPI_E_EXT_GASSTATION
    on identifier = blockNumber;

entity KPI_B_BLOCK @readonly               as projection on dw.KPI_B_BLOCK;
entity KPI_B_SPECIAL_EVT @readonly         as projection on dw.KPI_B_SPECIAL_EVT;

entity KPI_G_NODE_DISTRIBUTION @readonly   as
  select
    key timestamp,
    key coin,
        latitude,
        longitude,
        nodes
  from dw.KPI_G_NODE_DISTRIBUTION
  inner join dw.KPI_ENUM_COUNTRY_CODES
    on country = isoCode;

entity KPI_G_GINI @readonly                as projection on dw.KPI_G_GINI;
entity KPI_E_TOKEN @readonly               as projection on dw.KPI_E_TOKEN;

/* latest data kpi */
entity KPI_G_RICH_ACC_LATEST @readonly     as
  select * from dw.KPI_G_RICH_ACC as M
  where
    M.timestamp = (
      select MAX(
        timestamp
      ) as Max from dw.KPI_G_RICH_ACC);

entity KPI_G_PRICE_DIFF_LATEST @readonly   as
  select 
    key timestamp,
    key coin,
        MIN(
          price
        ) as Minimum : Double,
        MAX(
          price
        ) as Maximum : Double,
        AVG(
          price
        ) as Average : Double from dw.KPI_G_PRICE_VOLA as M
  where
    M.timestamp = (
      select MAX(
        timestamp
      ) as Max from dw.KPI_G_PRICE_VOLA as H
    );

entity KPI_G_PRICES_LATEST @readonly       as
  select * from dw.KPI_G_PRICES as M
  where
    M.timestamp = (
      select MAX(
        timestamp
      ) as Max from dw.KPI_G_PRICES as H
    );

entity KPI_G_N_PER_TIME_LATEST @readonly   as
  select * from dw.KPI_G_N_PER_TIME as M
  where
    M.timestamp = (
      select MAX(
        timestamp
      ) as Max from dw.KPI_G_N_PER_TIME as H
    );

entity KPI_G_NEWS @readonly                as projection on dw.KPI_G_NEWS;
entity KPI_G_RECOMM @readonly              as projection on dw.KPI_G_RECOMM;
}
