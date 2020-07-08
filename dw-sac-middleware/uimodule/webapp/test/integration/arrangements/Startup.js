sap.ui.define([
  "sap/ui/test/Opa5"
], function(Opa5) {
  "use strict";

  return Opa5.extend("uni.li.wue.project.dwconfig.test.integration.arrangements.Startup", {

    iStartMyApp: function () {
      this.iStartMyUIComponent({
        componentConfig: {
          name: "uni.li.wue.project.dwconfig",
          async: true,
          manifest: true
        }
      });
    }

  });
});
