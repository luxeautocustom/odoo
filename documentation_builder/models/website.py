#coding: utf-8

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class website(models.Model):
    """
    Overwrite to keep configuration for particular website
    """
    _inherit = "website"

    @api.model
    def _docu_default_security_action_selection(self):
        """
        Method to get available security actions options
        """
        return self.env["documentation.section.article"]._security_action_selection()

    def _inverse_documentation_builder_portal(self):
        """
        Inverse method for documentation_builder_portal
        """
        for record in self:
            if not record.documentation_builder_portal:
                record.documentation_builder_public = False

    documentation_builder_portal = fields.Boolean(
        string="Portal Documentation",
        default=True,
        inverse=_inverse_documentation_builder_portal,
    )
    documentation_builder_public = fields.Boolean(
        string="Public Documentation",
        default=False,
    )
    docu_default_security_action = fields.Selection(
        _docu_default_security_action_selection,
        string="Default Security Action",
        default="no_access",
    )
    docu_attachments_show = fields.Boolean("Show Attachments")

    @api.model
    def create(self, values):
        """
        Overwrite to manage Documentaiton menu
        """
        if values.get("documentation_builder_public") is not None:
            record._generate_docu_menu(values.get("documentation_builder_public"), False)            
        return super(website, self).create(values)        

    def write(self, values):
        """
        Re-write to change menus
        """
        if values.get("documentation_builder_public") is not None:
            for record in self:
                record._generate_docu_menu(
                    values.get("documentation_builder_public"),
                    record.documentation_builder_public,
                )
        return super(website, self).write(values)

    def _generate_docu_menu(self, shouldbemenu, previouslyexist):
        """
        The method to add Documentation menu or ublink it

        Args:
         * shouldbemenu - bool - whether the menu should present
         * previouslyexist - whether the menu should have already exist (not to recover manually removed menu)
        
        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        exist_ids = self.env["website.menu"].search([
            ("url", "=", "/docs"), 
            ('website_id', 'in', [False, self.id]),
        ])
        if shouldbemenu:
            if not previouslyexist and not exist_ids:
                try:
                    values = {
                        "name": _("Docs"),
                        "url": "/docs",
                        "parent_id": self.menu_id.id,
                        "website_id": self.id,
                        "sequence": 60,
                    }
                    new_menu_id = self.env["website.menu"].create(values)
                except Exception as e:
                    _logger.warning(e)            
        elif exist_ids:
            exist_ids.unlink()

