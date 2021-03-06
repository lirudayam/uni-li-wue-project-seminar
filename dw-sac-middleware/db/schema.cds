namespace uni_li_wue.dw;

using {
    User,
    Country,
    managed
} from '@sap/cds/common';

/* Enumeration Entites */
entity KPI_ENUM_COIN {
    key shortName   : String(3);
        longName    : String;
        description : String;
}

entity KPI_ENUM_STOCK_MARKET {
    key shortName : String(3);
        longName  : String;
        url       : String;
}

entity KPI_ENUM_EVENT {
    key name        : String;
        description : String;
}

entity KPI_ENUM_ETHEREUM_TOKEN {
    key symbol  : String;
        address : String;
        name    : String;
}

entity KPI_ENUM_COUNTRY_CODES {
    key isoCode     : String(2);
        latitude    : Double;
        longitude   : Double;
        name        : String;
}

/* Confiugration Entites */
entity KPI_STREAM_TYPE_CONFIG {
    key topic                       : String;
        aggregationInterval         : Integer;
        fetchInterval               : Integer;
        notificationStatisticalType : String;
        notificationLowerTreshold   : Double;
        notificationUpperTreshold   : Double;
}

entity API_CONFIG {
    key name  : String;
        value : String;
}

/* Logs */
entity LOG_HEALTH_CHECK {
    key api       : String;
        timestamp : DateTime;
}

entity LOG_FETCH_ERROR {
    key api       : String;
    key timestamp : DateTime;
        message   : String;
}


/* KPI Entites */
entity KPI_G_RICH_ACC {
    key timestamp      : DateTime;
    key coin           : String(3);
        coinInfo       : Association to one KPI_ENUM_COIN
                             on coin = coinInfo.shortName;
        accountAddress : String;
        balance        : Double;
}

entity KPI_G_N_PER_TIME {
    key timestamp  : DateTime;
    key coin       : String(3);
        coinInfo   : Association to one KPI_ENUM_COIN
                         on coin = coinInfo.shortName;
        numOfNodes : Integer;
}

entity KPI_G_PRICE_VOLA {
    key timestamp       : DateTime;
    key coin            : String(3);
        coinInfo        : Association to one KPI_ENUM_COIN
                              on coin = coinInfo.shortName;
    key stockMarket     : String(3);
        stockInfo       : Association to one KPI_ENUM_STOCK_MARKET
                              on stockMarket = stockInfo.shortName;
        price : Double;
}

entity KPI_G_PRICES {
    key timestamp : DateTime;
    key coin      : String(3);
        coinInfo  : Association to one KPI_ENUM_COIN
                        on coin = coinInfo.shortName;
        price     : Double;
        marketCap : Double;
        volume24h : Double;
        change24h : Double;
}

entity KPI_E_BLOCK {
    key timestamp        : DateTime;
        identifier       : Integer;
        size             : Integer;
        difficulty       : Double;
        gasLimit         : Double;
        gasUsed          : Double;
        noOfTransactions : Integer;
}

entity KPI_E_EXT_GASSTATION {
    key blockNumber  : Double;
        safeGasPrice : Double;
        blockTime    : Double;
}

entity KPI_B_BLOCK {
    key timestamp     : DateTime;
        blockTime     : Double;
        nextRetarget  : Double;
        difficulty    : Double;
        estimatedSent : Double;
        minersRevenue : Double;
        blockSize     : Integer;
}

entity KPI_B_SPECIAL_EVT {
    key timestamp : DateTime;
        event     : Association to KPI_ENUM_EVENT;
}

entity KPI_G_NEWS {
        timestamp      : DateTime;
    key msgId          : Integer;
    key coin           : String(3);
        coinInfo       : Association to one KPI_ENUM_COIN
                             on coin = coinInfo.shortName;
        sentiment      : Integer;
        sentimentScore : Double;
        weightedScore  : Double;
}

entity KPI_G_NODE_DISTRIBUTION {
    key timestamp : DateTime;
    key country   : String(3);
    key coin      : String(3);
        coinInfo  : Association to one KPI_ENUM_COIN
                        on coin = coinInfo.shortName;
        nodes     : Integer;
}


entity KPI_G_RECOMM {
    key timestamp : DateTime;
        token     : String;
        score     : Double;
        price     : Double;
}

entity KPI_E_TOKEN {
    key timestamp       : DateTime;
    key token           : String;
        tokenInfo       : Association to one KPI_ENUM_ETHEREUM_TOKEN
                               on token = tokenInfo.symbol;
        holdersCount    : Integer;
        issuancesCount  : Integer;
        txsCount        : Integer;
        marketCapUsd    : Double;
        availableSupply : Double;
        rate            : Double;
        volume24h       : Double;
}

entity KPI_G_GINI {
    key date             : Date;
    key coin             : String(3);
        coinInfo         : Association to one KPI_ENUM_COIN
                               on coin = coinInfo.shortName;
        gini             : Double;
}

view KPI_AGGREGATE_REQUIRED as
    select from KPI_STREAM_TYPE_CONFIG {
        key KPI_STREAM_TYPE_CONFIG.topic               as topic,
            KPI_STREAM_TYPE_CONFIG.aggregationInterval as aggregationInterval
    }
    where
        aggregationInterval != fetchInterval;
