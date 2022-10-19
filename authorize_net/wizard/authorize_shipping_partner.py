# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models


class AuthorizeShippingPartner(models.TransientModel):
    _name = "authorize.shipping.partner"
    _description = "Authorize Shipping Partner"

    @api.model
    def default_get(self, fields):
        res = super(AuthorizeShippingPartner, self).default_get(fields)
        if self._context.get('active_id') and self._context.get('active_model') == 'res.partner':
            res['partner_id'] = self._context['active_id']
        if self._context.get('active_id') and self._context.get('active_model') == 'res.partner.authorize':
            res['authorize_partner_id'] = self._context['active_id']
        return res

    def _get_shipping_partner_domain(self):
        domain = [('type', '=', 'delivery')]
        if self._context.get('active_id') and self._context.get('active_model') == 'res.partner':
            domain.append(('parent_id', '=', self._context['active_id']))
        return domain

    partner_id = fields.Many2one('res.partner', 'Partner')
    authorize_partner_id = fields.Many2one('res.partner.authorize', 'Authorize Partner')
    shipping_partner_id = fields.Many2one('res.partner', 'Shipping Partner', domain=_get_shipping_partner_domain)

    def add_shipping_authorize_cust(self):
        self.ensure_one()
        if self.partner_id:
            self.partner_id.authorize_customer_create(self.shipping_partner_id)
        if self.authorize_partner_id:
            self.authorize_partner_id.update_authorize(self.shipping_partner_id)
