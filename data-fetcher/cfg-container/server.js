'use strict';

const express = require('express');
const axios = require('axios');
const cors = require('cors');

// Constants
const PORT = 8080;
const HOST = '0.0.0.0';

const iFallbackFetchInterval = 300.0;
const iFallbackAggregationInterval = 60.0;
const iFallbackHealthPingInterval = 60.0;

let oAPIBasedMetrics = {};
let iHealthPingInterval = iFallbackHealthPingInterval;

const sBaseURL = process.env.BASE_URL;

const getData = async () => {
    let sKPIConfigURL = "https://" + sBaseURL + "/configuration/KPI_CONFIG";
    let sAPIConfigURL = "https://" + sBaseURL + "/configuration/API_CONFIG('health_ping_interval')";
 
    axios.get(sKPIConfigURL)
    .then(function (response) {
        let aJSON = response.data["value"];
        aJSON.forEach(topic => {
            if (!oAPIBasedMetrics[topic]) {
                oAPIBasedMetrics[topic] = {};
            }
            oAPIBasedMetrics[topic].aggregationInterval = topic.aggregationInterval
            oAPIBasedMetrics[topic].fetchInterval = topic.fetchInterval
        })
    })
    .catch(function (error) {
        // handle error
        console.log(error);
    });

    axios.get(sAPIConfigURL)
    .then(function (response) {
        iHealthPingInterval = response.data["value"]
    })
    .catch(function (error) {
        // handle error
        console.log(error);
    });
};

setInterval(() => {getData()}, 60 * 1000);

// App
const app = express();
app.use(cors());

app.get('/health_ping_interval', async (req, res) => {
  res.send("" + iHealthPingInterval);
});

app.get('/aggregation_interval/:topic', async (req, res) => {
    const topic = req.params.topic;
    if (oAPIBasedMetrics[topic] && oAPIBasedMetrics[topic].aggregationInterval) {
        res.send("" + oAPIBasedMetrics[topic].aggregationInterval);
    }
    else {
        res.send("" + iFallbackAggregationInterval);
    }
});

app.get('/fetch_interval/:topic', async (req, res) => {
    const topic = req.params.topic;
    if (oAPIBasedMetrics[topic] && oAPIBasedMetrics[topic].fetchInterval) {
        res.send("" + oAPIBasedMetrics[topic].fetchInterval);
    }
    else {
        res.send("" + iFallbackFetchInterval);
    }
});

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);