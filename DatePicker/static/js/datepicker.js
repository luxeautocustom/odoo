odoo.define('swr.web.datepicker', function (require) {
    "use strict";
    
    var core = require('web.core');
    var DatePicker = require('web.datepicker');
    var fieldUtils = require('web.field_utils');
    var time = require('web.time');
    
    var _t = core._t;
    
    DatePicker.DateWidget.include({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            var _options = {};
            if (options && (options.showType==="months" || options.showType==="years")) {
                var l10n = _t.database.parameters;
                _options.viewMode = options.showType;
                _options.showMonthAfterYear = options.showMonthAfterYear;
                _options.format = time.strftime_to_moment_format((options.showType==="months")? l10n.month_format : l10n.year_format);
            }
            this.options = _.defaults(_options || {}, this.options);
        },
        
        _formatClient: function(v) {
            return fieldUtils.format[this.type_of_date](v, null, {timezone: false, datepicker: {showType: this.options.showType}});
        },
        _parseClient: function (v) {
            return fieldUtils.parse[this.type_of_date](v, null, {timezone: false, datepicker: {showType: this.options.showType}});
        }
        
    });
    return DatePicker;
    })
    
    odoo.define('swr.web.field_utils', function (require) {
    "use strict";
    
        var core = require('web.core');
        var fieldUtils = require('web.field_utils');
        var time = require('web.time');
        var origin_format_date = fieldUtils.format.date;
        var origin_parse_date = fieldUtils.parse.date;
        var _t = core._t;
    
        fieldUtils.format.date = function (value, field, options) {
            if (value && options) {
                var showType;
                if ('datepicker' in options && 'showType' in options.datepicker) {
                    showType = options.datepicker.showType;
                }
                if(showType === 'months' || showType === 'years') {
                    var l10n = _t.database.parameters;
                    var _format = time.strftime_to_moment_format((showType==="months")? l10n.month_format : l10n.year_format);
                    return value.format(_format);
                }
            }
            return origin_format_date(value, field, options);
        }
    
        fieldUtils.parse.date = function (value, field, options) {
            if (value && options) {
                var showType;
                if ('datepicker' in options && 'showType' in options.datepicker) {
                    showType = options.datepicker.showType;
                }
                if(showType === 'months' || showType === 'years') {
                    var l10n = _t.database.parameters;
                    var _format = time.strftime_to_moment_format(showType === 'months'? l10n.month_format : l10n.year_format);
                    var date_pattern = _format;
                    var date_pattern_wo_zero = date_pattern.replace('MM','M').replace('DD','D');
                    var date;
                    if (options && options.isUTC) {
                        date = moment.utc(value);
                    } else {
                        date = moment.utc(value, [date_pattern, date_pattern_wo_zero, moment.ISO_8601], true);
                    }
                    if (date.isValid()) {
                        if (date.year() === 0) {
                            date.year(moment.utc().year());
                        }
                        if (date.year() >= 1900) {
                            date.toJSON = function () {
                                return this.clone().locale('en').format('YYYY-MM-DD');
                            };
                            return date;
                        }
                    }
                    throw new Error(_.str.sprintf(core._t("'%s' is not a correct date"), value));
                }
            }
            return origin_parse_date(value, field, options);
        }
    
    })
    
    odoo.define('swr.web.ListRenderer', function (require) {
    "use strict";
    
        var ListRenderer = require('web.ListRenderer');
        var field_utils = require('web.field_utils');
        
        ListRenderer.include({
            _renderBodyCell: function (record, node, colIndex, options) {
                var $td = this._super.apply(this, arguments);
                var name = node.attrs.name;
                var field = this.state.fields[name];
                var value = record.data[name];
                var tmp = {
                    data: record.data,
                    escape: true,
                    isPassword: 'password' in node.attrs,
                };
                if (node.tag === 'button'||node.tag === 'widget'||node.attrs.widget || (options && options.renderWidgets)) {
                    return $td;
                }
                if (field && field.type==='date' && node.attrs.options) {
                    var json;
                    try {
                        json = JSON.parse(node.attrs.options);
                    } catch(e) {
                        json = JSON.parse(node.attrs.options.replace(/\'/g,"\""));
                    }
                    if(json) {
                        tmp = _.defaults(tmp, json);
                        var formattedValue = field_utils.format[field.type](value, field, tmp);
                        return $td.html(formattedValue);
                    }
                } else {
                    return $td;
                }
                
            }
        })
    
    })
    