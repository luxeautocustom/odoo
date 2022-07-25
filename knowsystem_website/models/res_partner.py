#coding: utf-8

from odoo import fields, models


class res_partner(models.Model):
    """
    Overwrite to add knowsystem tags to partners
    """
    _inherit = "res.partner"

    knowsystem_tag_ids = fields.Many2many(
        "knowsystem.tag",
        "res_partner_know_system_tag_rel_table",
        "knowsystem_tag_id",
        "res_partner_id",
        string="KnowSystem Tags",
    )
