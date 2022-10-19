# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models


class PaymentTransactionStripe(models.Model):
    _inherit = 'payment.transaction'

    def render_stripe_button(self, invoice):
        values = {
            'partner_id': invoice.partner_id.id,
        }
        return self.acquirer_id.sudo().render(
            self.reference,
            invoice.amount_residual_signed,
            invoice.currency_id.id,
            values=values,
        )
