# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    user_ids = fields.Many2many('res.users', 'journal_user_rel',
                                string='Allowed Users')
