# -*- coding: utf-8 -*-

from odoo import api, fields, models


class add_to_documentation(models.TransientModel):
    _name = "add.to.documentation"
    _description = "Add articles to documentation"

    @api.model
    def _security_action_selection(self):
        """
        Method to get available security actions options
        """
        return self.env["documentation.section.article"]._security_action_selection()

    section_id = fields.Many2one(
        "documentation.section",
        string="Documentation Section",
        required=True,
    )
    articles = fields.Char(string="Articles")
    security_action = fields.Selection(
        _security_action_selection,
        string="Security Action",
        default=False,
    )
    version_ids = fields.Many2many(
        "documentation.version",
        "documentation_version_add_to_documentation_article_rel_table",
        "documentation_version_rel_id",
        "add_to_documentation_rel_id",
        string="Versions",
    )


    @api.model
    def create(self, values):
        """
        Overwrite to trigger adding of articles to a documentation section

        Methods:
         * action_add_to_doc

        Extra info:
         *  we do not use standard wizard buttons in the footer to use standard js forms
        """
        res = super(add_to_documentation, self).create(values)
        res.action_add_to_doc()
        return res

    def action_add_to_doc(self):
        """
        The method to select tour and add selected articles to it

        Returns:
         * Action of the tour

        Extra info:
         * we use articles char instead of m2m as ugly hack to avoid default m2m strange behaviour
         * Expected singleton
        """
        self.ensure_one()
        article_ids = self.articles.split(",")
        existing_articles = self.section_id.article_ids.mapped("article_id.id")
        article_ids = [int(art) for art in article_ids if int(art) not in existing_articles]
        docu_article = self.env["documentation.section.article"]
        max_sequence = self.section_id.article_ids and self.section_id.article_ids[-1].sequence + 1 or 0
        for article in article_ids:
            values = {
                "documentation_id": self.section_id.id,
                "article_id": article,
                "sequence": max_sequence,
                "security_action": self.security_action,
                "version_ids": [(6, 0, self.version_ids.ids or [])],
            }
            new_article = docu_article.create(values)
            max_sequence += 1
