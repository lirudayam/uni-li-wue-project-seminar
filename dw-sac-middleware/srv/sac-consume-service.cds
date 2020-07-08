using { uni_li_wue.dw as dw } from '../db/schema';

namespace uni_li_wue.dw.service;

service SACSlowLayerDataService {
/* readonly enum */
  entity KPI_ENUM_COINS @readonly as projection on dw.KPI_ENUM_COIN;
  entity KPI_ENUM_STOCK_MARKETS @readonly as projection on dw.KPI_ENUM_STOCK_MARKET;
  entity KPI_ENUM_EVENTS @readonly as projection on dw.KPI_ENUM_EVENT;
  entity KPI_ENUM_SEMANTICS @readonly as projection on dw.KPI_ENUM_SEMANTICS;

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
  ) as status: String from dw.LOG_HEALTH_CHECK;
  
/* configs tables */
  entity KPI_CONFIG @readonly as projection on dw.KPI_STREAM_TYPE_CONFIG;
  
/* kpi readonly */
  entity KPI_G_RICH_ACC @readonly as projection on dw.KPI_G_RICH_ACC;
  entity KPI_G_T_PER_TIME @readonly as projection on dw.KPI_G_T_PER_TIME;
  entity KPI_E_SMART_EXEC @readonly as projection on dw.KPI_E_SMART_EXEC;
  entity KPI_G_N_PER_TIME @readonly as projection on dw.KPI_G_N_PER_TIME;
  entity KPI_G_TRANSACT_INF @readonly as projection on dw.KPI_G_TRANSACT_INF;
  entity KPI_G_PRICE_VOLA @readonly as projection on dw.KPI_G_PRICE_VOLA;
  entity KPI_G_PRICES @readonly as projection on dw.KPI_G_PRICES;
  entity KPI_E_GASSTATION @readonly as projection on dw.KPI_E_GASSTATION;
  entity KPI_B_SPECIAL_EVT @readonly as projection on dw.KPI_B_SPECIAL_EVT;
  
  entity KPI_G_NEWS @readonly as projection on dw.KPI_G_NEWS;
  entity KPI_G_RECOMM @readonly as projection on dw.KPI_G_RECOMM;
  entity KPI_G_CREDITS @readonly as projection on dw.KPI_G_CREDITS;
}