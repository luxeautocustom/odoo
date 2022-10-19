# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
import pprint

from odoo import api, fields, models, _
from odoo.tools import float_round, float_repr
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

def _partner_format_address(address1=False, address2=False):
    return ' '.join((address1 or '', address2 or '')).strip()

def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    backend_view_template_id = fields.Many2one('ir.ui.view', string='Backend Form Button Template')
    auto_payment = fields.Selection([
        ('none', 'No automatic payment'),
        ('generate_and_pay_invoice', 'Automatic pay invoice on acquirer confirmation')],
        string='Invoice Payment', default='none', required=True)

    def _wrap_payment_block(self, html_block, amount, currency_id):
        payment_header = _('Pay safely online')
        currency = self.env['res.currency'].browse(currency_id)
        amount_str = float_repr(amount, currency.decimal_places)
        currency_str = currency.symbol or currency.name
        amount = u"%s %s" % ((currency_str, amount_str) if currency.position == 'before' else (amount_str, currency_str))
        result = u"""<div class="payment_acquirers">
                 <div class="payment_header">
                     <div class="payment_amount">%s</div>
                     %s
                 </div>
                 %%s
             </div>""" % (amount, payment_header)
        return result % html_block.unescape()

    def render_payment_block(self, reference, amount, currency_id, tx_id=None, partner_id=False, partner_values=None, tx_values=None, company_id=None):
        html_forms = []
        domain = [('state', '!=', 'disabled'), ('provider', '=', 'stripe')]
        if company_id:
            domain.append(('company_id', '=', company_id))
        acquirer_ids = self.search(domain)
        for acquirer_id in acquirer_ids:
            button = acquirer_id.render(
                reference, amount, currency_id,
                partner_id, tx_values)
            html_forms.append(button)
        if not html_forms:
            return ''
        # html_block = (b'\n').join(html_forms[0])
        return self._wrap_payment_block(html_forms[0], amount, currency_id)

    def render(self, reference, amount, currency_id, partner_id=False, values=None):
        """ Renders the form template of the given acquirer as a qWeb template.
        :param string reference: the transaction reference
        :param float amount: the amount the buyer has to pay
        :param currency_id: currency id
        :param dict partner_id: optional partner_id to fill values
        :param dict values: a dictionary of values for the transction that is
        given to the acquirer-specific method generating the form values

        All templates will receive:

         - acquirer: the payment.acquirer browse record
         - user: the current user browse record
         - currency_id: id of the transaction currency
         - amount: amount of the transaction
         - reference: reference of the transaction
         - partner_*: partner-related values
         - partner: optional partner browse record
         - 'feedback_url': feedback URL, controler that manage answer of the acquirer (without base url) -> FIXME
         - 'return_url': URL for coming back after payment validation (wihout base url) -> FIXME
         - 'cancel_url': URL if the client cancels the payment -> FIXME
         - 'error_url': URL if there is an issue with the payment -> FIXME
         - context: Odoo context

        """
        invoice_id = self.env['account.move'].search([('name','=',reference.split('-')[0])])
        if not self._context.get('call_backend', False):
            if not invoice_id.partner_id.email:
                return {'email_warning': 'Customer Email is required to perform transaction.'}
            elif invoice_id.amount_total < 0.50: 
                return {'amount_warning': 'We are not able to redirect you to the payment form.Payment amount should be above 0.49' + invoice_id.currency_id.symbol + '.'}
        if values is None:
            values = {}

        # if not self.view_template_id:
        #     return None

        values.setdefault('return_url', '/payment/process')
        # reference and amount
        values.setdefault('reference', reference)
        amount = float_round(amount, 2)
        values.setdefault('amount', amount)

        # currency id
        currency_id = values.setdefault('currency_id', currency_id)
        if currency_id:
            currency = self.env['res.currency'].browse(currency_id)
        else:
            currency = self.env.company.currency_id
        values['currency'] = currency

        # Fill partner_* using values['partner_id'] or partner_id argument
        partner_id = values.get('partner_id', partner_id)
        billing_partner_id = values.get('billing_partner_id', partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner_id != billing_partner_id:
                billing_partner = self.env['res.partner'].browse(billing_partner_id)
            else:
                billing_partner = partner
            values.update({
                'partner': partner,
                'partner_id': partner_id,
                'partner_name': partner.name,
                'partner_lang': partner.lang,
                'partner_email': partner.email,
                'partner_zip': partner.zip,
                'partner_city': partner.city,
                'partner_address': _partner_format_address(partner.street, partner.street2),
                'partner_country_id': partner.country_id.id or self.env['res.company']._company_default_get().country_id.id,
                'partner_country': partner.country_id,
                'partner_phone': partner.phone,
                'partner_state': partner.state_id,
                'billing_partner': billing_partner,
                'billing_partner_id': billing_partner_id,
                'billing_partner_name': billing_partner.name,
                'billing_partner_commercial_company_name': billing_partner.commercial_company_name,
                'billing_partner_lang': billing_partner.lang,
                'billing_partner_email': billing_partner.email,
                'billing_partner_zip': billing_partner.zip,
                'billing_partner_city': billing_partner.city,
                'billing_partner_address': _partner_format_address(billing_partner.street, billing_partner.street2),
                'billing_partner_country_id': billing_partner.country_id.id,
                'billing_partner_country': billing_partner.country_id,
                'billing_partner_phone': billing_partner.phone,
                'billing_partner_state': billing_partner.state_id,
            })
        if values.get('partner_name'):
            values.update({
                'partner_first_name': _partner_split_name(values.get('partner_name'))[0],
                'partner_last_name': _partner_split_name(values.get('partner_name'))[1],
            })
        if values.get('billing_partner_name'):
            values.update({
                'billing_partner_first_name': _partner_split_name(values.get('billing_partner_name'))[0],
                'billing_partner_last_name': _partner_split_name(values.get('billing_partner_name'))[1],
            })

        # Fix address, country fields
        if not values.get('partner_address'):
            values['address'] = _partner_format_address(values.get('partner_street', ''), values.get('partner_street2', ''))
        if not values.get('partner_country') and values.get('partner_country_id'):
            values['country'] = self.env['res.country'].browse(values.get('partner_country_id'))
        if not values.get('billing_partner_address'):
            values['billing_address'] = _partner_format_address(values.get('billing_partner_street', ''), values.get('billing_partner_street2', ''))
        if not values.get('billing_partner_country') and values.get('billing_partner_country_id'):
            values['billing_country'] = self.env['res.country'].browse(values.get('billing_partner_country_id'))

        # compute fees
        fees_method_name = '%s_compute_fees' % self.provider
        if hasattr(self, fees_method_name):
            fees = getattr(self, fees_method_name)(values['amount'], values['currency_id'], values.get('partner_country_id'))
            values['fees'] = float_round(fees, 2)

        values.update({
            'tx_url': '',
            'submit_class': self._context.get('submit_class', 'btn btn-link'),
            'submit_txt': self._context.get('submit_txt'),
            'acquirer': self,
            'user': self.env.user,
            'context': self._context,
            'type': values.get('type') or 'form',
        })

        _logger.info('payment.acquirer.render: <%s> values rendered for form payment:\n%s', self.provider, pprint.pformat(values))
        # Change(s) add to the replaced method.
        if self.backend_view_template_id and self._context.get('call_backend'):
            return self.backend_view_template_id._render(values, engine='ir.qweb')
        transaction_id = self.env['payment.transaction'].search([('reference','=',values['reference'])])
        invoice_id = transaction_id.invoice_ids[0]
        session = transaction_id._stripe_create_checkout_session()
        if session.get('url',False):
            return {'url':session['url']}
        else:
            raise ValidationError(_(
                'We are not able to redirect you to the payment form.'
            ))
