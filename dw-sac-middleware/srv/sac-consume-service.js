const moment = require("moment");

module.exports = async (srv) => {
  /* Handlers for catching errors and documenting as an error */
  const aTopics = [
    "KPI_G_RICH_ACC",
    "KPI_G_N_PER_TIME",
    "KPI_G_PRICE_VOLA",
    "KPI_G_PRICES",
    "KPI_E_BLOCK",
    "KPI_B_BLOCK",
    "KPI_B_SPECIAL_EVT",
    "KPI_G_NEWS",
    "KPI_G_NODE_DISTRIBUTION",
    "KPI_G_RECOMM",
    "KPI_E_TOKEN",
    "KPI_G_GINI",
  ];

  aTopics.forEach(sEntity => {
    srv.on(["CREATE", "UPDATE"], sEntity, async (req) => {
        try {
          const tx = cds.transaction(req);
          return await tx.run(req.query);
        } catch (error) {
          const srv = await cds.connect.to("KafkaPublishService"); // > could be a local service, a remote one or a database
          const { LOG_FETCH_ERROR } = srv.entities;
          await srv.run(
            INSERT.into(LOG_FETCH_ERROR).entries([
              {
                api: sEntity,
                timestamp: moment().format(),
                message: "Insert error: " + req.query,
              },
            ])
          );
          throw error;
        }
      });
  })
  
};
