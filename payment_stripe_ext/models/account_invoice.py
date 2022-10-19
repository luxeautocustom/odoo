# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from werkzeug import urls
from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    portal_payment_options = fields.Text(string='Portal Payment Options', readonly=True)
    stripe_payment_url = fields.Char(string='Stripe Payment Link')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.render_stripe_payment_block_backend()
        return res

    def render_stripe_payment_block_backend(self):
        payment_acquirer = self.env['payment.acquirer']
        # base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for invoice in self:
            stripe_payment_url = invoice.with_context(force_website=True).get_access_action().get('url', False)
            invoice.stripe_payment_url = stripe_payment_url
            invoice.portal_payment_options = payment_acquirer.with_context({'call_backend': True}).render_payment_block(
                invoice.name, invoice.amount_residual, invoice.currency_id.id,
                partner_id=invoice.partner_id.id, company_id=invoice.company_id.id)


class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    def reconcile(self):
        rec = super(AccountMoveLines, self).reconcile()
        move_ids = self.mapped('move_id')
        if move_ids and move_ids.filtered(lambda x: x.move_type in ['out_invoice', 'in_invoice']):
            invoice_id = move_ids.filtered(lambda x: x.move_type in ['out_invoice', 'in_invoice'])
            invoice_id.render_stripe_payment_block_backend()
        return rec
