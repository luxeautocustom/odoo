# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class documentation_section_article(models.Model):
    """
    The model to link documentation and articles
    """
    _name = "documentation.section.article"
    _description = "Documentation Article"

    @api.model
    def _security_action_selection(self):
        """
        Selection method to get possible security actions
        """
        return [
            ("no_access", _("Not shown")),
            ("warning", _("Warning Shown")),
            ("sudo", _("Neglect access rights")),
        ]

    article_id = fields.Many2one(
        "knowsystem.article",
        string="Article",
        required=True,
    )
    documentation_id = fields.Many2one("documentation.section", string="Documentation")
    sequence = fields.Integer(string="Sequence", default=0,)
    security_action = fields.Selection(
        _security_action_selection,
        string="Security Action",
        default=False,
        help="""
            The setting defines how to proceed an article if a current user does not have an acccess to article:
             * Not shown - article is just not shown
             * Warning shown - instead of an article, a warning about restricted access is shown
             * Neglect access rights - article would be shown as a user has full rights for this
            If not defined, the setting from configuration page would be used 
        """,
    )
    version_ids = fields.Many2many(
        "documentation.version",
        "documentation_version_documentation_section_article_rel_table",
        "documentation_version_rel_id",
        "documentation_section_article_rel_id",
        string="Versions",
    )

    _order = "sequence, article_id, id"

    _sql_constraints = [(
        'unique_article_per_section',
        'unique(article_id,documentation_id)',
       'Article should be unique per documentation!',
    )]

