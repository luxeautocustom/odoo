# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def _change_journal_account(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.user.company_id
    acquirer_ids = env['payment.acquirer'].sudo().search([('provider', '=', 'authorize'), ('company_id', '=', company.id)])
    for acquirer in acquirer_ids.filtered(lambda aq: aq.journal_id):
        acquirer.journal_id.authorize_cc = True
