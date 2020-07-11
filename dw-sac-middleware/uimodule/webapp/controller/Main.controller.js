sap.ui.define(["sap/ui/core/mvc/Controller"], function (Controller) {
  "use strict";

  return Controller.extend("uni.li.wue.project.dwconfig.controller.Main", {
    onInit: function () {
      this.getView().addStyleClass(
        this.getOwnerComponent().getContentDensityClass()
      );
    },
  });
});
