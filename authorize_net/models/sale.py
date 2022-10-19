# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('transaction_ids')
    def _compute_authorized_transaction_ids(self):
        for trans in self:
            trans.authorized_transaction_ids = trans.transaction_ids.filtered(lambda t: t.state == 'authorized' and t.provider != 'authorize')

    def _compute_payment_tx_count(self):
        for record in self:
            record.payment_tx_count = len(record.transaction_ids)

    @api.depends('transaction_ids', 'transaction_ids.amount', 'transaction_ids.state')
    def _compute_payment_amount(self):
        for record in self:
            debit_amount = sum(record.transaction_ids.filtered(lambda tx: tx.transaction_type != 'credit' and tx.provider == 'authorize' and tx.state in ['done', 'authorized']).mapped('amount'))
            void_amount = sum(record.transaction_ids.filtered(lambda tx: tx.transaction_type == 'credit' and tx.provider == 'authorize' and tx.state == 'cancel').mapped('amount'))
            record.payment_amount = debit_amount - void_amount

    @api.depends('partner_id', 'partner_id.authorize_partner_ids', 'partner_id.payment_token_ids')
    def _compute_is_customer_link(self):
        for record in self:
            record.is_customer_link = False
            if (record.partner_id and record.partner_id.authorize_partner_ids and\
                record.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id.id == self.env.company.id)) \
                or (record.partner_id.payment_token_ids.filtered(lambda x: x.company_id.id == self.env.company.id \
                    and x.acquirer_ref and x.acquirer_id.provider == 'authorize')):
                record.is_customer_link = True

    payment_authorize = fields.Boolean('Payment Thru Authorize', default=False, copy=False)
    authorize_cc = fields.Boolean('Authorize CCD', copy=False)
    authorize_bank = fields.Boolean('Authorize Bank A/C', copy=False)
    payment_amount = fields.Monetary('Outstanding credits', compute="_compute_payment_amount", store=True, copy=False)
    payment_tx_count = fields.Integer(string="Number of payment transactions", compute='_compute_payment_tx_count')
    is_customer_link = fields.Boolean('Link Customer', compute="_compute_is_customer_link", store=True)

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

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.transaction_ids:
            transaction_ids = self.transaction_ids.filtered(lambda x: x.transaction_type != 'credit')
            invoice_vals.update({'transaction_ids': [(6, 0, transaction_ids.ids)]})
        return invoice_vals
