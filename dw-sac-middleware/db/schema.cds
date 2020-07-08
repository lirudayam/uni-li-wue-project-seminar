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
	timestamp	: Timestamp;
}

entity LOG_FETCH_ERROR {
	key api		: String;
	message	    : String;
	timestamp	: Timestamp;
}


/* KPI Entites */
entity KPI_G_RICH_ACC {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	accountAddress	: String;
	balance			: Double;
}

entity KPI_G_T_PER_TIME {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	senderAddress	: String;
	recieverAddress	: String;
	units			: Decimal;
	transactionHash	: String(64);
}

entity KPI_E_SMART_EXEC {
	key timestamp	: Timestamp;
	contractAddress	: String;
	count			: Integer;
}

entity KPI_G_N_PER_TIME {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	numOfNodes		: Integer;
}

entity KPI_G_TRANSACT_INF {
	key timestamp			: Timestamp;
	key coin				: Association to KPI_ENUM_COIN;
	totalTransactionFees	: Double;
	numOfTransactions		: Integer;
	totalTransactionVolume	: Double;
}

entity KPI_G_PRICE_VOLA {
	key timestamp			: Timestamp;
	key coin				: Association to KPI_ENUM_COIN;
	priceVolatility			: Double;
}

entity KPI_G_PRICES {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	price			: Double;
	marketCap		: Double;
	volume24h		: Double;
	change24h 		: Double;
}

entity KPI_B_SPECIAL_EVT {
	key timestamp	: Timestamp;
	event			: Association to KPI_ENUM_EVENT;
}

entity KPI_G_NEWS {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	url				: String;
	sentiment		: Association to KPI_ENUM_SEMANTICS;
}

entity KPI_G_RECOMM {
	key timestamp	: Timestamp;
	token			: String;
	score			: Decimal;
	price			: Decimal;
}

entity KPI_G_CREDITS {
	key timestamp	: Timestamp;
	key coin		: Association to KPI_ENUM_COIN;
	noOfCredits		: Integer;
	noOfTransactions: Integer;
}
