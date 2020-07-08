sap.ui.define([
  "sap/ui/test/Opa5",
  "uni/li/wue/project/dwconfig/test/integration/arrangements/Startup",
  "uni/li/wue/project/dwconfig/test/integration/BasicJourney"
], function(Opa5, Startup) {
  "use strict";

  Opa5.extendConfig({
    arrangements: new Startup(),
    pollingInterval: 1
  });

});
