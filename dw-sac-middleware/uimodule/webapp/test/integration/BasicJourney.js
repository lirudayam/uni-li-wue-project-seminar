sap.ui.define([
  "sap/ui/test/opaQunit",
  "uni/li/wue/project/dwconfig/test/integration/pages/Main"
], function (opaTest) {
  "use strict";

  opaTest("should show correct number of nested pages", function (Given, When, Then) {

    // Arrangements
    Given.iStartMyApp();

    // Assertions
    Then.onTheAppPage.iShouldSeePageCount(1);

    // Cleanup
    Then.iTeardownMyApp();
  });

});
