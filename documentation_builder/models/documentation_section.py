# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.translate import html_translate

class documentation_section(models.Model):
    """
    The model to combine articles into a documentation section
    """
    _name = "documentation.section"
    _inherit = [ "mail.thread", "mail.activity.mixin", "website.published.mixin", "website.seo.metadata", 
                 "image.mixin", "portal.mixin",]
    _description = "Documentation Section"

    @api.model
    def _max_header_to_parse_selection(self):
        """
        Method to generate header 
        """
        return [(str(header), str(header)) for header in range(0, 7)]

    def _compute_website_url(self):
        """
        Overwritting the compute method for portal_url to pass our pathes

        Methods:
         * super
        """
        super(documentation_section, self)._compute_website_url()
        for section in self:
            section.website_url = u"/docs/{}".format(slug(section))

    def _compute_access_url(self):
        """
        Overwritting the compute method for access_url to pass our pathes

        Methods:
         * super
        """
        for section in self:
            section.access_url = section.website_url

    def _compute_portal_has_right_to(self):
        """
        Compute method for portal_has_right_to

        To-do:
         * think of making that context dependentant
        """
        current_user = self.env.user
        parent = current_user.partner_id
        tag_ids = self.env["knowsystem.tag"]
        while parent:
            tag_ids += self.env["knowsystem.tag"].search([("partner_ids", "in", parent.ids)])
            parent = parent.parent_id
        tag_inlc_childs = self.env["knowsystem.tag"].search([("id", "child_of", tag_ids.ids)])
        section_ids = tag_inlc_childs.mapped("doc_ids")
        for section in self:
            section.portal_has_right_to = section in section_ids and [(6, 0, [current_user.id])] or False

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
        doc_ids = tag_inlc_childs.mapped("doc_ids")
        return [("id", "in", doc_ids.ids)]

    @api.model
    def _read_group_category_id(self, stages, domain, order):
        """
        The method to open in kanban even empty columns
        """
        return self.env["documentation.category"].search([])

    name = fields.Char(
        string="Title",
        required=True,
        translate=True,
    )
    category_id = fields.Many2one(
        "documentation.category",
        string="Category",
        required=True,
        group_expand="_read_group_category_id",
    )
    article_ids = fields.One2many(
        "documentation.section.article",
        "documentation_id",
        string="Articles",
    )
    short_description = fields.Text(string="Preview Text", translate=True,)
    introduction = fields.Html(string="Introduction", translate=html_translate,        )
    footer = fields.Html(string="Footer", translate=html_translate,        )
    max_header_to_parse = fields.Selection(
        _max_header_to_parse_selection,
        string="Header Level for Navigation",
        help="""
            Defines article inline headers should be parsed for navigation (table of contents)
            * '0' - articles content headers would not be added to the navigation panel
            * '3' - headers till the third level (h1, h2, h3) would be parsed
            * '6' - h1, h2, h3, h4, h5, h6 article headers would be added to the navigation panel
        """,
        default="3",
    )
    tag_ids = fields.Many2many(
        "knowsystem.tag",
        "knowsystem_tag_documentation_section_r_table",
        "knowsystem_tag_r_id",
        "documentation_section_r_id",
        string="Tags",
        copy=True,
    )
    portal_has_right_to = fields.Many2many(
        "res.users",
        "res_user_knowsystem_article_rel_table_portal",
        "res_users_id",
        "knowsystem_article_id",
        string="Portal right",
        compute=_compute_portal_has_right_to,
        search="search_portal_has_right_to",
    )
    version_ids = fields.Many2many(
        "documentation.version",
        "documentation_version_documentation_section_rel_table",
        "documentation_version_rel_id",
        "documentation_section_rel_id",
        string="Versions",
    )
    sequence = fields.Integer(
        "Sequence",
        default=0,
        help="The lesser the closer to the top",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Uncheck to archive",
    )
    color = fields.Integer(string="Color")

    _order = "sequence, id"

    def name_get(self):
        """
        Overloading the method to overcome controller access rights
        """
        if self.env.context.get("no_sudo_required") == "True":
            return super(documentation_section, self).name_get()
        else:
            return super(documentation_section, self.sudo()).name_get()

    def return_headers_depth(self):
        """
        The method to return queryselector for headers to parse
        
        Returns:
         * char (e.g. "h1, h2")

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        res = ""
        if self.max_header_to_parse and self.max_header_to_parse != "0":
            max_level = int(self.max_header_to_parse)
            for itera in range(1, max_level+1):
                res += "h{},".format(itera)
            else:
                res = res[:-1]
        return res

    def get_access_method(self, article, mode, website_id=False):
        """
        The method to check out security action for the article

        Args:
         * documentation.section.article object
         * mode - char: "read", "write", etc
         * website_id - website object

        Returns:
         * char - one of security action values

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        res = website_id.docu_default_security_action or "no_access"
        try:
            # user have the right for an article
            article.article_id.check_access_rights(mode)
            article.article_id.check_access_rule(mode)
            res = "sudo"
        except:
            res = article.security_action or res
        if not article.sudo().article_id.active:
            # not active articles are never shown
            res = "no_access"            
        return res    

    def return_add_to_documentation_wizard(self):
        """
        The method to return add to tourd view
        """
        view_id = self.sudo().env.ref("documentation_builder.add_to_documentation_form_view").id
        return view_id
    
    def return_form_view(self):
        """
        The method to open form of the documentation

        Returns:
         * action
        """
        action_id = self.sudo().env.ref("documentation_builder.documentation_section_action_form_only")
        action = action_id.read()[0]
        action["res_id"] = self.id
        return action