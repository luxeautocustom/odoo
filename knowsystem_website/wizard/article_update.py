# -*- coding: utf-8 -*-

from odoo import fields, models


class article_update(models.TransientModel):
    _inherit = "article.update"

    publish = fields.Selection(
        [
            ("publish", "Publish"),
            ("unpublish", "Unpublish"),
        ],
        string="Website Published",
    )

    def _prepare_values(self):
        """
        Re write to add mass publish / unpublish
        """
        values = super(article_update, self)._prepare_values()
        if self.publish:
            if self.publish == "publish":
                values.update({"website_published": True})
            else:
                values.update({"website_published": False})
        return values
