define(["app/core/app_events"], function(appEvents) {
  'use strict';
  
  return {
    init: function() {
      console.log('Rhinometric Dashboard Builder Plugin Loaded');
      appEvents.emit('alert-success', ['Rhinometric Dashboard Builder loaded successfully!']);
    }
  };
});
