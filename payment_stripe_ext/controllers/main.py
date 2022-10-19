# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import logging
import werkzeug
import pprint

from odoo import http, tools, _
from odoo.http import request

from odoo.addons.payment_stripe.controllers.main import StripeController
from odoo.addons.payment.controllers.portal import PaymentPostProcessing

_logger = logging.getLogger(__name__)

def _get_invoice_id(tx):
    invoice = False
    reference = tx.reference.split('-')
    if 'x' in tx.reference:
        reference = tx.reference.split('x')
    if reference:
        invoice = request.env['account.move'].sudo().search([('name', '=', reference[0])], limit=1)
    return invoice


class StripeBackendController(StripeController):

    @http.route(['/payment/stripe/checkout_return'], type='http', auth='public')
    def stripe_return_from_checkout(self, **data):
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_feedback_data(
            'stripe', data
        )
        acquirer_sudo = tx_sudo.acquirer_id
        # Fetch the PaymentIntent, Charge and PaymentMethod objects from Stripe
        payment_intent = acquirer_sudo._stripe_make_request(
            f'payment_intents/{tx_sudo.stripe_payment_intent}', method='GET'
        )
        self._include_payment_intent_in_feedback_data(payment_intent, data)

        # Handle the feedback data crafted with Stripe API objects
        request.env['payment.transaction'].sudo()._handle_feedback_data('stripe', data)
        tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', data.get('reference'))], limit=1)
        if tx_sudo and tx_sudo.state == 'done' and request.session.get('from_backend'):
            invoice = _get_invoice_id(tx=tx_sudo)
            if invoice and invoice.state == 'posted' and tx_sudo.acquirer_id and tx_sudo.acquirer_id.provider == 'stripe' and tx_sudo.acquirer_id.journal_id:
                tx_sudo.sudo()._cron_finalize_post_processing()
                action = request.env.ref('account.action_move_out_invoice_type')
                menu = request.env.ref('account.menu_finance')
                invoice_url = '/web?#id=%s&action=%s&model=account.move&view_type=form&cids=1&menu_id=%s' % (invoice[0].id, action.id, menu.id)
                request.session.pop('from_backend', False)
                return werkzeug.utils.redirect(invoice_url)
        return werkzeug.utils.redirect('/payment/status')


class PaymentStripe(http.Controller):

    @http.route(['/payment_stripe/transaction'], type='json', auth="public", website=True)
    def transaction(self, reference, amount, currency_id, acquirer_id, partner=None):
        if partner:
            partner_id = int(partner)
        else:
            partner_id = request.env.user.partner_id.id if request.env.user.partner_id != request.website.partner_id else False
        acquirer = request.env['payment.acquirer'].browse(int(acquirer_id))
        invoice = request.env['account.move'].search([('name','=', reference)], limit=1)
        reference_values = invoice and {'invoice_ids': [(4, invoice)]} or {}
        reference = request.env['payment.transaction']._compute_reference(provider=acquirer, prefix=invoice.name, values=reference_values)
        values = {
            'acquirer_id': int(acquirer_id),
            'reference': reference,
            'amount': float(amount),
            'currency_id': int(currency_id),
            'partner_id': partner_id,
            'operation': 'online_redirect'
            #'type': 'online_redirect' if acquirer.allow_tokenization != 'none' and partner_id else 'form',
        }
        tx = request.env['payment.transaction'].sudo().create(values)
        invoice = _get_invoice_id(tx=tx)
        tx.update({'invoice_ids': [(6, 0, [invoice.id])]})
        PaymentPostProcessing.monitor_transactions(tx)
        request.session['from_backend'] = True
        return tx.render_stripe_button(invoice)
