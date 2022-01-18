# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.order_line:
            section_lst = []
            for each in res.order_line:
                if each.product_id.section_id and each.product_id.section_id not in section_lst:
                    section_lst.append(each.product_id.section_id)
            if section_lst:
                sequence = 10
                for sec in section_lst:
                    order_lines = res.order_line.filtered(lambda l:l.product_id.section_id == sec)
                    section_line = res.order_line.filtered(lambda l:l.name == sec.name and l.display_type == 'line_section')
                    if not section_line:
                        section_line = self.env['sale.order.line'].create({
                            'display_type': 'line_section',
                            'name': sec.name,
                            'order_id': res.id
                        })
                    section_line.sequence = sequence
                    sequence = sequence + 1
                    for each in order_lines:
                        each.sequence = sequence
                        sequence = sequence + 1
                order_line = res.order_line.filtered(lambda l: not l.product_id.section_id and not l.display_type)
                if order_line:
                    for line in order_line:
                        line.sequence = sequence
                        sequence = sequence + 1
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('order_line'):
            if self.order_line:
                section_lst = []
                for each in self.order_line:
                    if each.product_id.section_id and each.product_id.section_id not in section_lst:
                        section_lst.append(each.product_id.section_id)
                if section_lst:
                    sequence = 10
                    for sec in section_lst:
                        order_lines = self.order_line.filtered(lambda l: l.product_id.section_id == sec)
                        section_line = self.order_line.filtered(
                            lambda l: l.name == sec.name and l.display_type == 'line_section')
                        if not section_line:
                            section_line = self.env['sale.order.line'].create({
                                'display_type': 'line_section',
                                'name': sec.name,
                                'order_id': self.id
                            })
                        section_line.sequence = sequence
                        sequence = sequence + 1
                        for each in order_lines:
                            each.sequence = sequence
                            sequence = sequence + 1
                    order_line = self.order_line.filtered(lambda l: not l.product_id.section_id and not l.display_type)
                    if order_line:
                        for line in order_line:
                            line.sequence = sequence
                            sequence = sequence + 1
        return res