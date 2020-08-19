using { uni_li_wue.dw as dw } from '../db/schema';

namespace uni_li_wue.dw.service;

service KafkaPublishService {
/* readonly enum */
  entity KPI_ENUM_COIN @readonly as projection on dw.KPI_ENUM_COIN;
  entity KPI_ENUM_STOCK_MARKET @readonly as projection on dw.KPI_ENUM_STOCK_MARKET;
  entity KPI_ENUM_EVENT @readonly as projection on dw.KPI_ENUM_EVENT;
  entity KPI_ENUM_ETHEREUM_TOKEN as projection on dw.KPI_ENUM_ETHEREUM_TOKEN;
  
/* configs tables */
  entity KPI_CONFIG @readonly as projection on dw.KPI_STREAM_TYPE_CONFIG;
  entity API_CONFIG @readonly as projection on dw.API_CONFIG;

/* logs tables */
  entity LOG_HEALTH_CHECK as projection on dw.LOG_HEALTH_CHECK;
  entity LOG_FETCH_ERROR @insertonly as projection on dw.LOG_FETCH_ERROR;
  
/* kpi insertonly */
  entity KPI_G_RICH_ACC @insertonly as projection on dw.KPI_G_RICH_ACC;
  entity KPI_G_N_PER_TIME @insertonly as projection on dw.KPI_G_N_PER_TIME;
  entity KPI_G_PRICE_VOLA @insertonly as projection on dw.KPI_G_PRICE_VOLA;
  entity KPI_G_PRICES @insertonly as projection on dw.KPI_G_PRICES;
  entity KPI_E_BLOCK as projection on dw.KPI_E_BLOCK;
  entity KPI_E_EXT_GASSTATION as projection on dw.KPI_E_EXT_GASSTATION;
  entity KPI_B_BLOCK as projection on dw.KPI_B_BLOCK;
  entity KPI_B_SPECIAL_EVT @insertonly as projection on dw.KPI_B_SPECIAL_EVT;
  entity KPI_G_NODE_DISTRIBUTION @insertonly as projection on dw.KPI_G_NODE_DISTRIBUTION;
  entity KPI_G_GINI @insertonly as projection on dw.KPI_G_GINI;
  entity KPI_E_TOKEN @insertonly as projection on dw.KPI_E_TOKEN;

  action KPI_E_TOKEN_BI(array : array of KPI_E_TOKEN);
  action KPI_G_NODE_DISTRIBUTION_BI(array : array of KPI_G_NODE_DISTRIBUTION);
  action KPI_G_N_PER_TIME_BI(array : array of KPI_G_N_PER_TIME);
  action KPI_E_GASSTATION_BI(array : array of KPI_E_EXT_GASSTATION);
  
  entity KPI_G_NEWS @insertonly as projection on dw.KPI_G_NEWS;
  entity KPI_G_RECOMM @insertonly as projection on dw.KPI_G_RECOMM;
}