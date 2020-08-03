'use strict';
const hana = require('@sap/hana-client');
let conn = hana.createConnection();
let initialized = false;
let schema;

module.exports = {
	getDBConnection: function () {
		return initialized ? conn : null;
	},

	initializeDBConnection: function (options) {
		if (options) {
			try {
				const config = options.hana;
				schema = config.schema;

				const conn_params = {
					host: config.host,
					port: config.port,
					uid: config.user,
					pwd: config.password,
					ENCRYPT: true,
					sslValidateCertificate: false
				};

				conn.connect(conn_params);
				initialized = true;
			} catch (error) {
				console.error(error);
			}
		}
	},

	getSchema: function () {
		return initialized ? schema : null;
	}
};
