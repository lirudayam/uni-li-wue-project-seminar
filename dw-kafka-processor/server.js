const { Kafka, logLevel } = require("kafkajs");
const oauthClient = require("client-oauth2");

const xsenv = require("@sap/xsenv");
const moment = require("moment");

const conn_service = xsenv.getServices({
  connectivity: function (service) {
    return service.label === "connectivity";
  },
}).connectivity;

String.prototype.getBytes = function () {
  var bytes = [];
  for (var i = 0; i < this.length; ++i) {
    bytes.push(this.charCodeAt(i));
  }
  return bytes;
};

const cds = require("@sap/cds");
const asyncf = async () => {
  const srv = await cds.connect.to("externalService");
  const entites = srv.entities("uni_li_wue.dw");
  let relevantServiceEntites = {};
  Object.keys(entites).map((key) => {
    if (key.startsWith("service.KafkaPublishService.")) {
      relevantServiceEntites[key.replace("service.KafkaPublishService.", "")] =
        entites[key];
    }
  });

  const {
    KPI_ENUM_COINS,
    KPI_ENUM_STOCK_MARKETS,
    KPI_ENUM_EVENTS,
    KPI_ENUM_SEMANTICS,
    KPI_ENUM_STREAM_ENTRY,
    KPI_TIME_CONFIG,
    KPI_REFRESH_CONFIG,
    KPI_NOTIFICATION_CONFIG,
    KPI_G_RICH_ACC,
    KPI_G_T_PER_TIME,
    KPI_E_SMART_EXEC,
    KPI_G_N_PER_TIME,
    KPI_G_TRANSACT_INF,
    KPI_G_PRICE_VOLA,
    KPI_G_PRICES,
    KPI_B_SPECIAL_EVT,
    KPI_G_NEWS,
    KPI_G_RECOMM,
    KPI_G_CREDITS,
    LOG_FETCH_ERROR,
    LOG_HEALTH_CHECK,
    KPI_E_GASSTATION,
    KPI_G_LATEST_BLOCK
  } = relevantServiceEntites;

  var oSimpleTopicMaps = {
    RAW_G_RICH_ACC: KPI_G_RICH_ACC,
    RAW_G_T_PER_TIME: KPI_G_T_PER_TIME,
    RAW_E_SMART_EXEC: KPI_E_SMART_EXEC,
    RAW_G_N_PER_TIME: KPI_G_N_PER_TIME,

    RAW_G_TRANSACT_INF: KPI_G_TRANSACT_INF,

    RAW_G_PRICE_VOLA: KPI_G_PRICE_VOLA,
    RAW_G_PRICES: KPI_G_PRICES,
    RAW_B_SPECIAL_EVT: KPI_B_SPECIAL_EVT,

    RAW_G_NEWS: KPI_G_NEWS,
    RAW_G_RECOMM: KPI_G_RECOMM,
    RAW_G_CREDITS: KPI_G_CREDITS,
  };

  const socketAliveTime = 60 * 60 * 1000;

  var socks = require("@luminati-io/socksv5");

  const _getTokenForDestinationService = function () {
    return new Promise((resolve, reject) => {
      let tokenEndpoint = conn_service.token_service_url + "/oauth/token";
      const client = new oauthClient({
        authorizationUri: conn_service.token_service_url + "/oauth/authorize",
        accessTokenUri: tokenEndpoint,
        clientId: conn_service.clientid,
        clientSecret: conn_service.clientsecret,
        scopes: [],
        grant_type: "client_credentials",
      });
      client.credentials
        .getToken()
        .catch((error) => {
          return reject({
            message:
              "Error: failed to get access token for Connectivity service",
            error: error,
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
        console.log("START");

        var STATE_VERSION = 0,
          STATE_RESPONSE = 1,
          STATE_2VERSION = 2,
          STATE_STATUS = 3;

        socks.connect(
          {
            host: "kafka.cloud",
            port: 9092,
            proxyHost: conn_service.onpremise_proxy_host,
            proxyPort: parseInt(conn_service.onpremise_socks5_proxy_port, 10),
            localDNS: false,
            strictLocalDNS: true,
            auths: [
              {
                METHOD: 0x80,
                client: function clientHandler(stream, cb) {
                  console.log("BEGIN AUTH");
                  var state = STATE_2VERSION;

                  function onData(chunk) {
                    var i = 0,
                      len = chunk.length;

                    while (i < len) {
                      console.log(chunk[i]);
                      switch (state) {
                        case STATE_2VERSION:
                          if (chunk[i] !== 0x01) {
                            stream.removeListener("data", onData);
                            cb(
                              new Error(
                                "Unsupported auth request version: " + chunk[i]
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
                          stream.removeListener("data", onData);
                          cb(true);
                          return;
                          break;
                      }
                    }
                  }
                  stream.on("data", onData);

                  // === Authenticate ==
                  // Send the following bytes
                  // 1 byte - authentication method version: 1
                  // 4 bytes - length of JWT token acquired from XSUAA OAuth
                  // X bytes - The content of JWT token acquired from XSUAA OAuth
                  // 1 byte - Length of Cloud Connector location ID: Currently 0 because we don't CC locations
                  // Y bytes - The content of location ID
                  var len = Buffer.byteLength(jwtToken, "utf8");
                  var buf = Buffer.alloc(5 + 1 + len); //10 +
                  buf[0] = 0x01;
                  var pos = 1;
                  pos = buf.writeInt32BE(len, pos);
                  pos = buf.write(jwtToken, pos);
                  pos += 5;
                  buf[pos] = 0x00;

                  stream.write(buf);
                },
              },
            ],
          },
          function (socket) {
            startKafka(socket);
          }
        );
        console.log("DONE");
      })
      .catch((err) => console.log(err));

    async function startKafka(socket) {
      var myCustomSocketFactory = ({ host, port, ssl, onConnect }) => {
        console.log("Start listening to Kafka", host, port, ssl);
        socket.setKeepAlive(true, socketAliveTime);
        onConnect();
        socket.pipe(process.stdout);

        return socket;
      };

      var broker = ["kafka.cloud:9092", "kafka:9092", "kafka-production:9092"];

      const kafka = new Kafka({
        clientId: "dw-client",
        brokers: broker,
        retry: {
          initialRetryTime: 5000,
          retries: 2,
        },
        requestTimeout: 30000,
        authenticationTimeout: 7000,
        socketFactory: myCustomSocketFactory,
        logLevel: logLevel.ERROR,
      });

      const consumer = kafka.consumer({ groupId: "dw-consumer" });

      const run = async () => {
        // Consuming
        await consumer.connect();
        await consumer.subscribe({ topic: /RAW_.*/i });

        await consumer.run({
          autoCommitInterval: 5000,
          eachMessage: async ({ topic, partition, message }) => {
            if (oSimpleTopicMaps.hasOwnProperty(topic)) {
              try {
                let entry = JSON.parse(message.value.toString());
                if (entry.timestamp) {
                  entry.timestamp = moment(entry.timestamp * 1000).format();
                }
                
                await srv.run(
                  INSERT.into(oSimpleTopicMaps[topic]).entries([entry])
                );
              } catch (e) {
                //console.error("Error has occurred", e);
              }
            } else if (topic === 'RAW_E_GASSTATION' || topic === 'RAW_G_LATEST_BLOCK') {
                let entry = JSON.parse(message.value.toString());
                let entries = null;
                if (entry.timestamp) {
                  entry.timestamp = moment(entry.timestamp * 1000).format();
                }
                
                switch (topic) {
                  case 'RAW_G_LATEST_BLOCK':
                    entries = await srv.run(
                      SELECT.from(KPI_G_LATEST_BLOCK).where({
                        identifier: entry.identifier,
                        coin: entry.coin
                      })
                    );
                    if (entries.length === 0) {
                      await srv.run(
                        INSERT.into(KPI_G_LATEST_BLOCK).entries([entry])
                      );
                    }
                    break;
                  case 'RAW_E_GASSTATION':
                  default:
                    entries = await srv.run(
                      SELECT.from(KPI_E_GASSTATION).where({
                        blockNumber: entry.blockNumber,
                      })
                    );
                    if (entries.length === 0) {
                      await srv.run(
                        INSERT.into(KPI_E_GASSTATION).entries([entry])
                      );
                    }
                    break;
                }
            } else if (topic === "RAW_HEALTH_CHECKS") {
              try {
                let api = message.value.toString().replace(/\"/g, "");

                entries = await srv.run(
                  SELECT.from(LOG_HEALTH_CHECK).where({
                    api: api,
                  })
                );
                console.log("ENTRIES", entries);
                if (entries.length === 0) {
                  await srv.run(INSERT.into(LOG_HEALTH_CHECK).entries([
                    {
                      timestamp: moment().format(),
                      api: api,
                    }
                  ]));
                } else {
                  await srv.run(
                    UPDATE(LOG_HEALTH_CHECK)
                      .set({
                        timestamp: moment().format(),
                      })
                      .where({
                        api: "'" + api + "'",
                      })
                  );
                }
              } catch (e) {
                console.error("Error has occurred", e);
              }
            } else if (topic === "RAW_FETCH_ERROR") {
              try {
                let entry = JSON.parse(message.value);
                if (entry.timestamp) {
                  entry.timestamp = moment(entry.timestamp).format();
                }
                await srv.run(INSERT.into(LOG_FETCH_ERROR).entries([entry]));
              } catch (e) {
                console.error("Error has occurred", e);
              }
            }
          },
        });

        setTimeout(function () {
          consumer.pause([{ topic: /RAW_.*/i }]);
          consumer.disconnect();
          delete consumer;
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
  console.log("async start");
};
asyncf();

const express = require("express");
const app = express();

app.get("/", function (req, res) {
  res.send("Hello World");
});

app.listen(8080);
