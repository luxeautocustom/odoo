# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"

    pw_payment_status = fields.Selection([
        ('fully_paid', 'Fully Paid'),
        ('not_paid', 'Not Paid'),
        ('no_invoice', 'No Invoice'),
        ('partial_paid', 'Partially Paid')], 'Payment Status', compute="_compute_pw_payment_status", store=True)
    amount_due = fields.Float(string="Amount Due", compute="_compute_pw_payment_status",  store=True)

    @api.depends('invoice_ids.amount_residual', 'order_line.qty_invoiced')
    def _compute_pw_payment_status(self):
        for order in self:
            if order.invoice_ids:
                if all([invoice.payment_state in ("paid", "in_payment") for invoice in order.invoice_ids]):
                    order.pw_payment_status = "fully_paid"
                    order.amount_due = sum(order.invoice_ids.mapped('amount_residual'))
                elif all([invoice.payment_state == "not_paid" for invoice in order.invoice_ids]):
                     order.pw_payment_status = "not_paid"
                     order.amount_due = sum(order.invoice_ids.mapped('amount_residual'))            
                elif any([invoice.payment_state == "partial" for invoice in order.invoice_ids]):
                    order.pw_payment_status = "partial_paid"
                    order.amount_due = sum(order.invoice_ids.mapped('amount_residual'))
            else:
                order.pw_payment_status = "no_invoice"
