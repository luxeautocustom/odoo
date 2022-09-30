# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = "res.users"

    journal_ids = fields.Many2many('account.journal', 'journal_user_rel',
                                   string='Allowed Journals')
