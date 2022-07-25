# -*- coding: utf-8 -*-

from odoo import fields, models

class documentation_category(models.Model):
    """
    The model to categorize documentation sections
    """
    _name = "documentation.category"
    _inherit = ["website.published.mixin", "website.multi.mixin"]
    _description = "Documentation Category"

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
    sequence = fields.Integer(
        string="Sequence",
        help="The lesser the closer to the top",
        default=0,
    )
    section_ids = fields.One2many(
        "documentation.section",
        "category_id",
        string="Sections",
    )

    _order = "sequence, id"

    def get_sections_with_context(self):
        """
        The method to return sections searched by context

        1. to apply security rules, since we search articles under sudo

        Extra info:
         * Expected singeton

        Returns:
         * documentation.section recordset
        """
        self.ensure_one()
        sections = self.section_ids
        if self._context.get("docu_section_search"):
            search_term = self._context.get("docu_section_search")
            article_ids = self.env["documentation.section.article"].sudo().search([
                ("documentation_id.category_id", "=", self.id),
                "|", "|", "|", "|", "|", "|", "|", "|",
                    ("documentation_id.name", "ilike", search_term),
                    ("documentation_id.short_description", "ilike", search_term),
                    ("documentation_id.introduction", "ilike", search_term),
                    ("documentation_id.footer", "ilike", search_term),
                    ("documentation_id.category_id.name", "ilike", search_term),
                    ("article_id.name", "ilike", search_term),
                    ("article_id.published_name", "ilike", search_term),
                    ("article_id.indexed_description", "ilike", search_term),
                    ("article_id.kanban_manual_description", "ilike", search_term),
            ])
            sections = article_ids.mapped("documentation_id")
            # 1
            sections = self.env["documentation.section"].search([("id", "in", sections.ids)])
        else:
            sections = self.section_ids
        return sections




