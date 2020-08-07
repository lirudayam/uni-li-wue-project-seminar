using {uni_li_wue.dw as dw} from '../db/schema';

namespace uni_li_wue.dw.service;

service ConfigurationService {
  /* enum */
  entity KPI_ENUM_COIN               as projection on dw.KPI_ENUM_COIN;
  entity KPI_ENUM_STOCK_MARKET       as projection on dw.KPI_ENUM_STOCK_MARKET;
  entity KPI_ENUM_EVENT              as projection on dw.KPI_ENUM_EVENT;
  /* configs tables */
  entity KPI_CONFIG                  as projection on dw.KPI_STREAM_TYPE_CONFIG;
  entity API_CONFIG                  as projection on dw.API_CONFIG;

  /* logs tables */
  entity LAST_DATA_ARRIVAL @readonly as
      select from (
        select
          MAX(
            timestamp
          )             as TS,
          'RAW_B_BLOCK' as D_Topic
        from dw.KPI_B_BLOCK
      union
        select
          MAX(
            timestamp
          )             as TS,
          'RAW_E_BLOCK' as D_Topic
        from dw.KPI_E_BLOCK
      union
        select
          MAX(
            timestamp
          )             as TS,
          'RAW_E_TOKEN' as D_Topic
        from dw.KPI_E_TOKEN
      union
        select
          MAX(
            date
          )            as TS,
          'RAW_G_GINI' as D_Topic
        from dw.KPI_G_GINI
      union
        select
          MAX(
            timestamp
          )            as TS,
          'RAW_G_NEWS' as D_Topic
        from dw.KPI_G_NEWS
      union
        select
          MAX(
            timestamp
          )                         as TS,
          'RAW_G_NODE_DISTRIBUTION' as D_Topic
        from dw.KPI_G_NODE_DISTRIBUTION
      union
        select
          MAX(
            timestamp
          )                  as TS,
          'RAW_G_N_PER_TIME' as D_Topic
        from dw.KPI_G_N_PER_TIME
      union
        select
          MAX(
            timestamp
          )              as TS,
          'RAW_G_PRICES' as D_Topic
        from dw.KPI_G_PRICES
      union
        select
          MAX(
            timestamp
          )                  as TS,
          'RAW_G_PRICE_VOLA' as D_Topic
        from dw.KPI_G_PRICE_VOLA
      union
        select
          MAX(
            timestamp
          )                as TS,
          'RAW_G_RICH_ACC' as D_Topic
        from dw.KPI_G_RICH_ACC
      ) as T
      inner join dw.KPI_STREAM_TYPE_CONFIG
        on T.D_Topic = KPI_STREAM_TYPE_CONFIG.topic
      {
        key T.D_Topic     : String,
            T.TS          : Timestamp,
            case
              when
                SECONDS_BETWEEN(
                  T.TS, $now
                ) > KPI_STREAM_TYPE_CONFIG.fetchInterval
              then
                'late'
              else
                'on-time'
            end as status : String
      };

  entity HEALTH_STATUS @readonly     as
    select from dw.LOG_HEALTH_CHECK {
      api,
      timestamp as last_ping,
      (
        case
          when
            SECONDS_BETWEEN(
              timestamp, $now
            ) > (
        select from dw.API_CONFIG {
          TO_INT(
            value
          ) as val        : Integer
        }
        where
          name = 'health_ping_interval'
      )

      then
        'down'
      else
        'up'
    end
  )             as status : String
};


entity LOG_FETCH_ERROR @readonly     as projection on dw.LOG_FETCH_ERROR;
}
