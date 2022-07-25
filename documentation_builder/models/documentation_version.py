# -*- coding: utf-8 -*-

from odoo import api, fields, models

class documentation_version(models.Model):
    """
    The model to introduce sections versions
    """
    _name = "documentation.version"
    _inherit = ["website.published.mixin"]
    _description = "Version"

    name = fields.Char(
        string="Title",
        required=True,
        translate=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Uncheck to archive",
    )
    color = fields.Integer(string='Color index', default=10,)
    sequence = fields.Integer(
        string="Sequence",
        help="The lesser the closer to the top",
        default=0,
    )
    section_ids = fields.Many2many(
        "documentation.section",
        "documentation_version_documentation_section_rel_table",
        "documentation_section_rel_id",
        "documentation_version_rel_id",
        string="Sections",
    )

    _order = "sequence, id"
