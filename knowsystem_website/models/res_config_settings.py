# -*- coding: utf-8 -*-

from odoo import fields, models


class res_config_settings(models.TransientModel):
    """
    Overwrite to add website-specific settings
    """
    _inherit = "res.config.settings"

    def _default_knowsystem_website_id(self):
        """
        Default method for knowsystem_website_id
        """
        return self.env["website"].search([("company_id", "=", self.env.company.id)], limit=1)

    knowsystem_website_id = fields.Many2one(
        "website",
        string="KnowSystem Website",
        default=_default_knowsystem_website_id, 
        ondelete="cascade",
    )
    knowsystem_website_portal = fields.Boolean(
        related="knowsystem_website_id.knowsystem_website_portal",
        readonly=False,
    )
    knowsystem_website_public = fields.Boolean(
        related="knowsystem_website_id.knowsystem_website_public",
        readonly=False,
    )
    knowsystem_portal_print = fields.Boolean(
        related="knowsystem_website_id.knowsystem_portal_print",
        readonly=False,
    )
    knowsystem_portal_likes = fields.Boolean(
        related="knowsystem_website_id.knowsystem_portal_likes",
        readonly=False,
    )
    knowsystem_portal_social_share = fields.Boolean(
        related="knowsystem_website_id.knowsystem_portal_social_share",
        readonly=False,
    )
    knowsystem_portal_tooltip = fields.Boolean(
        related="knowsystem_website_id.knowsystem_portal_tooltip",
        readonly=False,
    )
    knowsystem_portal_filters_ids = fields.Many2many(
        related="knowsystem_website_id.knowsystem_portal_filters_ids",
        readonly=False,
    )
    knowsystem_custom_search_ids = fields.Many2many(
        related="knowsystem_website_id.knowsystem_custom_search_ids",
        readonly=False,
    )
    knowsystem_custom_sorts_ids = fields.Many2many(
        related="knowsystem_website_id.knowsystem_custom_sorts_ids",
        readonly=False,
    )
    knowsystem_default_sort_option = fields.Selection(
        related="knowsystem_website_id.knowsystem_default_sort_option",
        readonly=False,
    )
    knowsystem_default_sort = fields.Selection(
        related="knowsystem_website_id.knowsystem_default_sort",
        readonly=False,
    )
    knowsystem_default_sort_id = fields.Many2one(
        related="knowsystem_website_id.knowsystem_default_sort_id",
        readonly=False,        
    )
    pager_knowsystem = fields.Integer(
        related="knowsystem_website_id.pager_knowsystem",
        readonly=False,
    )

    def set_values(self):
        super(res_config_settings, self).set_values()
