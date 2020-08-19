const {
  KPI_E_TOKEN,
  KPI_E_BLOCK,
  KPI_B_BLOCK,
  KPI_G_NODE_DISTRIBUTION,
  KPI_G_N_PER_TIME,
  KPI_E_EXT_GASSTATION,
} = cds.entities("uni_li_wue.dw");

module.exports = async (srv) => {
  const fnBatchInsert = async (req, entity, array) => {
    const tx = cds.transaction(req);
    try {
      if (array.length > 0) {
        await tx.run(INSERT.into(entity).entries(array));
        return array.length;
      }
    } catch (error) {
      req._.req.logger.error(error.message, { event: req.event, error });
      throw error;
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
  srv.on("KPI_E_GASSTATION_BI", async (req) => {
    fnBatchInsert(req, KPI_E_EXT_GASSTATION, req.data.array);
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
};
