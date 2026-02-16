System.register([], function (_export, _context) {
  "use strict";

  var RhinometricAPIConnectorApp;
  
  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError("Cannot call a class as a function");
    }
  }

  return {
    setters: [],
    execute: function () {
      _export("ConfigCtrl", RhinometricAPIConnectorApp = function RhinometricAPIConnectorApp() {
        _classCallCheck(this, RhinometricAPIConnectorApp);
      });

      RhinometricAPIConnectorApp.template = '\n        <div class="page-container page-body">\n          <div class="page-header">\n            <h1 style="color: #00d4aa; font-weight: 700;">\n              <i class="fa fa-plug"></i> RHINOMETRIC API Connector\n            </h1>\n          </div>\n          <div class="api-connector-iframe-container" style="height: calc(100vh - 100px); width: 100%;">\n            <iframe \n              src="http://localhost:8000" \n              style="width: 100%; height: 100%; border: 2px solid #00d4aa; border-radius: 4px;"\n              frameborder="0"\n              title="Rhinometric API Connector"\n            ></iframe>\n          </div>\n        </div>\n      ';

      _export("ConfigCtrl", RhinometricAPIConnectorApp);
    }
  };
});
