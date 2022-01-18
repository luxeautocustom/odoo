# -*- coding: utf-8 -*-

from odoo import api, models, fields,_


class ProductProduct(models.Model):
    _inherit = 'product.product'

    section_id = fields.Many2one('sale.order.section', string="Sale Order Section")


class SaleOrderSection(models.Model):
    _name = 'sale.order.section'
    _description = 'Sale Order Section'

    name = fields.Char(string="Name")