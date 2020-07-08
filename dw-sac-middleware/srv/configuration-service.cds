using { uni_li_wue.dw as dw } from '../db/schema';

namespace uni_li_wue.dw.service;

service ConfigurationService {
/* enum */
  entity KPI_ENUM_COIN as projection on dw.KPI_ENUM_COIN;
  entity KPI_ENUM_STOCK_MARKET as projection on dw.KPI_ENUM_STOCK_MARKET;
  entity KPI_ENUM_EVENT as projection on dw.KPI_ENUM_EVENT;
  entity KPI_ENUM_SEMANTICS as projection on dw.KPI_ENUM_SEMANTICS;

/* configs tables */
  entity KPI_CONFIG as projection on dw.KPI_STREAM_TYPE_CONFIG;
  entity API_CONFIG as projection on dw.API_CONFIG;
  
/* logs tables */
  entity HEALTH_STATUS @readonly as select api, timestamp as last_ping, (
      case
          when
            SECONDS_BETWEEN(timestamp, $now) > (SELECT TO_INT(value) as delta FROM dw.API_CONFIG WHERE name = 'health_ping_interval')
          then
            'down'
          else
            'up'
        end
  ) as status : String from dw.LOG_HEALTH_CHECK;
  entity LOG_FETCH_ERROR @readonly as projection on dw.LOG_FETCH_ERROR;

}