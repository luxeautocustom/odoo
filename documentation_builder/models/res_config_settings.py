# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

PARAMS = [
    ("group_documentation_versioning", safe_eval, "False"), # since portal & public would not have a group
]

class res_config_settings(models.TransientModel):
    """
    Overwrite to add website-specific settings
    """
    _inherit = "res.config.settings"

    def _default_docu_builder_website_id(self):
        """
        Default method for knowsystem_website_id
        """
        return self.env['website'].search([('company_id', '=', self.env.company.id)], limit=1)

    docu_builder_website_id = fields.Many2one(
        "website",
        string='Documentation Website',
        default=_default_docu_builder_website_id, 
        ondelete='cascade',
    )
    documentation_builder_portal = fields.Boolean(
        related="docu_builder_website_id.documentation_builder_portal",
        readonly=False,
    )
    documentation_builder_public = fields.Boolean(
        related="docu_builder_website_id.documentation_builder_public",
        readonly=False,
    )
    group_documentation_versioning = fields.Boolean(
    	string="Versioning",
        implied_group='documentation_builder.group_documentation_versioning',    	
    )
    docu_default_security_action = fields.Selection(
        related="docu_builder_website_id.docu_default_security_action",
        readonly=False,
    )
    docu_attachments_show = fields.Boolean(
        related="docu_builder_website_id.docu_attachments_show",
        readonly=False,
    )


    def set_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, getter, default in PARAMS:
            value = getattr(self, field_name, default)
            Config.set_param(field_name, value)
