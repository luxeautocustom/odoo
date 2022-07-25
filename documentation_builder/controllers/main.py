# -*- coding: utf-8 -*-

import json
from werkzeug.urls import url_encode

from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import consteq
from odoo.tools.safe_eval import safe_eval

def preprocessprint(full_title):
    """
    The method to make possible print from portal
    """
    res = full_title.replace("/", "")
    res = res[:19]
    return res

class DocumentationController(http.Controller):
    """
    The controller to manage pages related to documentation
    """
    def _check_docs_rights(self, redirect_route="/knowsystem", redirect_params="{}", section_id=None):
        """
        The method to check whether this user is allowed to observe based on configured options
        1. If portal is turned but not website, and user is not logged in, we redirect to login
        2. If portal and website are turned on, but user is not logged in and doesn't have rights, also redirect to
           login

        Args:
         * redirect_route - in case of redirection after login
         * redirect_params - str representing dumped OrderDict
         * section_id - documentation.section object or none

        Returns:
         * False if no restrictions
         * Redirection otherwise
        """
        website_id = request.website
        show_portal = website_id.documentation_builder_portal
        show_website = website_id.documentation_builder_public
        res = False
        if not show_portal and not request.env.user.has_group('base.group_user'):
            res = request.render("http_routing.403")
        if show_portal and not request.env.user.has_group('base.group_portal') \
                       and not request.env.user.has_group('base.group_user'):
            redirect_required = False
            # 1
            if not show_website:
                redirect_required = True
            # 2
            elif section_id:
                try:
                    section_id.check_access_rights("read")
                    section_id.check_access_rule("read")
                except Exception as error:
                    redirect_required = True
            if redirect_required:
                redirect_path = "/web/login?&redirect={}<knowsystem_redirect>{}".format(
                    redirect_route, redirect_params,
                )
                res = request.redirect(redirect_path)
        return res

    @http.route(['/docs'], type='http', auth="public", website=True)
    def documentation_sections_overview(self, **kw):
        """
        The route to open documentation sections page
        """
        redirect_route = u"/docs/"
        params_str = json.dumps(request.params)
        res = self._check_docs_rights(redirect_route, params_str)
        if not res:
            search_context = request.env.context.copy()
            if kw.get("search"):
                search_context.update({"docu_section_search": kw.get("search")})
            categories = request.env["documentation.category"].search([
                ("website_published", "=", True), 
                ("website_id", "in", (False, request.website.id)),
            ])
            # to avoid showing empty for this user catgeories
            categories = categories.filtered(lambda categ: categ.with_context(search_context).get_sections_with_context())
            values = {
                "categories": categories.with_context(search_context),
                "docu_section_search": kw.get("search") and kw.get("search") or "",
            }
            res = request.render("documentation_builder.documentation_overview", values)
        return res

    @http.route(['/docs/<model("documentation.section"):doc_section_id>',], type='http', auth="public", website=True)
    def documentation_section(self, doc_section_id=None, **kw):
        """
        The route to open specified documentation section (with default version)
        """
        redirect_route = u"/docs/".format(doc_section_id.sudo().id)
        params_str = json.dumps(request.params)
        res = self._check_docs_rights(
            redirect_route=redirect_route, redirect_params=params_str, section_id=doc_section_id
        )
        if not res:
            ICPSudo = request.env['ir.config_parameter'].sudo()
            website_editor = safe_eval(ICPSudo.get_param('knowsystem_website_editor', default='False'))
            versioning_option = safe_eval(ICPSudo.get_param('group_documentation_versioning', default='False'))
            current_version = current_version_name = False
            available_versions = []
            if versioning_option:
                current_version = kw.get("version_id")
                if current_version:
                    try:
                        current_version_obj = request.env["documentation.version"].browse(current_version)
                        current_version_name = current_version_obj.name_get()[0][1]
                    except:
                        # if not correct version id 
                        current_version = False
                # in case we are under section sudo
                available_version_ids = request.env["documentation.version"].search([
                    ("id", "in", doc_section_id.version_ids.ids),
                    ("active", "=", True),
                ]) 
                available_versions = available_version_ids.name_get()
                if available_versions and (not current_version or current_version not in available_version_ids.ids):
                    current_version = available_versions[0][0]
                    return request.redirect("/docs/{}/{}?{}".format(current_version, doc_section_id.id, url_encode(kw)))
            values = {
                "main_object": doc_section_id,
                "page_name": "{}".format(doc_section_id.name),
                "available_versions": available_versions,
                "current_version": current_version,
                "current_version_name": current_version_name,
                "versioning_option": versioning_option,
                "url_main": "docs",
                "section_safe_name": preprocessprint(doc_section_id.name),
                "edit_website_possible": website_editor,
            }
            res = request.render("documentation_builder.documentation", values)        
        return res

    @http.route(['/docs/<int:doc_version_id>/<model("documentation.section"):doc_section_id>',], 
                type='http', auth="public", website=True)
    def documentation_section_version(self, doc_version_id=None, doc_section_id=None, **kw):
        """
        The route to open specified documentation section
        """
        ICPSudo = request.env['ir.config_parameter'].sudo()
        versioning_option = safe_eval(ICPSudo.get_param('group_documentation_versioning', default='False'))
        res = False
        if not versioning_option or not doc_version_id:
            # if versioning is not turned on or its is zero (global)
            res = request.redirect("/docs/{}?{}".format(doc_section_id.id, url_encode(kw)))
        else:
            kw.update({"version_id": doc_version_id})
            res = self.documentation_section(doc_section_id=doc_section_id, **kw)
        return res

    @http.route(['/doctoken/<int:docint>',], type='http', auth="public", website=True)
    def documentation_section_token(self, docint=None, **kw):
        """
        The route to open the article page by access token

        Methods:
         * _check_rights
         * update_number_of_views of knowsystem.article
         * _prepare_portal_layout_values
        """
        doc_section_id = request.env["documentation.section"].sudo().browse(docint)
        if not doc_section_id or not doc_section_id.exists() or not kw.get("access_token") \
                or not consteq(doc_section_id.access_token, kw.get("access_token")):
            res = request.render("http_routing.404")
        else:
            # SUPERUSER_ID is required for check rights because of has_group
            doc_section_id = doc_section_id.sudo().with_user(SUPERUSER_ID)
            ICPSudo = request.env['ir.config_parameter'].sudo()
            versioning_option = safe_eval(ICPSudo.get_param('group_documentation_versioning', default='False'))
            current_version = current_version_name = False
            available_versions = []
            if versioning_option:
                current_version = kw.get("version_id")
                if current_version:
                    try:
                        current_version_obj = request.env["documentation.version"].browse(current_version)
                        current_version_name = current_version_obj.name_get()[0][1]
                    except:
                        # if not correct version id 
                        current_version = False
                # in case we are under section sudo
                available_version_ids = request.env["documentation.version"].search([
                    ("id", "in", doc_section_id.version_ids.ids),
                    ("active", "=", True),
                ]) 
                available_versions = available_version_ids.name_get()
                if available_versions and (not current_version or current_version not in available_version_ids.ids):
                    current_version = available_versions[0][0]
                    return request.redirect(
                        "/docstokenmulti/{}/{}?{}".format(current_version, doc_section_id.id, url_encode(kw))
                    )
            values = {
                "main_object": doc_section_id,
                "page_name": "{}".format(doc_section_id.name),
                "available_versions": available_versions,
                "current_version": current_version,
                "current_version_name": current_version_name,
                "versioning_option": versioning_option,
                "url_main": "docstokenmulti",
                "section_safe_name": False,
                "edit_website_possible": False,
            }
            res = request.render("documentation_builder.documentation", values)
        return res

    @http.route(['/docstokenmulti/<int:doc_version_id>/<int:doc_section_id>',], 
                type='http', auth="public", website=True)
    def documentation_section_version_token(self, doc_version_id=None, doc_section_id=None, **kw):
        """
        The route to open specified documentation section
        """
        doc_section_id = request.env["documentation.section"].sudo().browse(doc_section_id)
        if not doc_section_id or not doc_section_id.exists() or not kw.get("access_token") \
                or not consteq(doc_section_id.access_token, kw.get("access_token")):
            res = request.render("http_routing.404")
        ICPSudo = request.env['ir.config_parameter'].sudo()
        versioning_option = safe_eval(ICPSudo.get_param('group_documentation_versioning', default='False'))
        res = False
        if not versioning_option or not doc_version_id:
            # if versioning is not turned on or its is zero (global)
            res = request.redirect("/doctoken/{}?{}".format(doc_section_id.id, url_encode(kw)))
        else:
            kw.update({"version_id": doc_version_id})
            res = self.documentation_section_token(docint=doc_section_id.id, **kw)
        return res

    @http.route(['/docs/<int:doc_version_id>/<model("documentation.section"):doc_section_id>/download/<aname>',], 
                type='http', auth="public", website=True)
    def documentation_section_articles_print(self, doc_version_id=None, doc_section_id=None, aname=None, **kw):
        """
        The route to make and download printing version of the documentation

        Methods:
         * _check_rights
         * get_access_method of documentation.section
         * render_qweb_pdf of report
         * make_response of odoo.request
        """
        redirect_route = u"/docs/".format(doc_section_id.sudo().id)
        params_str = json.dumps(request.params)
        res = self._check_docs_rights(
            redirect_route=redirect_route, redirect_params=params_str, section_id=doc_section_id
        )
        if not res:
            if doc_section_id:
                printed_articles = request.env["knowsystem.article"]
                ICPSudo = request.env["ir.config_parameter"].sudo()
                versioning_option = safe_eval(ICPSudo.get_param("group_documentation_versioning", default="False"))
                for article_id in doc_section_id.article_ids:
                    if not versioning_option or not article_id.sudo().version_ids \
                            or doc_version_id in article_id.sudo().version_ids.ids:
                        if doc_section_id.get_access_method(article_id, "read", request.website) == "sudo":
                            printed_articles += article_id.with_context(docu_builder=True).sudo().article_id

                if printed_articles:
                    lang = request.env.user.lang
                    report_id = request.env.ref("knowsystem.action_report_knowsystem_article")
                    pdf_content, mimetype = report_id.sudo().with_context(lang=lang)._render_qweb_pdf(
                        res_ids=printed_articles.ids,
                    )
                    pdfhttpheaders = [
                        ("Content-Type", "application/pdf"),
                        ("Content-Length", len(pdf_content)),
                    ]
                    res = request.make_response(pdf_content, headers=pdfhttpheaders)                    

                else:
                    res = request.render("http_routing.404")
            else:
                res = request.render("http_routing.404")
        return res

    @http.route(['/docs/<model("documentation.section"):doc_section_id>/download/<aname>',], 
                type='http', auth="public", website=True)
    def documentation_section_no_version_articles_print(self, doc_section_id=None, aname=None, **kw):
        """
        The route to make and download printing version of the documentation

        Methods:
         * _check_rights
         * get_access_method of documentation.section
         * render_qweb_pdf of report
         * make_response of odoo.request
        """
        redirect_route = u"/docs/".format(doc_section_id.sudo().id)
        params_str = json.dumps(request.params)
        res = self._check_docs_rights(
            redirect_route=redirect_route, redirect_params=params_str, section_id=doc_section_id
        )
        doc_version_id = False
        if not res:
            if doc_section_id:
                printed_articles = request.env["knowsystem.article"]
                ICPSudo = request.env["ir.config_parameter"].sudo()
                versioning_option = safe_eval(ICPSudo.get_param("group_documentation_versioning", default="False"))
                for article_id in doc_section_id.article_ids:
                    if not versioning_option or not article_id.sudo().version_ids \
                            or doc_version_id in article_id.sudo().version_ids.ids:
                        if doc_section_id.get_access_method(article_id, "read", request.website) == "sudo":
                            printed_articles += article_id.with_context(docu_builder=True).sudo().article_id

                if printed_articles:
                    lang = request.env.user.lang
                    report_id = request.env.ref("knowsystem.action_report_knowsystem_article")
                    pdf_content, mimetype = report_id.sudo().with_context(lang=lang)._render_qweb_pdf(
                        res_ids=printed_articles.ids,
                    )
                    pdfhttpheaders = [
                        ("Content-Type", "application/pdf"),
                        ("Content-Length", len(pdf_content)),
                    ]
                    res = request.make_response(pdf_content, headers=pdfhttpheaders)                    

                else:
                    res = request.render("http_routing.404")
            else:
                res = request.render("http_routing.404")
        return res
