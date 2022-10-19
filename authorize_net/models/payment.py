# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from .authorize_request import AuthorizeAPI

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PaymentAcquirerAuthorize(models.Model):
    _inherit = 'payment.acquirer'

    def _get_authorize_provider(self):
        return self.sudo().search([('provider','=','authorize'),
                            ('company_id', '=', self.env.company.id),
                            ('state', '!=', 'disabled')], limit=1)

    @api.onchange('company_id', 'provider')
    def _onchange_company(self):
        if self.provider == 'authorize' and self.company_id:
            return {
                'domain': {
                    'journal_id': [
                            ('type', '=', 'bank'),
                            ('authorize_cc', '=', True),
                            ('company_id', '=', self.company_id.id)
                        ]
                    }
            }
        else:
            return {
                'domain': {
                    'journal_id': [('type', 'in', ['bank', 'cash'])]
                    }
            }

    @api.constrains('authorize_login', 'authorize_transaction_key')
    def _check_authorize_login(self):
        for rec in self:
            try:
                if rec.provider == 'authorize':
                    journal_currency = False
                    if rec.authorize_login and rec.authorize_login != 'dummy' and rec.journal_id:
                        authorize_api = AuthorizeAPI(self)
                        journal_currency = rec.journal_id.currency_id.name
                        if not journal_currency:
                            journal_currency = rec.journal_id.company_id.currency_id.name
                        resp =  authorize_api.get_merchant_details()
                        if resp.get('resultCode') == 'Ok' and resp.get('x_currency') and resp['x_currency'][0] is not False:
                            merchant_currency = resp['x_currency'][0]
                            if journal_currency and merchant_currency and journal_currency != merchant_currency:
                                raise ValidationError(_("Do not Match Journal Currency and Merchant Acccount Currency."))
            except UserError as e:
                raise UserError(_(e.name))
            except ValidationError as e:
                raise ValidationError(e.args[0])
            except Exception as e:
                raise UserError(_("Authorize.NET Error! : %s !" %e))
