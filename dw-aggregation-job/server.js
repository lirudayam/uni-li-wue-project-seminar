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
    const selectSQL = `SELECT * FROM ${schema}.UNI_LI_WUE_DW_KPI_STREAM_TYPE_CONFIG`;
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

        const oAggregationsFormula = {
            KPI_G_PRICE_VOLA: {
                select: "MIN(Timestamp) as Timestamp, Coin, StockMarket, AVG(Price) as Price",
                fields: ["Timestamp", "Coin", "StockMarket", "Price"],
                groupBy: ", Coin, StockMarket"
            },
            KPI_G_PRICES: {
                select: "MIN(Timestamp) as Timestamp, Coin, AVG(Price) as Price, AVG(MarketCap) as MarketCap, AVG(volume24h) as volume24h, AVG(change24h) as change24h",
                fields: ["Timestamp", "Coin", "Price", "MarketCap", "Volume24h", "Change24h"],
                groupBy: ", Coin"
            },
            KPI_E_BLOCK: {
                select: "MIN(Timestamp) as Timestamp, MIN(identifier) as identifier, AVG(Size) as Size, AVG(difficulty) as difficulty, AVG(gasLimit) as gasLimit, AVG(gasUsed) as gasUsed, CEIL(AVG(noOfTransactions)) as noOfTransactions",
                fields: ["Timestamp", "identifier", "size", "difficulty", "gasLimit", "gasUsed", "noOfTransactions"],
                groupBy: ""
            },
            KPI_B_BLOCK: {
                select: "MIN(Timestamp) as Timestamp, AVG(blockTime) as blockTime, AVG(nextRetarget) as nextRetarget, AVG(difficulty) as difficulty, AVG(estimatedSent) as estimatedSent, AVG(minersRevenue) as minersRevenue",
                fields: ["Timestamp", "blockTime", "nextRetarget", "difficulty", "estimatedSent", "minersRevenue"],
                groupBy: ""
            },
            KPI_G_NODE_DISTRIBUTION: {
                select: "MIN(Timestamp) as Timestamp, Country, Coin, CEIL(AVG(nodes)) as nodes",
                fields: ["Timestamp", "Country", "Coin", "nodes"],
                groupBy: ", Coin, Country"
            }
        }


        if (aRelevantEntites.length === 0) {
            return true;
        } else {
            aRelevantEntites.forEach(element => {
                var sEntityName = "KPI" + element.TOPIC.substr(3).toUpperCase();
                var sTableName = "UNI_LI_WUE_DW_" + sEntityName;

                if (oAggregationsFormula.hasOwnProperty(sEntityName)) {
                    console.log(sTableName);
                    var aFieldNames = oAggregationsFormula[sEntityName].fields.map(item => item.toUpperCase());
                    var aQuestionMarks = oAggregationsFormula[sEntityName].fields.map(item => "?");

                    sAggregationQuery = `SELECT ${oAggregationsFormula[sEntityName].select} FROM ${schema}.${sTableName} WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ? GROUP BY CEIL(SECONDS_BETWEEN(Timestamp, NOW()) * 1.0 / ?)${oAggregationsFormula[sEntityName].groupBy}`;
                    sDeletionQuery = `DELETE FROM ${schema}.${sTableName} WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ?`;
                    sInsertQuery = `INSERT INTO ${schema}.${sTableName}(${aFieldNames.join(", ")}) VALUES(${aQuestionMarks.join(", ")})`;

                    selectStmt = conn.prepare(sAggregationQuery);
                    const aEntities = selectStmt.exec([iAggregationDelay, element.AGGREGATIONINTERVAL]).map(entry => {
                        return aFieldNames.map(field => entry[field.toUpperCase()])
                    });

                    if (aEntities.length > 0) {
                        selectStmt = conn.prepare(sDeletionQuery);
                        console.log(selectStmt.exec([iAggregationDelay]), "dropped");

                        insertStmt = conn.prepare(sInsertQuery);
                        console.log(insertStmt.execBatch(aEntities), "inserted");
                    }
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