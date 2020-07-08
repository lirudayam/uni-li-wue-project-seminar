/* global QUnit */

QUnit.config.autostart = false;

sap.ui.getCore().attachInit(function() {
  "use strict";

  sap.ui.require([
    "uni/li/wue/project/dwconfig/test/integration/AllJourneys"
  ], function() {
    QUnit.start();
  });
});
