# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_payment_tx_count(self):
        for invoice in self:
            invoice.payment_tx_count = len(invoice.transaction_ids)

    payment_tx_count = fields.Integer(string="Number of payment transactions", \
                        compute='_compute_payment_tx_count')

    def payment_action_capture(self):
        self.authorized_transaction_ids.action_capture()
        self.authorized_transaction_ids._cron_finalize_post_processing()

    def action_view_transactions(self):
        action = {
            'name': _('Payment Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'target': 'current',
        }
        if len(self.transaction_ids) == 1:
            action['res_id'] = self.transaction_ids[0].id
            action['view_mode'] = 'form'
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', self.transaction_ids.ids)]
        return action
