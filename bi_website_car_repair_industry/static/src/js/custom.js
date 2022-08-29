odoo.define('bi_website_car_repair_industry.web', function (require) {
'use strict';
	var publicWidget = require('web.public.widget');
	publicWidget.registry.portalDetails = publicWidget.Widget.extend({
		selector: '.container',
		events: {
			'change select[name="country_id"]': '_onCountryChange',
			// 'change select[name="car"]': '_onCarChange',
		},

		start: function () {
			var def = this._super.apply(this, arguments);
			this.$state = this.$('select[name="state_id"]');
			this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');

			// this.$model = this.$('select[name="model"]');
			// this.$modelOptions = this.$model.filter(':enabled').find('option:not(:first)');
			// this._onCarChange();

			this._adaptAddressForm();
			return def;
		},

		_onCarChange: function () {
			var $car = this.$('select[name="car"]');
			var carID = ($car.val() || 0);
			this.$modelOptions.detach();
			var $displayedModel = this.$modelOptions.filter('[data-car_id=' + carID + ']');
			var nb = $displayedModel.appendTo(this.$model).show().length;
			this.$model.parent().toggle(nb >= 1);
		},

		_adaptAddressForm: function () {
			var $country = this.$('select[name="country_id"]');
			var countryID = ($country.val() || 0);
			this.$stateOptions.detach();
			var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
			var nb = $displayedState.appendTo(this.$state).show().length;
			this.$state.parent().toggle(nb >= 1);
		},

		_onCountryChange: function () {
			this._adaptAddressForm();
		},
	});
});

