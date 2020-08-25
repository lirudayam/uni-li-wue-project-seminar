const {
  KPI_E_TOKEN,
  KPI_E_BLOCK,
  KPI_B_BLOCK,
  KPI_G_NODE_DISTRIBUTION,
  KPI_G_N_PER_TIME,
  KPI_E_EXT_GASSTATION,
  KPI_G_NEWS,
  LOG_FETCH_ERROR,
} = cds.entities("uni_li_wue.dw");

const moment = require("moment");

module.exports = async (srv) => {
  const fnBatchInsert = async (req, entity, array) => {
    const tx = cds.transaction(req);
    try {
      if (array.length > 0) {
        await tx.run(INSERT.into(entity).entries(array));
        return array.length;
      }
    } catch (error) {
      console.error(error);
    }
  };

  srv.on("KPI_E_TOKEN_BI", async (req) => {
    fnBatchInsert(req, KPI_E_TOKEN, req.data.array);
  });
  srv.on("KPI_G_NODE_DISTRIBUTION_BI", async (req) => {
    fnBatchInsert(req, KPI_G_NODE_DISTRIBUTION, req.data.array);
  });
  srv.on("KPI_G_N_PER_TIME_BI", async (req) => {
    fnBatchInsert(req, KPI_G_N_PER_TIME, req.data.array);
  });
  srv.on("KPI_E_EXT_GASSTATION_BI", async (req) => {
    fnBatchInsert(req, KPI_E_EXT_GASSTATION, req.data.array);
  });
  srv.on("KPI_G_NEWS_BI", async (req) => {
    fnBatchInsert(req, KPI_G_NEWS, req.data.array);
  });

  srv.before("CREATE", "KPI_E_BLOCK", async (req) => {
    const tx = cds.transaction(req);

    const entry = await tx.run(
      SELECT.from(KPI_E_BLOCK).where({
        identifier: req.data.identifier,
      })
    );
    if (entry && entry.length > 0) {
      await tx.run(
        DELETE.from(KPI_E_BLOCK).where({
          identifier: req.data.identifier,
        })
      );
    }
  });

  srv.before("CREATE", "KPI_B_BLOCK", async (req) => {
    const tx = cds.transaction(req);

    const entry = await tx.run(
      SELECT.from(KPI_B_BLOCK)
        .orderBy({
          timestamp: "desc",
        })
        .limit(1)
    );
    if (entry && entry.length > 0) {
      await tx.run(
        DELETE.from(KPI_B_BLOCK).where({
          timestamp: entry[0].timestamp,
        })
      );
    }
  });

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

  aTopics.forEach((sEntity) => {
    srv.before(["CREATE", "UPDATE"], sEntity, async (req) => {
      if (sEntity !== "KPI_G_GINI") {
        const { timestamp } = req.data;
        if (!timestamp) {
          req.data.timestamp = moment().format();
        }
      }
    });
  });

  aTopics.forEach((sEntity) => {
    srv.on(["CREATE", "UPDATE"], sEntity, async (req) => {
      try {
        const tx = cds.transaction(req);
        return await tx.run(req.query);
      } catch (error) {
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
  });
};
