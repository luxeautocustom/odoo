# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging

from datetime import datetime

from lxml import etree, html

from odoo.addons.authorize_net.models.authorize_request import AuthorizeAPI
from odoo.addons.authorize_net.models import misc
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderAuthCapture(models.TransientModel):
    _name = "authorize.transaction"
    _description = "Authorize Transaction"

    @api.model
    def default_get(self, fields):
        res = super(SaleOrderAuthCapture, self).default_get(fields)
        context = dict(self.env.context or {})
        if context.get('active_id') and context.get('active_model') == 'sale.order':
            sale_order_id = self.env['sale.order'].browse(context['active_id'])
            remaining_amount = sale_order_id.amount_total - sale_order_id.payment_amount
            company_order_id = self.env['sale.order'].search([('company_id', 'child_of', [self.env.company.id]),
                                                              ('user_id', '=', self.env.uid),
                                                              ('id', '=', sale_order_id.id)], limit=1)
            cid, token = False, False
            if company_order_id:
                cid = sale_order_id.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id.id == sale_order_id.company_id.id)
            else:
                cid = sale_order_id.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id.id == self.env.company.id)
            if not cid and company_order_id:
                token = sale_order_id.partner_id.payment_token_ids.filtered(lambda x: x.company_id.id == sale_order_id.company_id.id and\
                            x.acquirer_ref and x.acquirer_id.provider == 'authorize')
            elif not cid:
                token = sale_order_id.partner_id.payment_token_ids.filtered(lambda x: x.company_id.id == self.env.company.id and\
                            x.acquirer_ref and x.acquirer_id.provider == 'authorize')
            res.update({
                'partner_id': sale_order_id.partner_id.id,
                'order_amount': remaining_amount,
                'merchant_id': cid.merchant_id if cid else False,
                'customer_profile_id': cid.customer_profile_id if cid else token.authorize_profile,
                'shipping_address_id': cid.shipping_address_id if cid else False,
                'company_id': cid.company_id.id if cid else token.company_id.id,
                #'acquirer_id': cid.acquirer_id.id if cid else token.acquirer_id.id,
            })
        return res

    @api.model
    def _get_authorize_payment_type(self, context=None):
        vals = []
        payment_types = self.env['payment.acquirer'].search([('provider', '=', 'authorize'), \
                        ('company_id', '=', self.env.company.id)]).mapped('authorize_payment_method_type')
        if 'credit_card' in payment_types and 'bank_account' in payment_types:
            vals.extend([('credit_card', 'Credit Card'), ('bank_account', 'eCheck.Net')])
        elif 'credit_card' in payment_types:
            vals.extend([('credit_card', 'Credit Card')])
        elif 'bank_account' in payment_types:
            vals.extend([('bank_account', 'eCheck.Net')])
        return vals

    def _get_billing_partner_domain(self):
        domain = [('type', '=', 'invoice')]
        if self._context.get('active_id') and self._context.get('active_model') == 'sale.order':
            sale_order_id = self.env['sale.order'].browse(self._context['active_id'])
            domain.append(('parent_id', '=', sale_order_id.partner_id.id))
        return domain

    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', copy=False)
    company_id = fields.Many2one('res.company', 'Company', index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string="Partner")
    authorize_payment_type = fields.Selection(selection=_get_authorize_payment_type, string='Authorize Transaction')
    transaction_type = fields.Selection([('authorize', 'Authorize'), ('auth_capture', 'Authorize and Capture')],
                                        'Transaction Type', default='authorize')
    merchant_id = fields.Char(string='Merchant')
    customer_profile_id = fields.Char(string='Customer Profile ID', size=64, readonly=True)
    shipping_address_id = fields.Char(string='Shipping ID', size=64, readonly=True)
    payment_token_id = fields.Many2one('payment.token', string='Credit Card', domain="[('partner_id','=', partner_id), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('authorize_payment_method_type', '=', 'credit_card')]")
    payment_token_bank_id = fields.Many2one('payment.token', string='Bank Account', domain="[('partner_id','=', partner_id), '|', ('company_id', '=', False), ('company_id', '=', company_id), ('authorize_payment_method_type', '=', 'bank_account')]")
    billing_partner_id = fields.Many2one('res.partner', 'Billing Partner', domain=_get_billing_partner_domain)
    # ECHECK PAYMENT: Add BANK Fields For Direct Payment
    routing_number = fields.Char('Routing Number', size=9)
    authorize_bank_type = fields.Selection([('checking', 'Personal Checking'), ('savings', 'Personal Savings'),('businessChecking', 'Business Checking')], 'Authorize Bank Type', default='checking')
    bank_name = fields.Char('Bank Name', size=64)

    authorize_cc = fields.Boolean('Authorize Customer Credit card', default=False)
    order_amount = fields.Float('Amount')
    is_wo_save_card = fields.Boolean('Direct Payment(Without Save Card)', default=False, copy=False)
    is_wo_save_bank_acc = fields.Boolean('Direct Payment(Without Save Bank Details)', default=False, copy=False)
    cc_type = fields.Selection([('americanexpress', 'American Express'),
                                ('visa', 'Visa'),
                                ('mastercard', 'Mastercard'),
                                ('discover', 'Discover'),
                                ('dinersclub', 'Diners Club'),
                                ('jcb', 'JCB')], 'Card Type', readonly=True, copy=False)
    cc_number = fields.Char('Card Number', size=16, copy=False)
    cc_cvv = fields.Char('CVV', size=4, copy=False)
    cc_month = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
                                                     ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
                                                     ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12'),
                                                     ('xx', 'xx')], 'Expires Month', copy=False)
    cc_year = fields.Char('Expires Year', size=64, copy=False)
    acc_number = fields.Char('Account Number', copy=False)
    acc_name = fields.Char('Owner Name')

    @api.onchange("cc_number", "is_wo_save_card", "authorize_payment_type", "is_wo_save_bank_acc")
    def onchange_cc_number(self):
        if self.authorize_payment_type == 'bank_account':
            self.is_wo_save_card = False
        if self.authorize_payment_type == 'credit_card':
            self.is_wo_save_bank_acc = False
        if not self.is_wo_save_card:
            self.cc_number = self.cc_type = self.cc_year = self.cc_month = self.cc_cvv = self.payment_token_id = False
        if self.is_wo_save_card:
            self.payment_token_id = False
        if not self.is_wo_save_bank_acc:
            self.acc_number = self.acc_name = self.routing_number = False
        if self.cc_number:
            self.cc_type = misc.cc_type(self.cc_number) or False

    @api.onchange('payment_token_id', 'authorize_payment_type')
    def onchange_token_id(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        if self.payment_token_id and self.authorize_payment_type == 'credit_card' \
            and not self.payment_token_id.authorize_card:
            self.update({
                'merchant_id': False,
                'customer_profile_id': self.payment_token_id.authorize_profile,
                'shipping_address_id': False,
                'acquirer_id': self.payment_token_id.acquirer_id.id
            })
        elif context.get('active_id') and context.get('active_model') == 'sale.order':
            acquirer_id = self.env['payment.acquirer'].search([('provider', '=', 'authorize'), \
                            ('company_id', '=', self.env.company.id), \
                            ('authorize_payment_method_type', '=', self.authorize_payment_type)], limit=1)
            sale_order_id = self.env['sale.order'].browse(context['active_id'])
            company_order_id = self.env['sale.order'].search([('company_id', 'child_of', [self.env.company.id]),
                                                              ('user_id', '=', self.env.uid),
                                                              ('id', '=', sale_order_id.id)], limit=1)
            cid = False
            if company_order_id:
                cid = sale_order_id.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id and x.company_id.id == sale_order_id.company_id.id)
            else:
                cid = sale_order_id.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id and x.company_id.id == self.env.company.id)
            if cid:
                self.update({
                    'merchant_id': cid.merchant_id,
                    'customer_profile_id': cid.customer_profile_id,
                    'shipping_address_id': cid.shipping_address_id,
                    'company_id': cid.company_id and cid.company_id.id or False,
                    'acquirer_id': acquirer_id and acquirer_id.id or False
                })

    @api.model
    def text_from_html(self, html_content, max_words=None, max_chars=None, ellipsis=u"…", fail=False):
        try:
            doc = html.fromstring(html_content)
        except (TypeError, etree.XMLSyntaxError, etree.ParserError):
            _logger.exception("Failure parsing this HTML:\n%s", html_content)
            return ""

        words = u"".join(doc.xpath("//text()")).split()
        text = u" ".join(words)

        return text

    def auth_payment(self):
        self.ensure_one()
        journal_obj = self.env['account.journal']
        context = dict(self.env.context or {})
        order_id = False
        if context.get('active_id') and context.get('active_model'):
            order_id = self.env['sale.order'].browse(context['active_id'])
        if not self.acquirer_id:
            raise ValidationError(_("Please configure your Authorize.Net account."))
        journal_id = self.acquirer_id.journal_id
        if not journal_id or not self.acquirer_id.journal_id:
            raise ValidationError(_("Please configure Authorize payment journal"))
        # Convert Currency Amount
        from_currency_id = order_id and order_id.currency_id
        to_currency_id = journal_id.currency_id or journal_id.company_id.currency_id
        currency_amount = self.order_amount
        if from_currency_id and to_currency_id and from_currency_id != to_currency_id:
            currency_amount = from_currency_id._convert(self.order_amount, to_currency_id, journal_id.company_id, fields.Date.today())

        transaction_vals = {
            'partner_id': self.partner_id.id,
            'acquirer_id': self.acquirer_id.id,
            'amount': self.order_amount,
            'transaction_type': 'debit',
            'currency_id': order_id.currency_id.id,
            'sale_order_ids':[(6, 0, [order_id.id])],
            'company_id': self.acquirer_id.company_id.id,
        }
        try:
            resp = None
            if self.authorize_payment_type == 'credit_card' and order_id:
                charge_data = {
                    'invoiceNumber': order_id.name[:19] + '/' if len(order_id.name) > 20 else order_id.name,
                    'description': order_id.note,
                    'amount': str(round(currency_amount, 2)),
                    'refId': self.merchant_id
                }
                if self.authorize_payment_type == 'credit_card' and self.payment_token_id\
                    and not self.payment_token_id.authorize_card:
                    charge_data.update({'refId': False})
                for item in order_id.order_line:
                    if not item.product_id:
                        continue
                    itemId = item.product_id.default_code or str(item.product_id.id)
                    line_item = {
                        'lineItem': {
                            'itemId': itemId[:30] + '/' if len(itemId) > 31 else itemId,
                            'name': item.product_id.name[:30] + '/' if len(item.product_id.name) > 31 else item.product_id.name,
                            'description': item.name[:254] + '/'  if len(item.name) > 255 else item.name,
                            'quantity': str(item.product_uom_qty).replace('-', ''),
                            'unitPrice': str(item.price_unit).replace('-', ''),
                        },
                    }
                    if item.tax_id:
                        charge_data.update({'taxable': 'true'})
                    charge_data.update({'line_items': line_item})
                charge_data.update({'shipping_address_id':order_id.partner_shipping_id})
                if self.transaction_type == 'authorize':
                    if self.is_wo_save_card:
                        expiry_date = self.cc_year + '-' + self.cc_month
                        if datetime.now().strftime('%Y%m') > datetime.strptime(expiry_date, '%Y-%m').strftime('%Y%m'):
                            raise ValidationError(_("Expiration date not valid."))

                        billing_detail = self.partner_id.get_partner_billing_address(self.billing_partner_id)
                        # Create the payment data for a credit card
                        card_details = {
                            'cc_number': str(self.cc_number),
                            'expiry_date': expiry_date,
                            'cc_cvv': self.cc_cvv,
                            'billing': billing_detail.get('billing')
                        }
                        charge_data.update(card_details)
                        authorize_api = AuthorizeAPI(self.acquirer_id)
                        resp = authorize_api.authorize_charge(charge_data=charge_data)
                    else:
                        if self.payment_token_id.acquirer_ref:
                            authorize_api = AuthorizeAPI(self.acquirer_id)
                            charge_data.update({
                                'customer_profile_id': str(self.customer_profile_id),
                                'token': self.payment_token_id
                            })
                            resp = authorize_api.authorize_charge(charge_data=charge_data)
                    self.update({'cc_number': '', 'cc_cvv': '', 'cc_type': '', 'cc_year': '', 'cc_month': ''})
                    if resp is not None:
                        transaction_id = self.env['payment.transaction'].create(transaction_vals)
                        trans_id = resp.get('x_trans_id')
                        status_code = int(resp.get('x_response_code', '0'))
                        if trans_id and status_code:
                            tx_vals = {'acquirer_reference': str(trans_id)}
                            if not self.is_wo_save_card:
                                tx_vals.update({'token_id': self.payment_token_id.id})
                            transaction_id.write(tx_vals)
                            if status_code == 1:
                                if self.payment_token_id.acquirer_ref:
                                    order_id.authorize_cc = True
                                transaction_id.write({'state_message': resp.get('x_response_reason_text')})
                                transaction_id._set_authorized()
                                order_id.authorize_cc = True
                                order_id.payment_authorize = True
                                if transaction_id:
                                    order_id.write({'transaction_ids': [(4, transaction_id.id)]})
                                    order_id.action_confirm()
                            elif status_code == 4:
                                transaction_id._set_pending()
                            else:
                                error = resp.get('x_response_reason_text', "Authorize Transaction Error")
                                _logger.info(error)
                                transaction_id._set_error(state_message=error)

                #  Applied Changes using sale order payment auth_capture
                elif self.transaction_type == 'auth_capture':
                    # Transaction amount same or less of order amount total
                    remaining_amount = order_id.amount_total - order_id.payment_amount
                    if remaining_amount < self.order_amount:
                        raise ValidationError("Transaction Failed!, Your credit amount grater than order amount.'")
                    if self.is_wo_save_card:
                        expiry_date = self.cc_year + '-' + self.cc_month
                        if datetime.now().strftime('%Y%m') > datetime.strptime(expiry_date, '%Y-%m').strftime('%Y%m'):
                            raise ValidationError(_("Expiration date not valid."))

                        billing_detail = self.partner_id.get_partner_billing_address(self.billing_partner_id)
                        # Create the payment data for a credit card
                        card_details = {
                            'card_number': str(self.cc_number),
                            'expiry_date': expiry_date,
                            'card_code': self.cc_cvv,
                        }
                        charge_data.update({'billing': billing_detail.get('billing')})
                        authorize_api = AuthorizeAPI(self.acquirer_id)
                        resp = authorize_api.auth_and_capture_charge(charge_data=charge_data, card_details=card_details)
                    elif self.payment_token_id.acquirer_ref:
                        authorize_api = AuthorizeAPI(self.acquirer_id)
                        charge_data.update({
                            'customer_profile_id': str(self.customer_profile_id),
                            'paymentProfileId': self.payment_token_id.acquirer_ref
                        })
                        resp = authorize_api.auth_and_capture_charge(charge_data=charge_data)
                    self.update({'cc_number': '', 'cc_cvv': '', 'cc_type': '', 'cc_year': '', 'cc_month': ''})
                    if resp is not None:
                        transaction_id = self.env['payment.transaction'].create(transaction_vals)
                        trans_id = resp.get('x_trans_id')
                        status_code = int(resp.get('x_response_code', '0'))
                        if trans_id and status_code:
                            tx_vals = {'acquirer_reference': str(trans_id)}
                            if not self.is_wo_save_card:
                                tx_vals.update({'token_id': self.payment_token_id.id})
                            transaction_id.write(tx_vals)
                            if status_code == 1:
                                transaction_id.write({
                                    'last_state_change': fields.Datetime.now(),
                                    'state': 'done',
                                    'state_message': resp.get('x_response_reason_text')
                                })
                                order_id.payment_authorize = True
                                order_id.write({'transaction_ids': [(4, transaction_id.id)]})
                                if transaction_id:
                                    payment_id = transaction_id.create_payment_vals(trans_id=trans_id, authorize_partner=self, authorize_payment_type='credit_card')
                                    payment_id.action_post()
                                    transaction_id.write({
                                        'payment_id': payment_id.id,
                                        'is_post_processed': True
                                    })
                                if order_id.amount_total == order_id.payment_amount:
                                    order_id.action_confirm()
                                    _logger.info('Successfully created transaction with Transaction ID: %s', trans_id)
                            elif status_code == 4:
                                transaction_id._set_pending()
                            else:
                                error = resp.get('x_response_reason_text', "Authorize Transaction Error")
                                _logger.info(error)
                                transaction_id._set_error(state_message=error)
            elif self.authorize_payment_type == 'bank_account' and order_id:
                charge_data = {
                    'invoiceNumber': order_id.name[:19] + '/' if len(order_id.name) > 20 else order_id.name,
                    'description': order_id.note,
                    'amount': str(round(currency_amount, 2)),
                    'refId': self.merchant_id
                }
                for item in order_id.order_line:
                    if not item.product_id:
                        continue
                    itemId = item.product_id.default_code or str(item.product_id.id)
                    line_item = {
                        'lineItem': {
                            'itemId': itemId[:30] + '/' if len(itemId) > 31 else itemId,
                            'name': item.product_id.name[:30] + '/' if len(item.product_id.name) > 31 else item.product_id.name,
                            'description': item.name[:254] + '/'  if len(item.name) > 255 else item.name,
                            'quantity': str(item.product_uom_qty).replace('-', ''),
                            'unitPrice': str(item.price_unit).replace('-', ''),
                        },
                    }
                    charge_data.update({'line_items': line_item})
                charge_data.update({'shipping_address_id':order_id.partner_shipping_id})

                if self.is_wo_save_bank_acc:
                    billing_detail = self.partner_id.get_partner_billing_address(self.billing_partner_id)
                    # Create the payment data for a credit card
                    bank_details = {
                        'accountType': self.authorize_bank_type,
                        'routingNumber': self.routing_number,
                        'accountNumber': self.acc_number,
                        'nameOnAccount': self.acc_name,
                    }
                    charge_data.update({'billing': billing_detail.get('billing')})
                    authorize_api = AuthorizeAPI(self.acquirer_id)
                    resp = authorize_api.auth_and_capture_charge(charge_data=charge_data, bank_details=bank_details)
                else:
                    if self.payment_token_bank_id.acquirer_ref:
                        authorize_api = AuthorizeAPI(self.acquirer_id)
                        charge_data.update({
                            'customer_profile_id': str(self.customer_profile_id),
                            'paymentProfileId': self.payment_token_bank_id.acquirer_ref
                        })
                        resp = authorize_api.auth_and_capture_charge(charge_data=charge_data)            
                self.update({'acc_name': '', 'acc_number': '', 'routing_number': ''})

                payment_id = False
                if resp is not None:
                    trans_id = resp.get('x_trans_id')
                    status_code = int(resp.get('x_response_code', '0'))
                    transaction_vals.update({
                        'echeck_transaction': True,
                        'acquirer_reference': str(trans_id)
                    })
                    transaction_id = self.env['payment.transaction'].create(transaction_vals)
                    if trans_id and status_code and str(trans_id) != '0':
                        if status_code == 1:
                            transaction_id.write({
                                'state': 'done',
                                'last_state_change': fields.datetime.today(),
                                'state_message': resp.get('x_response_reason_text'),
                                'token_id': self.payment_token_bank_id.id
                            })
                            payment_id = transaction_id.create_payment_vals(trans_id=trans_id, authorize_partner=self, authorize_payment_type='bank_account')
                            if payment_id:
                                payment_id.action_post()
                                order_id.write({'payment_authorize': True,
                                                'authorize_bank': True})
                                order_id.action_confirm()
                            transaction_id.payment_id = payment_id.id if payment_id else False
                            transaction_id.is_post_processed = True
                        elif status_code == 4:
                            transaction_id._set_pending()
                        else:
                            error = resp.get('x_response_reason_text', "Authorize Transaction Error")
                            _logger.info(error)
                            transaction_id._set_error(state_message=error)
                    else:
                        transaction_id.update({
                            'state': 'error',
                            'state_message': 'Null Response.'
                        })

        except UserError as e:
            raise UserError(_(e.sudo().name))
        except ValidationError as e:
            raise ValidationError(e.sudo().args[0])
        except Exception as e:
            raise UserError(_("Authorize.NET Error! : %s !" % e))
