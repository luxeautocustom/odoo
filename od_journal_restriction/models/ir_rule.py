# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.tools import config
from odoo.osv import expression


class IRRule(models.Model):
    _inherit = "ir.rule"

    @api.model
    @tools.conditional(
        'xml' not in config['dev_mode'],
        tools.ormcache('self.env.uid', 'self.env.su', 'model_name', 'mode',
                       'tuple(self._compute_domain_context_values())'),
    )
    def _compute_domain(self, model_name, mode="read"):
        domain = super(IRRule, self)._compute_domain(model_name, mode=mode)
        if not self.env.user.has_group("base.group_system"):
            if model_name == 'account.journal':
                g_domain = ['|', ('user_ids', 'in', [self.env.user.id]),
                            ('user_ids', '=', False)]
                if domain:
                    domain = expression.AND([domain, g_domain])
            elif model_name == 'account.move':
                g_domain = ['|', ('journal_id.user_ids', 'in', [self.env.user.id]),
                            ('journal_id.user_ids', '=', False)]
                if domain:
                    domain = expression.AND([domain, g_domain])
            elif model_name == 'account.move.line':
                g_domain = ['|', ('journal_id.user_ids', 'in', [self.env.user.id]),
                            ('journal_id.user_ids', '=', False)]
                if domain:
                    domain = expression.AND([domain, g_domain])
        return domain
