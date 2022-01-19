odoo.define("year_widget", function(require) {
  "use strict";

  var field_registry = require("web.field_registry");
  var basic_fields = require("web.basic_fields");

  var YearWidget = basic_fields.FieldInteger.extend({
    template: "YearWidget",

    _render: function() {
      var intValue = parseInt(this.value);
      var parseIntValue = isNaN(intValue) ? 0 : intValue;

      if (this.mode !== "readonly") {
        var $input = this.$el.find("input");
        $input.val(intValue);
        this.$input = $input;
        this.$(".oe_field_year").text(parseIntValue);
      } else {
        this.$(".oe_field_year").text(parseIntValue);
      }
    }
  });
  field_registry.add("year", YearWidget);
});
