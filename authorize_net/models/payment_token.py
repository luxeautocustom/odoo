# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from datetime import datetime
from .authorize_request import AuthorizeAPI

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.authorize_net.models import misc


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    @api.model
    def default_get(self, fields):
        res = super(PaymentToken, self).default_get(fields)
        context = dict(self.env.context or {})
        if context.get('authorize') and 'default_partner_id' in context:
            if 'default_partner_id' in context and not context.get('default_partner_id'):
                raise ValidationError('Please Create Partner or configure Authorize Payment Acquirer.')
            partner_id = self.env['res.partner'].browse(context['default_partner_id'])
            cid = partner_id.authorize_partner_ids.filtered(lambda x: x.company_id and x.company_id.id == self.env.company.id)
            if not cid:
                cid = partner_id.authorize_customer_create()
            if cid:
                acquirer_id = self.env['payment.acquirer'].sudo().search([('provider', '=', 'authorize'), \
                                ('company_id', '=', self.env.company.id), \
                                ('authorize_payment_method_type', '=', self.env.context.get('default_authorize_payment_method_type'))], limit=1)
                if acquirer_id:
                    res.update({
                        'partner_id': context['default_partner_id'],
                        'acquirer_ref': 'dummy',
                        'acquirer_id': acquirer_id.id,
                        'company_id': cid.company_id.id,
                        'customer_profile_id': cid.customer_profile_id,
                    })
                else:
                    raise ValidationError('Please configure Authorize Payment Acquirer.')
        return res

    def _get_billing_partner_domain(self):
        domain = [('type', '=', 'invoice')]
        if self._context.get('default_partner_id'):
            domain.append(('parent_id', '=', self._context['default_partner_id']))
        return domain

    authorize_card = fields.Boolean('Authorize Card', default=False, readonly=True)
    update_value = fields.Boolean('Update Value', default=True)
    credit_card_no = fields.Char('Card Number', size=16)
    credit_card_code = fields.Char('CVV', size=4)
    credit_card_type = fields.Selection([
                                ('americanexpress', 'American Express'),
                                ('visa', 'Visa'),
                                ('mastercard', 'Mastercard'),
                                ('discover', 'Discover'),
                                ('dinersclub', 'Diners Club'),
                                ('jcb', 'JCB')], 'Card Type', readonly=True)
    credit_card_expiration_month = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
                                                     ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
                                                     ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12'),
                                                     ('xx', 'XX')], 'Expires Month')
    credit_card_expiration_year = fields.Char('Expires Year', size=64)
    billing_partner_id = fields.Many2one('res.partner', 'Billing Partner', domain=_get_billing_partner_domain)

    acc_number = fields.Char('Account Number', required=False)
    owner_name = fields.Char('Owner Name', size=64)
    bank_name = fields.Char('Bank Name', size=64)
    routing_number = fields.Char('Routing Number', size=9)
    authorize_bank_type = fields.Selection([('checking', 'Personal Checking'), ('savings', 'Personal Savings'),('businessChecking', 'Business Checking')], 'Authorize Bank Type')

    customer_profile_id = fields.Char(string="Profile ID")
    company_id = fields.Many2one('res.company', 'Company', index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string="Customer")
    acquirer_id = fields.Many2one('payment.acquirer', 'Acquirer', copy=False)
    partner_ref_id = fields.Many2one(related='partner_id')
    provider = fields.Selection(related='acquirer_id.provider')

    @api.onchange("credit_card_no")
    def onchange_card_num(self):
        self.credit_card_type = False
        context = dict(self.env.context or {})
        if self.credit_card_no:
            self.credit_card_type = misc.cc_type(self.credit_card_no) or False
            self.partner_id = context.get('default_partner_id')
            self.name = str(misc.masknumber(self.credit_card_no))

    @api.onchange("acc_number")
    def onchange_account_num(self):
        context = dict(self.env.context or {})
        if self.acc_number:
            self.partner_id = context.get('default_partner_id')
            self.name = str(misc.mask_account_number(self.acc_number))

    def create_credit_card(self, values):
        context = dict(self.env.context or {})
        try:
            if values.get('acquirer_id') and values.get('partner_id'):
                provider_id = self.env['payment.acquirer'].sudo().browse(values['acquirer_id'])
                partner_id = self.env['res.partner'].browse(values['partner_id'])
                # customer credit Detail
                if context.get('is_import'):
                    return values
                elif values.get('customer_profile_id') and values.get('credit_card_no', False) and \
                    values.get('credit_card_code', False) and values.get('credit_card_expiration_month', False) and \
                    values.get('credit_card_expiration_year', False) and not context.get('is_import'):
                    expiry_date = values['credit_card_expiration_year'] + '-' + values['credit_card_expiration_month']
                    if datetime.now().strftime('%Y%m') > datetime.strptime(expiry_date, '%Y-%m').strftime('%Y%m'):
                        raise ValidationError(_("Card expiration date is not valid."))
                    billing_partner_id = None
                    if values.get('billing_partner_id'):
                        billing_partner_id = self.env['res.partner'].browse(values['billing_partner_id'])
                    billing_detail = partner_id.get_partner_billing_address(billing_partner_id)
                    card_details = {
                        'card_number': values['credit_card_no'],
                        'expiry_date': expiry_date,
                        'card_code': values['credit_card_code']
                    }
                    authorize_api = AuthorizeAPI(provider_id)
                    resp =  authorize_api.create_customer_payment_profile(partner=self,
                                    card_details=card_details, billing=billing_detail.get('billing'), customer_profile_id=values['customer_profile_id'])
                    if resp.get('customerPaymentProfileId') and resp.get('customerProfileId'):
                        ccdid = resp['customerPaymentProfileId']
                        validate_payment = authorize_api.validate_customer_payment_profile(customer_profile_id=values['customer_profile_id'], payment_profile_id=ccdid)
                        if validate_payment.get('result_code') == "Ok":
                            return {
                                'name': str(misc.masknumber(values['credit_card_no'])),
                                'acquirer_ref': str(ccdid),
                                'credit_card_no': str(misc.masknumber(values['credit_card_no'])),
                                'credit_card_code': str(misc.masknumber(values['credit_card_code'])),
                                'credit_card_expiration_month': 'xx',
                                'credit_card_expiration_year': str(misc.masknumber(values['credit_card_expiration_year'])),
                                'credit_card_type': values['credit_card_type'],
                                'customer_profile_id': values['customer_profile_id'],
                                'acquirer_id': values.get('acquirer_id', False),
                                'company_id': values.get('company_id', False),
                                'authorize_profile': resp['customerProfileId'],
                                'verified': True,
                                'authorize_card': True,
                                'authorize_payment_method_type': 'credit_card'
                            }
                else:
                    raise UserError(_("Please enter valid credit card details."))
            else:
                if not values.get('acquirer_id', False):
                    raise ValidationError(_('Please configure your Authorize.Net account'))
                if not values.get('partner_id', False):
                    raise ValidationError(_('Partner is not defined'))
        except UserError as e:
            raise UserError(_(e.name))
        except ValidationError as e:
            raise ValidationError(e.args[0])
        except Exception as e:
            raise UserError(_("Authorize.NET Error! : %s !" %e))
        return values

    def create_account(self, values):
        provider_id = self.env['payment.acquirer']._get_authorize_provider()
        if not provider_id:
            raise ValidationError(_('Please configure your Authorize.Net account'))
        try:
            if values.get('acquirer_id') and values.get('partner_ref_id'):
                provider_id = self.env['payment.acquirer'].sudo().browse(values['acquirer_id'])
                partner_id = self.env['res.partner'].browse(values['partner_ref_id'])
                billing_partner_id = None
                if values.get('billing_partner_id'):
                    billing_partner_id = self.env['res.partner'].browse(values['billing_partner_id'])
                # customer Bank Detail
                if values.get('owner_name') and values.get('authorize_bank_type') and partner_id:
                    billing_detail = partner_id.get_partner_billing_address(billing_partner_id)
                    bank_details = {
                        'accountType': values.get('authorize_bank_type'),
                        'routingNumber': values.get('routing_number'),
                        'accountNumber': values.get('acc_number'),
                        'nameOnAccount': values.get('owner_name'),
                        'bankName': values.get('bank_name', '')
                    }
                    cid = partner_id.authorize_partner_ids.filtered(lambda x: x.company_id.id == provider_id.company_id.id)
                    # Create the payment data for a bank account
                    authorize_api = AuthorizeAPI(provider_id)
                    resp =  authorize_api.create_customer_payment_profile(partner=self.partner_id, customer_profile_id=cid.customer_profile_id or self.customer_profile_id, billing=billing_detail.get('billing'), bank_details=bank_details)
                    if resp.get('customerPaymentProfileId') and resp.get('customerProfileId'):
                        ccdid = resp['customerPaymentProfileId']
                        validate_payment = authorize_api.validate_customer_payment_profile(customer_profile_id=resp['customerProfileId'], payment_profile_id=ccdid)
                        if validate_payment.get('result_code') == "Ok":
                            return {
                                'partner_id': partner_id.id,
                                'name': values.get('name'),
                                'acquirer_ref': str(ccdid),
                                'authorize_bank_type': values.get('authorize_bank_type'),
                                'routing_number':str(misc.mask_account_number(values['routing_number'])),
                                'acc_number': values.get('name'),
                                'owner_name': values.get('owner_name'),
                                'bank_name': values.get('bank_name', False),
                                'customer_profile_id': resp['customerProfileId'],
                                'acquirer_id': values.get('acquirer_id', False),
                                'company_id': values.get('company_id', False),
                                'authorize_profile': resp['customerProfileId'],
                                'verified': True,
                                'authorize_payment_method_type': 'bank_account'
                            }

                else:
                    raise ValidationError(_("Please enter proper account detail."))
        except UserError as e:
            raise UserError(_(e.name))
        except ValidationError as e:
            raise ValidationError(e.args[0])
        except Exception as e:
            raise UserError(_("Authorize.NET Error! : %s !" % e))
        return True

    def update_ccd_value(self):
        if self.acquirer_ref:
            self.update({
                'update_value': True,
                'credit_card_code': False,
                'credit_card_type': False,
                'credit_card_no': False,
                'credit_card_expiration_month': False,
                'credit_card_expiration_year': False,
                'verified': False
            })

    def update_acc_value(self):
        if self.acquirer_ref:
            self.update({
                'update_value': True,
                'acc_number': False,
                'owner_name': False,
                'bank_name': False,
                'routing_number': False,
                'authorize_bank_type': False,
            })

    def update_credit_card(self, values):
        self.ensure_one()
        context = dict(self.env.context or {})
        provider_id = self.acquirer_id
        if not provider_id:
            raise ValidationError(_('Please configure your Authorize.Net account'))
        try:
            if provider_id and self.customer_profile_id and values.get('credit_card_code') and \
                values.get('credit_card_expiration_year') and values.get('credit_card_expiration_month') and \
                values.get('credit_card_no'):
                expiry_date = values['credit_card_expiration_year'] + '-' + values['credit_card_expiration_month']
                if datetime.now().strftime('%Y%m') > datetime.strptime(expiry_date, '%Y-%m').strftime('%Y%m'):
                    raise ValidationError(_("Card expiration date is not valid."))

                billing_partner_id = self.billing_partner_id
                if values.get('billing_partner_id'):
                    billing_partner_id = self.env['res.partner'].browse(values['billing_partner_id'])
                billing_detail = self.partner_id.get_partner_billing_address(billing_partner_id)
                card_details = {
                    'card_number': values['credit_card_no'],
                    'expiry_date': expiry_date,
                    'card_code': values['credit_card_code']
                }
                authorize_api = AuthorizeAPI(provider_id)
                resp =  authorize_api.update_customer_payment_profile(partner=self, card_details=card_details, billing=billing_detail.get('billing'),
                                        customer_profile_id=self.customer_profile_id, payment_profile_id=self.acquirer_ref)
                if resp.get('result_code') == "Ok":
                    validate_payment = authorize_api.validate_customer_payment_profile(customer_profile_id=self.customer_profile_id, payment_profile_id=self.acquirer_ref)
                    if validate_payment.get('result_code') == "Ok":
                        values.update({
                            'name': str(misc.masknumber(values['credit_card_no'])),
                            'credit_card_type': values['credit_card_type'],
                            'credit_card_no': misc.masknumber(values['credit_card_no']),
                            'credit_card_code': misc.masknumber(values['credit_card_code']),
                            'credit_card_expiration_month': 'xx',
                            'credit_card_expiration_year': misc.masknumber(values['credit_card_expiration_year']),
                            'verified': True,
                            'authorize_card': True
                        })
                return values
            else:
                raise UserError(_("Please enter valid credit card detail."))
        except UserError as e:
            raise UserError(_(e.name))
        except ValidationError as e:
            raise ValidationError(e.args[0])
        except Exception as e:
            raise UserError(_("Authorize.NET Error! : %s !" %e))
        return values

    def update_account(self, values):
        self.ensure_one()
        provider_id = self.env['payment.acquirer']._get_authorize_provider()
        if not provider_id:
            raise ValidationError(_('Please configure your Authorize.Net account'))
        try:
            cid = self.partner_id.authorize_partner_ids.filtered(lambda x: x.company_id.id == provider_id.company_id.id)
            if not cid:
                cid = self.partner_id.authorize_customer_create()
            if cid.customer_profile_id and \
                values.get('authorize_bank_type') and values.get('routing_number') and \
                values.get('acc_number'):
                billing_partner_id = self.billing_partner_id
                if values.get('billing_partner_id'):
                    billing_partner_id = self.env['res.partner'].browse(values['billing_partner_id'])
                billing_detail = self.partner_id.get_partner_billing_address(billing_partner_id)
                bank_details = {
                    'accountType': values['authorize_bank_type'],
                    'routingNumber': values['routing_number'],
                    'accountNumber': values['acc_number'],
                    'nameOnAccount': values['owner_name'],
                    'bankName': values.get('bank_name', '')
                }
                authorize_api = AuthorizeAPI(provider_id)
                resp =  authorize_api.update_customer_payment_profile(
                            partner=self.partner_id, bank_details=bank_details,
                            billing=billing_detail.get('billing'),
                            customer_profile_id=cid.customer_profile_id or self.customer_profile_id,
                            payment_profile_id=self.acquirer_ref)
                if resp.get('result_code') == 'Ok':
                    values.update({
                        'authorize_bank_type': values['authorize_bank_type'],
                        'routing_number': str(misc.mask_account_number(values['routing_number'])),
                        'acc_number': values['acc_number']
                    })
            else:
                raise ValidationError(_("Please enter proper account detail."))
        except UserError as e:
            raise UserError(_(e.name))
        except ValidationError as e:
            raise ValidationError(e.args[0])
        except Exception as e:
            raise UserError(_("Authorize.NET Error! : %s !" % e))
        return values

    @api.model_create_multi
    def create(self, values_list):
        context = dict(self.env.context) or {}
        for values in values_list:
            if context.get('authorize') and not context.get('is_import'):
                if values.get('credit_card_no'):
                    values.update({'credit_card_type': misc.cc_type(values['credit_card_no']) or False})
                    if hasattr(self, 'create_credit_card'):
                        values.update(getattr(self, 'create_credit_card')(values))
                        fields_wl = set(self._fields) & set(values)
                        values = {field: values[field] for field in fields_wl}
                else:
                    if hasattr(self, 'create_account'):
                        values.update(getattr(self, 'create_account')(values))
                        fields_wl = set(self._fields) & set(values)
                        values = {field: values[field] for field in fields_wl}
        res = super(PaymentToken, self.sudo()).create(values)
        res.update({'update_value': False})
        return res

    def write(self, values):
        context = dict(self.env.context or {})
        for rec in self:
            if rec.acquirer_id and rec.acquirer_id.provider == 'authorize' and rec.acquirer_ref and not context.get('is_import'):
                if values.get('credit_card_expiration_year') and values.get('credit_card_expiration_month') and \
                    values.get('credit_card_code') and values.get('credit_card_no'):
                    values.update({
                        'update_value': False,
                        'credit_card_type': misc.cc_type(values['credit_card_no']) or False,
                    })
                    values = rec.update_credit_card(values)
                else:
                    if values.get('authorize_bank_type') and \
                        values.get('routing_number') and values.get('acc_number'):
                        values.update({'update_value': False})
                        values = rec.update_account(values)
        return super(PaymentToken, self).write(values)

    def unlink(self):
        for rec in self:
            transaction_ids = rec.env['payment.transaction'].search([('token_id','=',rec.id)])
            if not transaction_ids:
                if rec.acquirer_id.provider == 'authorize' and rec.acquirer_ref != 'dummy' and rec.partner_id:
                    authorize_api = AuthorizeAPI(rec.acquirer_id)
                    if rec.customer_profile_id and rec.acquirer_ref:
                        resp =  authorize_api.unlink_customer_payment_profile(customer_profile_id=rec.customer_profile_id,
                                                                              payment_profile_id=rec.acquirer_ref)
            else:
                raise UserError(_("Authorize.NET Error! : Payment transaction is available for this token so you can't Delete it!"))
        return super(PaymentToken, self).unlink()
