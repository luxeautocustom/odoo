# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging

from lxml import etree, html

from datetime import datetime
from .authorize_request import AuthorizeAPI
from odoo.addons.authorize_net.models import misc

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', copy=False)
    authorize_payment_type = fields.Selection([('credit_card', 'Credit Card'),
                                ('bank_account', 'eCheck.Net')], string='Authorize Transaction',
                                 copy=False, states={'draft': [('readonly', False)]}, readonly=True)
    transaction_type = fields.Selection([('authorize', 'Authorize'), ('capture', 'Capture'),
                        ('auth_capture', 'Authorize and Capture')], string='Transaction Type',
                        default='authorize', copy=False, states={'draft': [('readonly', False)]}, readonly=True)
    merchant_id = fields.Char(string='Merchant', readonly=True, copy=False)
    customer_profile_id = fields.Char(string='Customer Profile ID', size=64, readonly=True, copy=False)
    shipping_address_id = fields.Char(string='Shipping ID', size=64, readonly=True, copy=False)
    payment_token_id = fields.Many2one('payment.token', string='Credit Card or Account',
                        domain="[('partner_id', '=', partner_id), '|', ('company_id', '=', False), \
                            ('company_id', '=', company_id), ('authorize_payment_method_type', '=', authorize_payment_type)]",
                            copy=False, states={'draft': [('readonly', False)]}, readonly=True)
    transaction_id = fields.Char('Transaction ID', copy=False,
                        states={'draft': [('readonly', False)]}, readonly=True)
    payment_authorize = fields.Boolean('Payment via Authorize.Net', copy=False)
    is_refund_ref = fields.Boolean('Is Refund Reference', copy=False)
    auth_invoice_refund_ids = fields.Many2many('authorize.invoice.refund',
                                string="Transaction", ondelete='cascade', copy=False)
    # without save card
    is_wo_save_card = fields.Boolean('Direct Payment(Without Save Card)', default=False, copy=False)
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
    billing_partner_id = fields.Many2one('res.partner', 'Billing Partner')

    def _create_transaction(self, trans_id, invoice_id, acquirer=False):
        acquirer_id = acquirer if acquirer else self.acquirer_id
        values = {
            'partner_id': self.partner_id.id,
            'acquirer_id': acquirer_id and acquirer_id.id,
            'acquirer_reference': str(trans_id),
            'amount': self.amount,
            'transaction_type': 'debit',
            'currency_id': self.currency_id.id,
            'invoice_ids': [(6, 0, [invoice_id.id])],
            'company_id': acquirer_id and acquirer_id.company_id and acquirer_id.company_id.id,
            'operation': 'online_direct'
        }
        transaction_id = self.env['payment.transaction'].create(values)
        return transaction_id

    def action_post(self):
        ''' Add code for post payment with authorized .net payment. '''
        context = dict(self.env.context or {})
        if context.get('is_register_pay') and self.filtered(lambda p: p.journal_id.authorize_cc and p.payment_token_id):
            self.filtered(lambda p: p.payment_authorize and p.payment_token_id).sudo().post_payment_authorize()
            payments_trans_done = self.filtered(lambda pay: pay.payment_transaction_id and pay.payment_transaction_id.state == 'done')
            return super(AccountPayment, payments_trans_done).action_post()
        return super(AccountPayment, self).action_post()

    def _prepare_payment_transaction_vals(self, **extra_create_values):
        super()._prepare_payment_transaction_vals(**extra_create_values)
        self.ensure_one()
        transaction_ref = self.env['payment.transaction'].search([('reference', '=', self.ref)])
        new_ref = transaction_ref._compute_reference(self.payment_token_id.acquirer_id.provider, prefix=self.ref)
        return {
            'acquirer_id': self.payment_token_id.acquirer_id.id,
            'reference': self.ref if not transaction_ref else new_ref,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'token_id': self.payment_token_id.id,
            'operation': 'offline',
            'payment_id': self.id,
            **extra_create_values,
        }

    def post_payment_authorize(self):
        """Customer Register Payment"""
        context = dict(self.env.context or {})
        if context.get('active_id') and context.get('active_model') == 'account.move':
            for rec in self:
                invoice_id = self.env['account.move'].browse(context['active_id'])
                resp = {}
                # Credit Authorize Invoice Payment
                if rec.acquirer_id and invoice_id and \
                        invoice_id.move_type in ['out_invoice', 'in_invoice']:
                    if not rec.acquirer_id:
                        raise ValidationError(_('Please configure your Authorize.Net account.'))
                    if not rec.journal_id and not rec.acquirer_id.journal_id:
                        raise ValidationError(_("Please configure Authorize payment journal."))
                    # Convert Currency Amount
                    from_currency_id = rec.currency_id or rec.company_id.currency_id
                    to_currency_id = rec.acquirer_id.journal_id.currency_id or rec.acquirer_id.journal_id.company_id.currency_id
                    currency_amount = rec.amount
                    if from_currency_id and to_currency_id and from_currency_id != to_currency_id:
                        currency_amount = from_currency_id._convert(rec.amount, to_currency_id, rec.acquirer_id.journal_id.company_id, fields.Date.today())
                    if not invoice_id.name and invoice_id.invoice_line_ids:
                        raise ValidationError(_("Require fields:: Invoice Number or product of Invoice"))
                    try:
                        charge_data = {
                            'invoiceNumber': invoice_id.name[:19] + '/' if len(invoice_id.name) > 20 else invoice_id.name,
                            'description': invoice_id.narration,
                            'amount': str(round(currency_amount, 2)),
                            'refId': str(rec.merchant_id)
                        }
                        for item in invoice_id.invoice_line_ids:
                            itemId = ''
                            if item.product_id and item.product_id.default_code and len(item.product_id.default_code) > 31:
                                itemId = item.product_id.default_code[:30] + '/'
                            elif item.product_id and item.product_id.default_code and len(item.product_id.default_code) < 31:
                                itemId = item.product_id.default_code
                            else:
                                itemId = ''
                            line_item = {
                                'lineItem': {
                                    'itemId': itemId,
                                    'name': item.product_id.name[:30] + '/' if len(item.product_id.name) > 31 else item.product_id.name,
                                    'description': item.name[:254] + '/'  if len(item.name) > 255 else item.name,
                                    'quantity': str(item.quantity).replace('-', ''),
                                    'unitPrice': str(item.price_unit).replace('-', ''),
                                },
                            }
                            charge_data.update({'line_items': line_item})
                        charge_data.update({'shipping_address_id':invoice_id.partner_shipping_id})
                        if rec.is_wo_save_card:
                            expiry_date = rec.cc_year + '-' + rec.cc_month
                            if datetime.now().strftime('%Y%m') > datetime.strptime(expiry_date, '%Y-%m').strftime('%Y%m'):
                                raise ValidationError(_("Expiration date not valid."))
                            billing_detail = rec.partner_id.get_partner_billing_address(rec.billing_partner_id)
                            # Create the payment data for a credit card
                            card_details = {
                                'card_number': str(rec.cc_number),
                                'expiry_date': expiry_date,
                                'card_code': rec.cc_cvv
                            }
                            charge_data.update({'billing': billing_detail.get('billing')})
                            authorize_api = AuthorizeAPI(rec.acquirer_id)
                            resp = authorize_api.auth_and_capture_charge(charge_data=charge_data, card_details=card_details)

                        elif rec.payment_token_id and rec.payment_token_id.acquirer_ref and rec.payment_token_id.acquirer_ref != 'dummy':
                            authorize_api = AuthorizeAPI(rec.acquirer_id)
                            charge_data.update({
                                'customer_profile_id': str(rec.customer_profile_id),
                                'paymentProfileId': rec.payment_token_id.acquirer_ref
                            })
                            resp = authorize_api.auth_and_capture_charge(charge_data=charge_data)

                        trans_id = resp.get('x_trans_id')
                        status_code = int(resp.get('x_response_code', '0'))
                        if trans_id and status_code:
                            transaction_id = rec._create_transaction(trans_id=trans_id, invoice_id=invoice_id)
                            if status_code == 1:
                                transaction_id.write({
                                    'state': 'done',
                                    'last_state_change': fields.datetime.today(),
                                    'state_message': resp.get('x_response_reason_text')
                                })
                                if not rec.is_wo_save_card:
                                    transaction_id.token_id = rec.payment_token_id.id
                                invoice_id.write({'transaction_ids': [(4, transaction_id.id)]})
                                rec.update({
                                    'payment_transaction_id': transaction_id.id,
                                    'company_id': rec.company_id.id,
                                    'transaction_id': trans_id or '',
                                    'authorize_payment_type': 'credit_card',
                                    'transaction_type': 'auth_capture',
                                })
                                transaction_id.write({
                                    'payment_id': rec.id,
                                    'is_post_processed': True
                                })
                            elif status_code == 4:
                                transaction_id._set_pending()
                            else:
                                error = resp.get('x_response_reason_text', "Authorize Transaction Error")
                                _logger.info(error)
                                transaction_id._set_error(state_message=error)

                    except UserError as e:
                        raise UserError(_(e.name))
                    except ValidationError as e:
                        raise ValidationError(e.args[0])
                    except Exception as e:
                        raise UserError(_("Authorize.NET Error! : %s !" % e))
                # Refund Authorize Invoice Payment
                elif invoice_id and invoice_id.move_type in ['out_refund', 'in_refund']:
                    self.ensure_one()
                    try:
                        charge_data = {}
                        count = 0
                        for record in rec.auth_invoice_refund_ids:
                            count += 1
                            # Convert Currency Amount
                            from_currency_id = record.currency_id
                            to_currency_id = record.acquirer_id.journal_id.currency_id or record.acquirer_id.journal_id.company_id.currency_id
                            currency_amount = record.refund_amount
                            if from_currency_id and to_currency_id and from_currency_id != to_currency_id:
                                currency_amount = from_currency_id._convert(record.refund_amount, to_currency_id, record.acquirer_id.journal_id.company_id, fields.Date.today())
                            card_number = record.payment_transaction_id.get_payment_transaction_details()
                            if record.credit_amount and record.refund_amount and record.transaction_id \
                                and card_number and record.partner_id:
                                charge_data.update({
                                    'amount': str(round(currency_amount, 2)),
                                    'refId': str(record.customer_profile_id),
                                    'trans_id': str(record.transaction_id),
                                    'cc_number': str(card_number),
                                    'expiry_date': 'XXXX',
                                    'invoiceNumber': invoice_id.name[:19] + '/' if len(invoice_id.name) > 20 else invoice_id.name,
                                    'description': invoice_id.narration,
                                })

                                authorize_api = AuthorizeAPI(record.acquirer_id)
                                resp = authorize_api.refund_transaction(charge_data=charge_data)
                                if resp is not {}:
                                    refund_tran_id = resp.get('x_trans_id')
                                    status_code = int(resp.get('x_response_code', '0'))
                                    transaction_id = self._create_transaction(trans_id=refund_tran_id, invoice_id=invoice_id, acquirer=record.acquirer_id)
                                    if refund_tran_id and status_code:
                                        if record.payment_token_id:
                                            transaction_id.token_id = record.payment_token_id.id
                                        transaction_id.write({
                                            'transaction_type': 'credit',
                                            'amount': record.refund_amount,
                                            'currency_id': record.currency_id.id
                                        })
                                        if status_code == 1:
                                            transaction_id.write({
                                                'state': 'done',
                                                'last_state_change': fields.datetime.today(),
                                                'state_message': resp.get('x_response_reason_text')
                                            })
                                            if invoice_id and transaction_id:
                                                invoice_id.write({'transaction_ids': [(4, transaction_id.id)]})
                                                record.payment_transaction_id.refund_amount += round(currency_amount, 2)
                                                if count > 1:
                                                    payment_id = transaction_id.create_payment_vals(trans_id=str(refund_tran_id),
                                                                                    authorize_partner=record, authorize_payment_type='credit_card')
                                                    payment_id.action_post()
                                                    if transaction_id.invoice_ids:
                                                        transaction_id.invoice_ids.filtered(lambda move: move.state == 'draft')._post()

                                                        (payment_id.line_ids + transaction_id.invoice_ids.line_ids)\
                                                            .filtered(lambda line: line.account_id == payment_id.destination_account_id and not line.reconciled)\
                                                            .reconcile()
                                                    transaction_id.reference = self.env['payment.transaction']._compute_reference(prefix=invoice_id.name)
                                                    transaction_id.payment_id = payment_id.id if payment_id else False
                                                    transaction_id.is_post_processed = True
                                                else:
                                                    rec.update({
                                                        'amount': record.refund_amount,
                                                        'currency_id': record.currency_id.id,
                                                        'company_id': rec.company_id.id,
                                                        'transaction_id': refund_tran_id,
                                                        'authorize_payment_type': 'credit_card',
                                                        'merchant_id': record.merchant_id,
                                                        'customer_profile_id': record.customer_profile_id or '',
                                                        'payment_transaction_id': transaction_id.id,
                                                        'payment_token_id': transaction_id.token_id and transaction_id.token_id.id or None,
                                                    })
                                                    transaction_id.payment_id = rec.id
                                                    transaction_id.is_post_processed = True
                                            _logger.info('Successfully created transaction with Transaction ID: %s', refund_tran_id)
                                        elif status_code == 4:
                                            transaction_id._set_pending()
                                        else:
                                            error = resp.get('x_response_reason_text', "Authorize Transaction Error")
                                            _logger.info(error)
                                            transaction_id._set_error(msg=error)
                    except UserError as e:
                        raise UserError(_(e.name))
                    except ValidationError as e:
                        raise ValidationError(e.args[0])
                    except Exception as e:
                        raise UserError(_("Authorize.NET Error! : %s !" % e))
                rec.update({
                    'cc_number': '',
                    'cc_cvv': '',
                    'cc_type': '',
                    'cc_year': '',
                    'cc_month': ''
                })
        return True
