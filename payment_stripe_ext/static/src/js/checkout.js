odoo.define('payment_stripe_ext.FormRenderer', function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var BasicRenderer = require('web.BasicRenderer');
var FormRenderer = require('web.FormRenderer');

var _t = core._t;
var qweb = core.qweb;

ajax.loadXML('/payment_stripe_ext/static/src/xml/stripe_templates.xml', qweb);
$.getScript('https://js.stripe.com/v3/');

FormRenderer.include({
    events: _.extend({}, FormRenderer.prototype.events, {
        'click #pay_stripe': '_onClickpaystrip',
    }),
    _onClickpaystrip: function(e){
        console.log('Button Clicked')
        if(!$(e.currentTarget).find('i').length)
            $(e.currentTarget).append('<i class="fa fa-spinner fa-spin"/>');
            $(e.currentTarget).attr('disabled','disabled');
        var acquirer_id = $("input[name='acquirer']").val()
        if (! acquirer_id) {
            return false;
        }
        e.preventDefault();
        ajax.jsonRpc('/payment_stripe/transaction', 'call', {
            reference: $("input[name='invoice_num']").val(),
            amount: $("input[name='amount']").val(),
            currency_id: $("input[name='currency_id']").val(),
            partner: $("input[name='partner']").val(),
            acquirer_id: acquirer_id
        }).then(function (data){
            
            if (data.url) {
                window.location.href = data.url
            } else if(data.email_warning) {
                var wizard = $(qweb.render('stripe.error', {'msg': data.email_warning}));
                wizard.appendTo($('body')).modal({'keyboard': true});
            } else if(data.amount_warning) {
                var wizard = $(qweb.render('stripe.error', {'msg': data.amount_warning}));
                wizard.appendTo($('body')).modal({'keyboard': true});
            }
            else {
                var wizard = $(qweb.render('stripe.error', {'msg': 'We are not able to redirect you to the payment form.' || _t('Payment error')}));
                wizard.appendTo($('body')).modal({'keyboard': true});
            }
        })
    },
});
});
