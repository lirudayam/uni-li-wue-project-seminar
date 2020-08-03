'use strict';

import express from 'express';
import { filterCFServices } from '@sap/xsenv';
import { initializeDBConnection, getSchema, getDBConnection } from './db';

const app = express();

app.get('/runjob', function (req, res) {
	res.send(findAndAggregateData());
});

const port = process.env.PORT || 3000;
app.listen(port, function () {
	try {
		let hanaOptions = filterCFServices({
			plan: 'hdi-shared'
		})[0].credentials;
		hanaOptions = {
			hana: hanaOptions
		};
		hanaOptions.hana.pooling = true;
		initializeDBConnection(hanaOptions);
	} catch (error) {
		console.error(error);
	}
	console.log(`jobserver started on port ${port}`);
});

async function findAndAggregateData() {
	const schema = getSchema();

	// get kpi-specific configs and the general aggregation delay
	const selectSQL = `SELECT * FROM ${schema}.UNI_LI_WUE_DW_KPI_STREAM_TYPE_CONFIG`;
	const selectAggregationSQL = `SELECT * FROM ${schema}.UNI_LI_WUE_DW_API_CONFIG WHERE Name = 'aggregation_delay'`;

	let selectStmt, updateStmt, insertStmt;
	let sAggregationQuery, sDeletionQuery, sInsertQuery;

	try {
		const conn = getDBConnection();
		if (!conn) {
			throw new Error('Failed to retreive connection.');
		}
		console.log('connection acquired');

		selectStmt = conn.prepare(selectSQL);
		const aRelevantEntites = selectStmt.exec([]);

		selectStmt = conn.prepare(selectAggregationSQL);
		const iAggregationDelay = selectStmt.exec([])[0].VALUE;

		// map each kpi to select statment to be used to filter and reinsert
		const oAggregationsFormula = {
			KPI_G_PRICE_VOLA: {
				select:
					'MIN(Timestamp) as Timestamp, Coin, StockMarket, AVG(Price) as Price',
				fields: ['Timestamp', 'Coin', 'StockMarket', 'Price'],
				groupBy: ', Coin, StockMarket'
			},
			KPI_G_PRICES: {
				select:
					'MIN(Timestamp) as Timestamp, Coin, AVG(Price) as Price, MAX(MarketCap) as MarketCap, AVG(volume24h) as volume24h, AVG(change24h) as change24h',
				fields: [
					'Timestamp',
					'Coin',
					'Price',
					'MarketCap',
					'Volume24h',
					'Change24h'
				],
				groupBy: ', Coin'
			},
			KPI_E_BLOCK: {
				select:
					'MIN(Timestamp) as Timestamp, MIN(identifier) as identifier, AVG(Size) as Size, AVG(difficulty) as difficulty, AVG(gasLimit) as gasLimit, AVG(gasUsed) as gasUsed, CEIL(AVG(noOfTransactions)) as noOfTransactions',
				fields: [
					'Timestamp',
					'identifier',
					'size',
					'difficulty',
					'gasLimit',
					'gasUsed',
					'noOfTransactions'
				],
				groupBy: ''
			},
			KPI_B_BLOCK: {
				select:
					'MIN(Timestamp) as Timestamp, AVG(blockTime) as blockTime, AVG(nextRetarget) as nextRetarget, AVG(difficulty) as difficulty, AVG(estimatedSent) as estimatedSent, AVG(minersRevenue) as minersRevenue',
				fields: [
					'Timestamp',
					'blockTime',
					'nextRetarget',
					'difficulty',
					'estimatedSent',
					'minersRevenue'
				],
				groupBy: ''
			},
			KPI_G_NODE_DISTRIBUTION: {
				select:
					'MIN(Timestamp) as Timestamp, Country, Coin, CEIL(AVG(nodes)) as nodes',
				fields: ['Timestamp', 'Country', 'Coin', 'nodes'],
				groupBy: ', Coin, Country'
			}
		};

		if (aRelevantEntites.length === 0) {
			return true;
		} else {
			aRelevantEntites.forEach((element) => {
				var sEntityName = 'KPI' + element.TOPIC.substr(3).toUpperCase();
				var sTableName = 'UNI_LI_WUE_DW_' + sEntityName;

				// check if in mapping
				if (oAggregationsFormula.hasOwnProperty(sEntityName)) {
					var aFieldNames = oAggregationsFormula[
						sEntityName
					].fields.map((item) => item.toUpperCase());
					var aQuestionMarks = oAggregationsFormula[sEntityName].fields.map(
						(item) => '?'
					);

					sAggregationQuery = `SELECT ${oAggregationsFormula[sEntityName].select} FROM ${schema}.${sTableName} WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ? GROUP BY CEIL(SECONDS_BETWEEN(Timestamp, NOW()) * 1.0 / ?)${oAggregationsFormula[sEntityName].groupBy}`;
					sDeletionQuery = `DELETE FROM ${schema}.${sTableName} WHERE SECONDS_BETWEEN(Timestamp, NOW()) > ?`;
					sInsertQuery = `INSERT INTO ${schema}.${sTableName}(${aFieldNames.join(
						', '
					)}) VALUES(${aQuestionMarks.join(', ')})`;

					// get all relevant entries
					selectStmt = conn.prepare(sAggregationQuery);
					const aEntities = selectStmt
						.exec([iAggregationDelay, element.AGGREGATIONINTERVAL])
						.map((entry) => {
							return aFieldNames.map((field) => entry[field.toUpperCase()]);
						});

					if (aEntities.length > 0) {
						// delete them
						selectStmt = conn.prepare(sDeletionQuery);
						console.log(selectStmt.exec([iAggregationDelay]), 'dropped');

						// insert new aggregated ones
						insertStmt = conn.prepare(sInsertQuery);
						console.log(insertStmt.execBatch(aEntities), 'inserted');
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

// setup like a cronjob every day to trigger a cleanup
setInterval(() => {
	findAndAggregateData();
}, 24 * 60 * 60 * 1000);
