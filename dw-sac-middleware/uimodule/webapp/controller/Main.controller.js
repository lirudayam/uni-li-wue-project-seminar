sap.ui.define(["sap/ui/core/mvc/Controller"], function (Controller) {
  "use strict";

  return Controller.extend("uni.li.wue.project.dwconfig.controller.Main", {
    onInit: function () {
      this.getView().addStyleClass(
        this.getOwnerComponent().getContentDensityClass()
      );
    },

    onRefreshHealthStatus: function () {
      var oTable = this.getView().byId("health_table");
      oTable.getBinding("items").refresh()
    },

    onRefreshDataStatus: function () {
      var oTable = this.getView().byId("data_table");
      oTable.getBinding("items").refresh()
    },

    onRefreshAPIConfig: function() {
      var oTable = this.getView().byId("config_table");
      oTable.getBinding("items").refresh()
    },

    onRefreshErrors: function () {
      var oTable = this.getView().byId("error_table");
      oTable.getBinding("items").refresh()
    }
  });
});
