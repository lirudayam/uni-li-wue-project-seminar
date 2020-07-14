namespace uni_li_wue.dw;
using { User, Country, managed } from '@sap/cds/common';

/* Enumeration Entites */
entity KPI_ENUM_COIN {
	key shortName	: String(3);
	longName		: String;
	description		: String;
}

entity KPI_ENUM_STOCK_MARKET {
	key shortName	: String(3);
	longName		: String;
	url				: String;
}

entity KPI_ENUM_EVENT {
	key name		: String;
	description		: String;
}

entity KPI_ENUM_SEMANTICS {
	key scoreName	: String;
	pointScore		: Integer;
	description		: String;
}

/* Confiugration Entites */
entity KPI_STREAM_TYPE_CONFIG {
	key topic		            : String;
	aggregationInterval	        : Integer;
    fetchInterval	            : Integer;
    notificationStatisticalType	: String;
	notificationLowerTreshold	: Double;
	notificationUpperTreshold	: Double;                 
}

entity API_CONFIG {
	key name	: String;
	value	    : String;
}

/* Logs */
entity LOG_HEALTH_CHECK {
	key api		: String;
	timestamp	: DateTime;
}

entity LOG_FETCH_ERROR {
	key api		: String;
	message	    : String;
	timestamp	: DateTime;
}


/* KPI Entites */
entity KPI_G_RICH_ACC {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	accountAddress	: String;
	balance			: Double;
}

entity KPI_G_T_PER_TIME {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	senderAddress	: String;
	recieverAddress	: String;
	units			: Decimal;
	transactionHash	: String(64);
}

entity KPI_E_SMART_EXEC {
	key timestamp	: DateTime;
	contractAddress	: String;
	count			: Integer;
}

entity KPI_G_N_PER_TIME {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	numOfNodes		: Integer;
}

entity KPI_G_TRANSACT_INF {
	key timestamp			: DateTime;
	key coin				: String(3);
	coinInfo				: Association to one KPI_ENUM_COIN 
								on coin = coinInfo.shortName;
	totalTransactionFees	: Double;
	numOfTransactions		: Integer;
	totalTransactionVolume	: Double;
}

entity KPI_G_PRICE_VOLA {
	key timestamp		: DateTime;
	key coin			: String(3);
	coinInfo			: Association to one KPI_ENUM_COIN 
							on coin = coinInfo.shortName;
	priceVolatility		: Double;
}

entity KPI_G_PRICES {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	price			: Double;
	marketCap		: Double;
	volume24h		: Double;
	change24h 		: Double;
}

entity KPI_G_LATEST_BLOCK {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	identifier		: Integer;
    size			: Integer;
    difficulty		: Double;
    gasLimit		: Double;
    gasUsed			: Double;
    noOfTransactions: Integer;
}

entity KPI_E_GASSTATION {
	key timestamp	: DateTime;
	safeGasPrice	: Double;
	blockNumber		: Double;
	blockTime 		: Double;
}

entity KPI_B_SPECIAL_EVT {
	key timestamp	: DateTime;
	event			: Association to KPI_ENUM_EVENT;
}

entity KPI_G_NEWS {
	timestamp		: DateTime;
	key msgId		: Integer;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	sentiment		: Integer;
	sentimentScore 	: Double;
    weightedScore	: Double;
}

entity KPI_G_RECOMM {
	key timestamp	: DateTime;
	token			: String;
	score			: Decimal;
	price			: Decimal;
}

entity KPI_G_CREDITS {
	key timestamp	: DateTime;
	key coin		: String(3);
	coinInfo		: Association to one KPI_ENUM_COIN 
						on coin = coinInfo.shortName;
	noOfCredits		: Integer;
	noOfTransactions: Integer;
}

view KPI_AGGREGATE_REQUIRED as
  select from KPI_STREAM_TYPE_CONFIG
  {
    key KPI_STREAM_TYPE_CONFIG.topic as topic,
	KPI_STREAM_TYPE_CONFIG.aggregationInterval as aggregationInterval
  }
  where aggregationInterval != fetchInterval;