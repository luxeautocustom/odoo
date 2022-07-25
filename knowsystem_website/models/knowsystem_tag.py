#coding: utf-8

from odoo import fields, models


class knowsystem_tag(models.Model):
    """
    Overwrite to introduce portal security mechanics
    """
    _name = "knowsystem.tag"
    _inherit = ["knowsystem.tag", "website.multi.mixin", "website.published.mixin"]

    partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_know_system_tag_rel_table",
        "res_partner_id",
        "knowsystem_tag_id",
        string="Allowed partners",
        help="""
            Portal users of those partners would be able to observe articles with the current tag and its child tags
            disregarding whether an article is published or not
        """,
    )
    website_published = fields.Boolean(string="Show Tag on Website",)
