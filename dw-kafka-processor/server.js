const { Kafka, logLevel } = require('kafkajs');

// XS-Advanced environment variables
const xsenv = require('@sap/xsenv');
const oauthClient = require('client-oauth2');

// Moment.js
const moment = require('moment');

// Logging information
const log = require('cf-nodejs-logging-support');
log.setLoggingLevel('info');

// get the connectivity service for Kafka connection
const connService = xsenv.getServices({
	connectivity: function (service) {
		return service.label === 'connectivity';
	}
}).connectivity;

// enhance String with new func to get bytes for STOMP5 protocol
String.prototype.getBytes = function () {
	var bytes = [];
	for (var i = 0; i < this.length; ++i) {
		bytes.push(this.charCodeAt(i));
	}
	return bytes;
};

// get CDS module
const cds = require('@sap/cds');

// async function for consuming kafka and writing to data warehouse
const asyncInitialRunFn = async () => {
	// connect to the external service of dw -> access via OData, no direct access
	const srv = await cds.connect.to('dwInsertService');
	// get entities for namespace
	const entites = srv.entities('uni_li_wue.dw');

	// filter for any relevant ones in the required KafkaPublishService
	let relevantServiceEntities = {};
	Object.keys(entites).map((key) => {
		if (key.startsWith('service.KafkaPublishService.')) {
			relevantServiceEntities[
				key.replace('service.KafkaPublishService.', '')
			] = entites[key];
		}
	});

	const {
		KPI_ENUM_ETHEREUM_TOKEN,
		KPI_G_RICH_ACC,
		KPI_G_N_PER_TIME,
		KPI_G_PRICE_VOLA,
		KPI_G_PRICES,
		KPI_B_SPECIAL_EVT,
		KPI_G_NEWS,
		KPI_G_RECOMM,
		KPI_G_CREDITS,
		LOG_FETCH_ERROR,
		LOG_HEALTH_CHECK,
		KPI_E_EXT_GASSTATION,
		KPI_E_BLOCK,
		KPI_B_BLOCK,
		KPI_G_GINI
	} = relevantServiceEntities;

	// group by speed layer and batch layer topic
	var oSpeedLayerTopics = {
		RAW_G_RICH_ACC: KPI_G_RICH_ACC,
		RAW_G_N_PER_TIME: KPI_G_N_PER_TIME,

		RAW_G_PRICE_VOLA: KPI_G_PRICE_VOLA,
		RAW_G_PRICES: KPI_G_PRICES,
		RAW_B_SPECIAL_EVT: KPI_B_SPECIAL_EVT,

		RAW_G_STOCKTWITS_FETCHER: KPI_G_NEWS,
		RAW_G_RECOMM: KPI_G_RECOMM,
		RAW_G_CREDITS: KPI_G_CREDITS,

		RAW_G_GINI: KPI_G_GINI
	};
	var aBatchLayerTopics = [
		'RAW_E_GASSTATION',
		'RAW_G_NODE_DISTRIBUTION',
		'RAW_E_BLOCK',
		'RAW_B_BLOCK',
		'RAW_E_TOKEN'
	];

	const socketAliveTime = 60 * 60 * 1000;

	var socks = require('@luminati-io/socksv5');

	const _getTokenForDestinationService = function () {
		return new Promise((resolve, reject) => {
			let tokenEndpoint = connService.token_service_url + '/oauth/token';
			const client = new oauthClient({
				authorizationUri:
					connService.token_service_url + '/oauth/authorize',
				accessTokenUri: tokenEndpoint,
				clientId: connService.clientid,
				clientSecret: connService.clientsecret,
				scopes: [],
				grant_type: 'client_credentials'
			});
			client.credentials
				.getToken()
				.catch((error) => {
					return reject({
						message:
							'Error: failed to get access token for Connectivity service',
						error: error
					});
				})
				.then((result) => {
					resolve(result.data.access_token);
				});
		});
	};

	const triggerListener = () => {
		_getTokenForDestinationService()
			.then((jwtToken) => {
				var STATE_VERSION = 0,
					STATE_RESPONSE = 1,
					STATE_2VERSION = 2,
					STATE_STATUS = 3;

				// Establish a SOCKS5 handshake for TCP connection via connectivity service and Cloud Connector
				socks.connect(
					{
						host: 'kafka.cloud',
						port: 9092,
						proxyHost: connService.onpremise_proxy_host,
						proxyPort: parseInt(
							connService.onpremise_socks5_proxy_port,
							10
						),
						localDNS: false,
						strictLocalDNS: true,
						auths: [
							{
								METHOD: 0x80,
								client: function clientHandler(stream, cb) {
									console.log('BEGIN AUTH');
									var state = STATE_2VERSION;

									function onData(chunk) {
										var i = 0,
											len = chunk.length;

										while (i < len) {
											console.log(chunk[i]);
											switch (state) {
												case STATE_2VERSION:
													if (chunk[i] !== 0x01) {
														stream.removeListener(
															'data',
															onData
														);
														cb(
															new Error(
																'Unsupported auth request version: ' +
																	chunk[i]
															)
														);
														return;
													}
													++i;
													state = STATE_STATUS;
													break;
												case STATE_STATUS:
													++i;
													state = STATE_VERSION;
													console.log(chunk);
													stream.removeListener(
														'data',
														onData
													);
													cb(true);
													return;
											}
										}
									}
									stream.on('data', onData);

									// === Authenticate ==
									// Send the following bytes
									// 1 byte - authentication method version: 1
									// 4 bytes - length of JWT token acquired from XSUAA OAuth
									// X bytes - The content of JWT token acquired from XSUAA OAuth
									// 1 byte - Length of Cloud Connector location ID: Currently 0 because we don't CC locations
									// Y bytes - The content of location ID
									var len = Buffer.byteLength(
										jwtToken,
										'utf8'
									);
									var buf = Buffer.alloc(5 + 1 + len); //10 +
									buf[0] = 0x01;
									var pos = 1;
									pos = buf.writeInt32BE(len, pos);
									pos = buf.write(jwtToken, pos);
									pos += 5;
									buf[pos] = 0x00;

									stream.write(buf);
								}
							}
						]
					},
					function (socket) {
						startKafka(socket);
					}
				);
			})
			.catch((err) => log.error(err));

		async function startKafka(socket) {
			var myCustomSocketFactory = ({ host, port, ssl, onConnect }) => {
				socket.setKeepAlive(true, socketAliveTime);
				onConnect();
				return socket;
			};

			var broker = [
				'kafka.cloud:9092',
				'kafka:9092',
				'kafka-production:9092'
			];

			const kafka = new Kafka({
				clientId: 'dw-client',
				brokers: broker,
				retry: {
					initialRetryTime: 5000,
					retries: 2
				},
				requestTimeout: 30000,
				authenticationTimeout: 7000,
				socketFactory: myCustomSocketFactory,
				logLevel: logLevel.ERROR
			});

			const consumer = kafka.consumer({
				groupId: 'dw-consumer'
			});

			const run = async () => {
				// Consuming
				await consumer.connect();
				await consumer.subscribe({
					topic: /RAW_.*/i
				});
				console.log("Listening to Kafka now");

				let oBatchInsertQueue = {};

				function addIntoBatchInsertQueue(entity, value) {
					if (oBatchInsertQueue[entity]) {
						oBatchInsertQueue[entity].push(value);
					} else {
						oBatchInsertQueue[entity] = [value];
					}
				}

				const runBatchInserts = async () => {
					// clone the queue for thread safety and reset the other one
					const threadSafeQueueCopy = { ...oBatchInsertQueue };
					if (threadSafeQueueCopy !== {}) {
						oBatchInsertQueue = {};
						// iterate over copied queue and make batch inserts
						for (const [entity, values] of Object.entries(
							threadSafeQueueCopy
						)) {
							try {
								if (values.length > 0) {
									srv.run(
										INSERT.into(
											relevantServiceEntities[entity]
										).entries(
											values.filter((item) => item !== {})
										)
									).catch((error) => {
										log.error(error);
									});
								}
							} catch (e) {
								log.error(entity);
								log.error('Error has occurred', e);
							}
						}
					}
				};

				var fnBatchInterval = setInterval(() => {
					runBatchInserts();
				}, 5000);

				await consumer.run({
					autoCommitInterval: 5000,
					eachMessage: async ({ topic, partition, message }) => {
						// ---------------------------------------------------
						// --- BEGIN SPEED LAYER -----------------------------
						// ---------------------------------------------------
						if (oSpeedLayerTopics.hasOwnProperty(topic)) {
							let entry = JSON.parse(message.value.toString());
							if (entry.timestamp) {
								entry.timestamp = moment(
									entry.timestamp * 1000
								).format();
							}

							try {
								await srv.run(
									INSERT.into(
										oSpeedLayerTopics[topic]
									).entries([entry])
								);
							} catch (e) {
								log.error(entry);
								log.error('Error has occurred', e);
							}
						}
						// ---------------------------------------------------
						// --- BEGIN BATCH LAYER -----------------------------
						// ---------------------------------------------------
						else if (aBatchLayerTopics.indexOf(topic) !== -1) {
							let entry = JSON.parse(message.value.toString());
							let entries;
							if (entry.timestamp) {
								entry.timestamp = moment(
									entry.timestamp * 1000
								).format();
							}
							try {
								switch (topic) {
									case 'RAW_E_BLOCK':
										entries = await srv.run(
											SELECT.from(KPI_E_BLOCK).where({
												identifier: entry.identifier
											})
										);
										if (
											entries.length === 0 &&
											entry.identifier !== null &&
											entry.identifier !== undefined
										) {
											addIntoBatchInsertQueue(
												'KPI_E_BLOCK',
												entry
											);
										}
										break;
									case 'RAW_E_TOKEN':
										entries = await srv.run(
											SELECT.from(
												KPI_ENUM_ETHEREUM_TOKEN
											).where({
												symbol: entry.token
											})
										);
										if (entries.length === 0) {
											srv.run(
												INSERT.into(
													KPI_ENUM_ETHEREUM_TOKEN
												).entries([
													{
														symbol: entry.token,
														address: entry.address,
														name: entry.name
													}
												])
											);
										}
										if (entry.marketCapUsd === null) {
											entry.marketCapUsd = 0;
										}
										if (entry.availableSupply === null) {
											entry.availableSupply = 0;
										}

										delete entry.address;
										delete entry.name;
										addIntoBatchInsertQueue(
											'KPI_E_TOKEN',
											entry
										);
										break;
									case 'RAW_B_BLOCK':
										entries = await srv.run(
											SELECT.from(KPI_B_BLOCK)
												.orderBy({
													timestamp: 'desc'
												})
												.limit(1)
										);
										if (
											!entries[0] ||
											entries[0].blockTime !==
												entry.blockTime
										) {
											addIntoBatchInsertQueue(
												'KPI_B_BLOCK',
												entry
											);
										}
										break;
									case 'RAW_G_NODE_DISTRIBUTION':
										Object.keys(entry.countries).forEach(
											(country) => {
												addIntoBatchInsertQueue(
													'KPI_G_NODE_DISTRIBUTION',
													{
														timestamp:
															entry.timestamp,
														coin: entry.coin,
														country: country,
														nodes: parseInt(
															entry.countries[
																country
															]
														)
													}
												);
											}
										);
										addIntoBatchInsertQueue(
											'KPI_G_N_PER_TIME',
											{
												timestamp: entry.timestamp,
												coin: entry.coin,
												numOfNodes: parseInt(
													entry.nodeCount
												)
											}
										);
										break;
									case 'RAW_E_GASSTATION':
									default:
										entries = await srv.run(
											SELECT.from(
												KPI_E_EXT_GASSTATION
											).where({
												blockNumber: entry.blockNumber
											})
										);
										if (entries.length === 0) {
											addIntoBatchInsertQueue(
												'KPI_E_EXT_GASSTATION',
												entry
											);
										}
										break;
								}
							} catch (e) {
								log.error(entry);
								log.error('Error has occurred', e);
							}
						}
						// ---------------------------------------------------
						// --- HEALTH CHECKS ---------------------------------
						// ---------------------------------------------------
						else if (topic === 'RAW_HEALTH_CHECKS') {
							try {
								let api = message.value
									.toString()
									.replace(/\"/g, '');

								entries = await srv.run(
									SELECT.from(LOG_HEALTH_CHECK).where({
										api: api
									})
								);

								if (entries.length === 0) {
									srv.run(
										INSERT.into(LOG_HEALTH_CHECK).entries([
											{
												timestamp: moment().format(),
												api: api
											}
										])
									);
								} else {
									srv.run(
										UPDATE(LOG_HEALTH_CHECK)
											.set({
												timestamp: moment().format()
											})
											.where({
												api: "'" + api + "'"
											})
									);
								}
							} catch (e) {
								log.error('Error has occurred', e);
							}
						} else if (topic === 'RAW_FETCH_ERRORS') {
							try {
								let entry = JSON.parse(message.value);
								if (entry.timestamp) {
									entry.timestamp = moment(
										entry.timestamp
									).format();
								}
								const newEntry = {
									api: entry.topic,
									timestamp: entry.timestamp,
									message: entry.error
								};
								await srv.run(
									INSERT.into(LOG_FETCH_ERROR).entries([
										newEntry
									])
								);
							} catch (e) {
								log.error('Error has occurred', e);
							}
						}
					}
				});

				setTimeout(function () {
					consumer.pause([
						{
							topic: /RAW_.*/i
						}
					]);
					consumer.disconnect();
					clearInterval(fnBatchInterval);
					runBatchInserts();
				}, socketAliveTime);
			};

			run().catch(console.error);
		}
	};

	triggerListener();

	// Delay the socket restart interval
	setTimeout(() => {
		setInterval(function () {
			triggerListener();
		}, socketAliveTime);
	}, 1000);

	console.log('async start');
};
asyncInitialRunFn();

// Ping - Pong Health
const express = require('express');
const app = express();

app.get('/ping', function (req, res) {
	res.send('pong');
});

app.listen(8080);
