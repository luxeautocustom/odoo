# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import time
import random
import logging

from .authorize_request import AuthorizeAPI

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

def _partner_split_name(partner_name):
    return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]


class ResPartnerAuthorize(models.Model):
    _name = "res.partner.authorize"
    _description = "Authorize Customer"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Customer')
    customer_profile_id = fields.Char('Customer Profile ID', size=64, copy=False)
    shipping_address_id = fields.Char('Shipping ID', size=64, copy=False)
    merchant_id = fields.Char('Customer ID', copy=False)
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', required=True)
    company_id = fields.Many2one('res.company', related='acquirer_id.company_id', string='Company', index=True, copy=False)

    def update_authorize(self, shipping_address_id=None):
        self.ensure_one()
        company_id = self.env.company
        shipping_address = self.partner_id.get_partner_shipping_address(shipping_address_id)
        if not self.acquirer_id:
            raise ValidationError(_('Please configure your Authorize.Net account'))
        if self.customer_profile_id and self.merchant_id and self.partner_id.email:
            try:
                authorize_api = AuthorizeAPI(self.acquirer_id)
                resp = authorize_api.update_customer_profile(partner=self)
                if resp.get('result_code') == "Ok":
                    address_resp = authorize_api.update_customer_profile_shipping_address(partner=self, shipping=shipping_address.get('shipping'))
                    if address_resp.get('result_code') == "Ok":
                        _logger.info('Successfully updated shipping address')
            except UserError as e:
                raise UserError(_(e.name))
            except ValidationError as e:
                raise ValidationError(e.args[0])
            except Exception as e:
                raise UserError(_("Authorize.NET Error! : %s !" % e))
            return True
        else:
            raise ValidationError(_("To Update a Customer Profile merchant, email is required of customer: "))

    def unlink_authorize(self):
        self.ensure_one()
        if not self.acquirer_id:
            raise ValidationError(_('Please configure your Authorize.Net account'))
        if not self.user_has_groups('account.group_account_manager'):
            raise UserError(_("You cannot delete this record."))
        if self.customer_profile_id:
            try:
                authorize_api = AuthorizeAPI(self.acquirer_id)
                domain = [('partner_id', '=', self.partner_id.id),
                          ('company_id', '=', self.company_id.id),
                          ('customer_profile_id', '=', self.customer_profile_id)]
                # bank_ids = self.env['res.partner.bank'].search(domain).unlink()
                token_ids = self.env['payment.token'].search(domain).unlink()
                resp = authorize_api.unlink_customer_profile(partner=self)
                if resp.get('result_code') == "Ok":
                    self.unlink()
            except UserError as e:
                raise UserError(_(e.name))
            except ValidationError as e:
                raise ValidationError(e.args[0])
            except Exception as e:
                raise UserError(_("Authorize.NET Error! : %s !" % e))
        return True


class ResPartner(models.Model):
    _inherit = "res.partner"

    authorize_partner_ids = fields.One2many('res.partner.authorize', 'partner_id', string='Authorize Customer', copy=False)
    email = fields.Char('Email', size=240, copy=False)
    payment_token_ids = fields.One2many('payment.token', 'partner_id', 'Payment Tokens', domain=[('authorize_payment_method_type','=','credit_card')])
    bank_payment_token_ids = fields.One2many('payment.token', 'partner_ref_id', 'Payment Tokens', domain=[('authorize_payment_method_type','=','bank_account')])

    def _get_customer_id(self, country):
        return "".join([country, time.strftime('%y%m%d'), str(random.randint(0, 10000)).zfill(5)]).strip()

    @api.model
    def create(self, values):
        context = dict(self.env.context or {})
        context.update({'authorize': True})
        self.env.context = context
        return super(ResPartner, self).create(values)

    def write(self, values):
        context = dict(self.env.context or {})
        context.update({'authorize': True})
        self.env.context = context
        return super(ResPartner,self).write(values)

    def get_authorize_number_format(self):
        self.ensure_one()
        res = {'phone_number': False, 'fax_number': False}
        if self.phone:
            phone_no = self.phone.replace('+', '')
            res.update({'phone_number': phone_no.replace(' ', '-')})
        return res

    def get_partner_shipping_address(self, shipping_address_id=None):
        self.ensure_one()
        context = dict(self.env.context or {})
        shipping = {}
        partner_shipping_id = self
        if shipping_address_id:
            partner_shipping_id = shipping_address_id
        if not context.get('from', False):
            shipping = partner_shipping_id.get_authorize_number_format()
        if partner_shipping_id and not partner_shipping_id.name:
            raise ValidationError(_("Please configure shipping address contact name"))
        shipping.update({
            'first_name': _partner_split_name(partner_shipping_id.name)[0],
            'last_name': _partner_split_name(partner_shipping_id.name)[1],
            'company': partner_shipping_id.parent_id.name or partner_shipping_id.name,
            'address': partner_shipping_id.street,
            'city': partner_shipping_id.city,
            'state': partner_shipping_id.state_id.code,
            'zip': partner_shipping_id.zip,
            'country': partner_shipping_id.country_id.code,
        })
        return {
            'shipping': shipping,
            'partner': partner_shipping_id,
        }

    def get_partner_billing_address(self, billing_partner_id=None):
        self.ensure_one()
        context = dict(self.env.context or {})
        billing = {}
        cus_type = 'individual'
        partner_invoice_id = self
        if billing_partner_id:
            partner_invoice_id = billing_partner_id
        if not context.get('from', False):
            billing = partner_invoice_id.get_authorize_number_format()
        if partner_invoice_id and not partner_invoice_id.name:
            raise ValidationError(_("Please configure billing address contact name"))
        billing.update({
            'first_name': _partner_split_name(partner_invoice_id.name)[0],
            'last_name': _partner_split_name(partner_invoice_id.name)[1],
            'company': partner_invoice_id.parent_id.name or partner_invoice_id.name,
            'address': partner_invoice_id.street,
            'city': partner_invoice_id.city,
            'state': partner_invoice_id.state_id.code,
            'zip': partner_invoice_id.zip,
            'country': partner_invoice_id.country_id.code,
        })
        return {
            'customer_type': cus_type,
            'billing': billing,
        }

    def authorize_customer_create(self, shipping_address_id=None):
        self.ensure_one()
        customer_profile_ids = False
        company_id = self.env.company
        provider_id = self.env['payment.acquirer']._get_authorize_provider()
        if not provider_id or provider_id.authorize_login == 'dummy':
            raise ValidationError(_('Please configure your Authorize.Net account'))
        merchant_id = self._get_customer_id('CUST')
        if self.authorize_partner_ids.filtered(lambda x: x.company_id.id == provider_id.company_id.id):
            raise ValidationError("Customer profile already linked in authorize.net")
        if merchant_id and self.email:
            shipping_address = self.get_partner_shipping_address(shipping_address_id)
            try:
                partner = self
                authorize_api = AuthorizeAPI(provider_id)
                resp = authorize_api.create_authorize_customer_profile(partner=partner, merchant=merchant_id, shipping=shipping_address.get('shipping'))
                if resp.get('profile_id') and resp.get('shipping_address_id'):
                    customer_profile_ids = self.env['res.partner.authorize'].create({
                        'customer_profile_id': resp['profile_id'],
                        'shipping_address_id': resp['shipping_address_id'],
                        'partner_id': self.id,
                        'company_id': company_id.id,
                        'merchant_id': merchant_id,
                        'acquirer_id': provider_id.id,
                    })
                    self.env.cr.commit()
            except UserError as e:
                raise UserError(_(e.name))
            except ValidationError as e:
                raise ValidationError(e.args[0])
            except Exception as e:
                raise UserError(_("Authorize.NET Error! : %s !" % e))
        else:
            raise ValidationError(_("To register a customer profile we need following data of customer: "
                                    "Customer ID and Email."))
        return customer_profile_ids
