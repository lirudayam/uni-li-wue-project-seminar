"use strict";

const express = require('express');
const app = express();
const xsenv = require("@sap/xsenv");

const db = require("./db");

app.get('/runjob', function (req, res) {
    res.send(findAndAggregateData());
});

const port = process.env.PORT || 3000;
app.listen(port, function () {
    try {
        let hanaOptions = xsenv.filterCFServices({
            plan: "hdi-shared"
        })[0].credentials;
        hanaOptions = {
            "hana": hanaOptions
        };
        hanaOptions.hana.pooling = true;
        db.initializeDBConnection(hanaOptions);
    } catch (error) {
        console.error(error);
    }
    console.log(`jobserver started on port ${port}`);
});

async function findAndAggregateData() {
    const schema = db.getSchema();
    const selectSQL = `SELECT * FROM ${schema}.UNI_LI_WUE_DW_KPI_AGGREGATE_REQUIRED`;
    const selectAggregationSQL = `SELECT * FROM ${schema}.UNI_LI_WUE_DW_API_CONFIG WHERE Name = 'aggregation_delay'`;

    let selectStmt, updateStmt, insertStmt;
    let sAggregationQuery, sDeletionQuery, sInsertQuery;

    try {
        const conn = db.getDBConnection();
        if (!conn) {
            throw new Error('Failed to retreive connection.');
        }
        console.log("connection acquired");

        selectStmt = conn.prepare(selectSQL);
        const aRelevantEntites = selectStmt.exec([]);

        selectStmt = conn.prepare(selectAggregationSQL);
        const iAggregationDelay = selectStmt.exec([])[0].VALUE;

        if (aRelevantEntites.length === 0) {
            return true;
        } else {
            aRelevantEntites.forEach(element => {
                console.log("do it for", element.TOPIC);
                console.log(iAggregationDelay, element.AGGREGATIONINTERVAL);
                switch (element.TOPIC) {
                    case 'RAW_G_PRICES':
                        sAggregationQuery = `SELECT Coin, MIN(Timestamp) as N_Timestamp, AVG(Price) as N_Price, AVG(MarketCap) as N_MarketCap, AVG(Volume24h) as N_Volume, AVG(Change24h) as N_Change FROM ${schema}.UNI_LI_WUE_DW_KPI_G_PRICES WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ? GROUP BY CEIL(SECONDS_BETWEEN(Timestamp, NOW()) * 1.0 / ?), Coin`;
                        sDeletionQuery = `DELETE FROM ${schema}.UNI_LI_WUE_DW_KPI_G_PRICES WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ?`;
                        sInsertQuery = `INSERT INTO ${schema}.UNI_LI_WUE_DW_KPI_G_PRICES(TIMESTAMP, PRICE, MARKETCAP, VOLUME24H, CHANGE24H, COIN) VALUES(?, ?, ?, ?, ?, ?)`;

                        selectStmt = conn.prepare(sAggregationQuery);
                        const aPriceEntities = selectStmt.exec([iAggregationDelay, element.AGGREGATIONINTERVAL]).map(entry => {
                            return [entry.N_TIMESTAMP, entry.N_PRICE, entry.N_MARKETCAP, entry.N_VOLUME, entry.N_CHANGE, entry.COIN];
                        });

                        if (aPriceEntities.length > 0) {
                            selectStmt = conn.prepare(sDeletionQuery);
                            console.log(selectStmt.exec([iAggregationDelay]), "dropped");
    
                            insertStmt = conn.prepare(sInsertQuery);
                            console.log(insertStmt.execBatch(aPriceEntities), "inserted");
                        }

                    break;

                    case 'RAW_E_GASSTATION':
                        sAggregationQuery = `SELECT MIN(Timestamp) as N_Timestamp, AVG(SafeGasPrice) as N_SafeGasPrice, MIN(BlockNumber) as N_BlockNumber, AVG(BlockTime) as N_BlockTime FROM ${schema}.UNI_LI_WUE_DW_KPI_E_GASSTATION WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ? GROUP BY CEIL(SECONDS_BETWEEN(Timestamp, NOW()) * 1.0 / ?)`;
                        sDeletionQuery = `DELETE FROM ${schema}.UNI_LI_WUE_DW_KPI_E_GASSTATION WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ?`;
                        sInsertQuery = `INSERT INTO ${schema}.UNI_LI_WUE_DW_KPI_E_GASSTATION(TIMESTAMP, SafeGasPrice, BlockNumber, BlockTime) VALUES(?, ?, ?, ?)`;

                        selectStmt = conn.prepare(sAggregationQuery);
                        const aGasEntities = selectStmt.exec([iAggregationDelay, element.AGGREGATIONINTERVAL]).map(entry => {
                            return [entry.N_TIMESTAMP, entry.N_SAFEGASPRICE, entry.N_BLOCKNUMBER, entry.N_BLOCKTIME];
                        });
                        
                        if (aGasEntities.length > 0) {
                            selectStmt = conn.prepare(sDeletionQuery);
                            console.log(selectStmt.exec([iAggregationDelay]), "dropped");
    
                            insertStmt = conn.prepare(sInsertQuery);
                            console.log(insertStmt.execBatch(aGasEntities), "inserted");
                        }

                    break;

                    case 'RAW_G_LATEST_BLOCK':
                        /*let sAggregationQuery = "SELECT Coin, MIN(Timestamp) as N_Timestamp, AVG(Price) as N_Price, AVG(MarketCap) as N_MarketCap, AVG(Volume24h) as N_Volume, AVG(Change24h) as N_Change FROM UNI_LI_WUE_DW_KPI_G_PRICES WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ? GROUP BY CEIL(SECONDS_BETWEEN(Timestamp, NOW()) * 1.0 / ?), Coin";
                        let sDeletionQuery = "DELETE FROM UNI_LI_WUE_DW_KPI_G_PRICES WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ?";
                        let sInsertQuery = "INSERT INTO UNI_LI_WUE_DW_KPI_G_PRICES(TIMESTAMP, PRICE, MARKETCAP, VOLUME24H, CHANGE24H, COIN) VALUES(?, ?, ?, ?, ?, ?)";

                        selectStmt = conn.prepare(sAggregationQuery);
                        const aEntities = selectStmt.exec([iAggregationDelay, element.AGGREGATIONINTERVAL]).map(entry => {
                            return [entry.N_Timestamp, entry.N_Price, entry.N_MarketCap, entry.N_Volume, entry.N_Change, entry.Coin];
                        });

                        selectStmt = conn.prepare(sDeletionQuery);
                        selectStmt.exec([]);

                        insertStmt = conn.prepare(sInsertQuery);
                        insertStmt.execBatch(aEntities);*/
                    break;
                }

            });
            return true;
        }
    } catch (e) {
        console.error(e);
        if (selectStmt) {
            selectStmt.drop(function (err) {
                if (err) console.error(err);
            });
        }
        if (updateStmt) {
            updateStmt.drop(function (err) {
                if (err) console.error(err);
            });
        }
        if (insertStmt) {
            insertStmt.drop(function (err) {
                if (err) console.error(err);
            });
        }
        return e;
    }
}