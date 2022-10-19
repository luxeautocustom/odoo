# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
import pprint

from .authorize_request import AuthorizeAPI
from odoo import fields, models, api, _
from odoo.addons.authorize_net.models import misc

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    transaction_type = fields.Selection([
        ('debit', 'Debit'),
        ('credit', 'Credit')], 'Transaction Type', copy=False)
    refund_amount = fields.Monetary(string="Refund Amount", copy=False)
    echeck_transaction = fields.Boolean(help='Technical field for check is echeck transaction or not?', copy=False)
    company_id = fields.Many2one('res.company', related='acquirer_id.company_id',
            string='Company', index=True, copy=False)

    def _send_capture_request(self):
        self.ensure_one()
        transaction = AuthorizeAPI(self.acquirer_id)
        # Convert Currency Amount
        from_currency_id = self.currency_id or self.company_id.currency_id
        to_currency_id = self.acquirer_id.journal_id.currency_id or self.acquirer_id.journal_id.company_id.currency_id
        currency_amount = self.amount
        if from_currency_id and to_currency_id and from_currency_id != to_currency_id:
            currency_amount = from_currency_id._convert(self.amount, to_currency_id, self.acquirer_id.journal_id.company_id, fields.Date.today())
            tree = transaction.capture(self.acquirer_reference or '', round(currency_amount, 2))
        else:
            tree = transaction.capture(self.acquirer_reference or '', self.amount)
        feedback_data = {'reference': self.reference, 'response': tree}
        return self._handle_feedback_data('authorize', feedback_data)

    def get_payment_transaction_details(self):
        self.ensure_one()
        if self.acquirer_reference and self.acquirer_id:
            transaction = AuthorizeAPI(self.acquirer_id)
            resp = transaction.get_transaction_details(self.acquirer_reference)
            resp.update(resultCode=resp.get('messages').get('resultCode'))
            if resp.get('transaction', {}).get('payment', {}).get('creditCard', False):
                resp.update(x_cardNumber=resp.get('transaction', {}).get('payment', {}).get('creditCard', {}).get('cardNumber', False))
            else:
                resp.update(x_cardNumber=resp.get('transaction', {}).get('payment', {}).get('bankAccount', {}).get('accountNumber', False))
            if resp.get('resultCode') == 'Ok' and resp.get('x_cardNumber'):
                return resp['x_cardNumber'][4:]
            return False

    def create_payment_vals(self, trans_id, authorize_partner, authorize_payment_type):
        self.ensure_one()
        payment_vals = {
            'amount': self.amount,
            'payment_type': 'inbound' if self.transaction_type == 'debit' else 'outbound',
            'partner_type': 'customer',
            'date': fields.Date.today(),
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'transaction_id': trans_id,
            'journal_id': self.acquirer_id.journal_id.id,
            'company_id': self.acquirer_id.company_id.id,
            'payment_token_id': self.token_id and self.token_id.id or None,
            'payment_transaction_id': self.id,
            'ref': self.reference,
            'customer_profile_id': authorize_partner.customer_profile_id,
            'merchant_id': authorize_partner.merchant_id,
            'authorize_payment_type': authorize_payment_type,
            'transaction_type': 'auth_capture'
        }
        payment_id = self.env['account.payment'].sudo().create(payment_vals)
        return payment_id

    def _process_feedback_data(self, data):
        super(PaymentTransaction, self)._process_feedback_data(data=data)
        self = self.sudo()
        
        response_content = data.get('response')
        if response_content and self.state == 'done' and not self.payment_id:
            self._cron_finalize_post_processing()
        if response_content and self.state == 'done' and self.payment_id:
            self.transaction_type = 'debit'
            if self.token_id and self.token_id.customer_profile_id:
                self.payment_id.customer_profile_id = self.token_id.customer_profile_id
            if not self.echeck_transaction and not self.payment_id.authorize_payment_type:
                self.payment_id.authorize_payment_type = 'credit_card'
        return response_content

    def prepare_token_values(self, partner, payment_profile, payment, authorize_API):
        card_details = payment.get('creditCard', False)
        bank_details = payment.get('bankAccount', False)
        token_vals = {}
        if card_details:
            token_vals.update(
                acquirer_id=self.acquirer_id.id,
                name=str(misc.masknumber(card_details.get('cardNumber'))) or str(misc.masknumber(card_details.get('name'))),
                credit_card_no=str(misc.masknumber(card_details.get('cardNumber'))) or str(misc.masknumber(card_details.get('name'))),
                credit_card_type=card_details.get('cardType').lower(),
                credit_card_code='XXX',
                credit_card_expiration_month='xx',
                credit_card_expiration_year='XXXX',
                partner_id=self.partner_id.id,
                acquirer_ref=payment_profile,
                authorize_profile=partner,
                customer_profile_id=partner,
                authorize_payment_method_type=self.acquirer_id.authorize_payment_method_type,
                verified=True,
            )
        else:
            bank_details = authorize_API.get_customer_payment_profile(partner, payment_profile).get('paymentProfile', {}).get('payment', {}).get('bankAccount', {})
            token_vals.update(
                acquirer_id=self.acquirer_id.id,
                name=str(misc.mask_account_number(bank_details.get('accountNumber'))),
                acc_number=str(misc.mask_account_number(bank_details.get('accountNumber'))),
                owner_name=bank_details.get('nameOnAccount'),
                routing_number=str(misc.mask_account_number(bank_details.get('routingNumber'))),
                authorize_bank_type=bank_details.get('accountType'),
                partner_id=self.partner_id.id,
                acquirer_ref=payment_profile,
                authorize_profile=partner,
                customer_profile_id=partner,
                authorize_payment_method_type=self.acquirer_id.authorize_payment_method_type,
                verified=True,
            )
        return token_vals

    def _authorize_tokenize(self):
        """ Create a token for the current transaction.

        Note: self.ensure_one()

        :return: None
        """
        self.ensure_one()
        token = False
        customer_profile_ids = False
        company_id = self.env.company
        provider_id = self.acquirer_id
        merchant_id = self.partner_id._get_customer_id('CUST')
        if not provider_id or provider_id.authorize_login == 'dummy':
            raise ValidationError(_('Please configure your Authorize.Net account'))

        authorize_API = AuthorizeAPI(self.acquirer_id)
        if not self.partner_id.authorize_partner_ids:
            cust_profile = authorize_API.create_customer_profile(
                self.partner_id, self.acquirer_reference,merchant_id
            )
            if cust_profile.get('profile_id') and cust_profile.get('shipping_address_id'):
                    customer_profile_id = self.env['res.partner.authorize'].create({
                        'customer_profile_id': cust_profile['profile_id'],
                        'shipping_address_id': cust_profile['shipping_address_id'],
                        'partner_id': self.partner_id.id,
                        'company_id': company_id.id,
                        'merchant_id': merchant_id,
                        'acquirer_id': provider_id.id,
                    })
            token_vals = self.prepare_token_values(customer_profile_id.customer_profile_id, 
                            cust_profile.get('payment_profile_id'), 
                            cust_profile.get('payment'),
                            authorize_API)
        else:
            transaction = authorize_API.get_transaction_details(self.acquirer_reference).get('transaction', {})
            payment = transaction.get('payment', {})
            payment_profile = transaction.get('profile', {}).get('customerPaymentProfileId', False)
            token_vals = self.prepare_token_values(self.partner_id.authorize_partner_ids[0].customer_profile_id, 
                            payment_profile, 
                            payment,
                            authorize_API)

        token = self.env['payment.token'].create(token_vals)
        
        self.write({
            'token_id': token.id,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %s for partner with id %s", token.id, self.partner_id.id
        )
