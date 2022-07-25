# -*- coding: utf-8 -*-

from odoo import fields, models


class knowsystem_tag(models.Model):
    """
    The model to systemize documentation sections
    """
    _inherit = "knowsystem.tag"

    doc_ids = fields.Many2many(
        "documentation.section",
        "knowsystem_tag_documentation_section_r_table",
        "documentation_section_r_id",
        "knowsystem_tag_r_id",
        string="Doc Sections",
    )    
