#coding: utf-8

from odoo import _, api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval

AccessErrorMessage = _("Access for articles is denied by website settings!")


class knowsystem_article(models.Model):
    """
    Overwrite to add portal and website attributes
    """
    _name = "knowsystem.article"
    _inherit = ["knowsystem.article", "website.published.mixin", "website.multi.mixin", "website.seo.metadata", 
                "portal.mixin",]

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(knowsystem_article, self)._compute_website_url()
        for article in self:
            article.website_url = u'/knowsystem/{}'.format(slug(article))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for article in self:
            article.access_url = article.website_url

    def _compute_portal_has_right_to(self):
        """
        Compute method for portal_has_right_to
        """
        current_user = self.env.user
        parent = current_user.partner_id
        tag_ids = self.env["knowsystem.tag"]
        while parent:
            tag_ids += self.env["knowsystem.tag"].search([("partner_ids", "in", parent.ids)])
            parent = parent.parent_id
        tag_inlc_childs = self.env["knowsystem.tag"].search([("id", "child_of", tag_ids.ids)])
        article_ids = tag_inlc_childs.mapped("article_ids")
        for article in self:
            article.portal_has_right_to = article in article_ids and [(6, 0, [current_user.id])] or False

    def search_portal_has_right_to(self, operator, value):
        """
        Search method for portal_has_right_to
        """
        current_user = self.env["res.users"].browse(value)
        self.env["res.users"].invalidate_cache(ids=[current_user.id])
        parent = current_user.partner_id
        tag_ids = self.env["knowsystem.tag"]
        while parent:
            tag_ids += self.env["knowsystem.tag"].search([
                ("partner_ids", "in", parent.ids)
            ])
            parent = parent.parent_id
        tag_inlc_childs = self.env["knowsystem.tag"].search([
            ("id", "child_of", tag_ids.ids)
        ])
        article_ids = tag_inlc_childs.mapped("article_ids")
        return [('id', 'in', article_ids.ids)]

    portal_has_right_to = fields.Many2many(
        "res.users",
        "res_user_knowsystem_article_rel_table_portal",
        "res_users_id",
        "knowsystem_article_id",
        string="Portal right",
        compute=_compute_portal_has_right_to,
        search="search_portal_has_right_to",
    )
    website_pinned = fields.Boolean(
        string="Website Pinned",
        default=False,
        help="""
            If checked, such an article would be shown always above all articles and disregarding active page, which 
            sections or tags are selected.
        """,
    )

    def write(self, values):
        """
        Re-write to save changes to 'description' to make sure printing/emails backendeditor would work

        Extra info:
         * this action would make none of snippets suitable for printings 
         * we should each arcticle for a real change to avoid writing 'bad' description to articles which are not
           updated (especially from documentatiob page)
        """
        res = True
        if values.get("description_arch") and not values.get("description"):           
            for article in self:
                article_vals = values.copy()
                if values.get("description_arch") != article.description_arch:
                    article_vals.update({"description": values.get("description_arch")})
                res = super(knowsystem_article, article).write(article_vals)
        else:
            res = super(knowsystem_article, self).write(values)
        return res

    def name_get(self):
        """
        Overloading the method to overcome controller access rights
        """
        if self.env.context.get("no_sudo_required") == "True":
            return super(knowsystem_article, self).name_get()
        else:
            return super(knowsystem_article, self.sudo()).name_get()

    def check_access_rule(self, operation):
        """
        Re-write to check the public/portal options
        Implement mainly to avoid direct access to attachments. Does not influence _search

        Methods:
         * _check_article_public
        """
        if self._check_article_public():
            return super(knowsystem_article, self).check_access_rule(operation=operation)

    def _check_article_public(self):
        """
        The method to check whether article is available for public / portal users according to the options

        Methods:
         * _check_website_options

        Returns:
         * True if no error registered
        """
        if not self.env.user.has_group("base.group_user"):
            portal, public = self._check_website_options()
            for article in self:
                website = article.sudo().website_id
                if website:
                    portal_access = website.knowsystem_website_portal
                    public_access = website.knowsystem_website_public
                else:
                    portal_access, public_access = portal, public
                if not portal_access:
                    raise AccessError(AccessErrorMessage)
                elif not public_access and not self.env.user.has_group("base.group_portal"):
                    raise AccessError(AccessErrorMessage)
        return True

    @api.model
    def _check_website_options(self):
        """
        The method for global website article - to check whether anywhere the options are turned on
        It is enough a single website to finish check

        Returns:
         * bool, bool
        """
        self = self.sudo()
        portal = self.env["website"]._search([("knowsystem_website_portal", "=", True)], limit=1) and True or False
        public = False
        if portal:
            public = self.env["website"]._search([("knowsystem_website_public", "=", True)], limit=1) and True or False
        return portal, public

    def return_complementary_data(self):
        """
        Re-write to add website_published and website
        """
        res = super(knowsystem_article, self).return_complementary_data()
        res.update({
            "knowsystem_website": True,
            "website_published": self.website_published,
        })
        return res

    def return_selected_articles(self):
        """
        Re-write to add website is installed
        """
        res = super(knowsystem_article, self).return_selected_articles()
        return [res[0], True]

    def publish_article(self):
        """
        The method to publish article

        Methods:
         * website_publish_button
         * return_complementary_data

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self.write({"website_published": not self.website_published})
        cdata = self.return_complementary_data()
        return cdata

    def mass_publish(self):
        """
        The method to publish a few articles simultaneously
        """
        self.write({"website_published": True})

    def edit_website(self):
        """
        Open url of this article on website
        """
        ICPSudo = self.env['ir.config_parameter'].sudo()
        website_editor = safe_eval(ICPSudo.get_param('knowsystem_website_editor', default='False'))
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/knowsystem/{}{}'.format(self.id, website_editor and "?enable_editor" or ""),
        }
