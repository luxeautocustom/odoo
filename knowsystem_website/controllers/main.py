# -*- coding: utf-8 -*-

import json
import logging
import re

from collections import OrderedDict
from werkzeug.urls import url_encode

from odoo import _, http, SUPERUSER_ID
from odoo.http import request
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal, pager as portal_pager
from odoo.tools import consteq
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


def preprocessprint(full_title):
    """
    The method to make possible print from portal
    """
    res = full_title.replace("/", "")
    res = res[:19]
    return res

class CustomerPortal(CustomerPortal):
    """
    Overwritting the controller to show apps pages
    """
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        show_portal = request.website.knowsystem_website_portal
        values.update({"show_portal": show_portal,})
        return values

    def _return_search_in_articles(self, search_in, search):
        """
        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ('indexed_description'):
            search_domain =  [
                                '|', '|', '|',
                                    ('search_name_key', 'ilike', search),
                                    ('indexed_description', 'ilike', search),
                                    ('kanban_description', 'ilike', search),
                                    '&', # hack to search old articles; to-remove in v16
                                        ('search_name_key', '=', False),
                                        ('name', 'ilike', search),
                             ]
        if search_in in ('name'):
            search_domain = [
                '|',
                    ('search_name_key', 'ilike', search),
                    '&',  # hack to search old articles; to-remove in v16
                        ('search_name_key', '=', False),
                        ('name', 'ilike', search),
            ]
        if search_in in ('section_id'):
            search_domain = [('section_id.name', 'ilike', search)]

        website_id = request.website
        custom_search_ids =  website_id.knowsystem_custom_search_ids
        for csearch in custom_search_ids:
            field_name = csearch.sudo().custom_field_id.name
            if search_in in (field_name,):
                search_domain = [(field_name, 'ilike', search)]            
        return search_domain

    def _return_searchbar_sortings_articles(self, values):
        """
        Returns:
         * dict
            ** search_by_sortings - {}
            ** searchbar_filters dict - {}
            ** searchbar_inputs - {}

        Extra info:
         * for databases exist prior to search_name_key, sorting might work incorrect. It is needed to update
           either name or pubslihed name to trigger inverse
        """
        website_id = request.website
        searchbar_sortings = {
            'views': {'label': _('Trending'), 'order': 'views_number_internal desc, id desc'},
            'name': {'label': _('Title'), 'order': 'search_name_key asc, name asc, id desc'},
            'section': {'label': _('Section'), 'order': 'section_id asc, search_name_key asc, name asc, id desc'},
        }
        if request.website.knowsystem_portal_likes:
            searchbar_sortings.update({
                'likes': {'label': _('Likes'), 'order': 'likes_score desc, id desc'},
            })
        custom_sort_ids = website_id.sudo().knowsystem_custom_sorts_ids
        for csort in custom_sort_ids:
            try:
                searchbar_sortings.update({
                    "{}".format(csort.id): {
                        'label': csort.name,  'order': '{} {}, search_name_key asc, name asc, id desc'.format(
                            csort.custom_field_id.name,
                            csort.order_sort,
                        )
                    }
                })
            except:
                # for the case when field was removed
                continue

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        custom_filters_ids = website_id.sudo().knowsystem_portal_filters_ids
        for cfilter in custom_filters_ids:
            searchbar_filters.update({
                "{}".format(cfilter.id): {'label': cfilter.name,  'domain': safe_eval(cfilter.domain)}
            })
        searchbar_inputs = {
            'content': {'input': 'indexed_description', 'label': _('Search in content')},
            'name': {'input': 'name', 'label': _('Search in titles only')},
            'section': {'input': 'section_id', 'label': _('Search by section')},
        }
        custom_search_ids = website_id.sudo().knowsystem_custom_search_ids
        for csearch in custom_search_ids:
            try:
                searchbar_inputs.update({
                    "{}".format(csearch.sudo().custom_field_id.name): {
                        'input': csearch.sudo().custom_field_id.name, 
                        'label': csearch.name,
                    }
                })
            except:
                # for the case when field was removed
                continue
        return {
            "searchbar_sortings": searchbar_sortings,
            "searchbar_filters": searchbar_filters,
            "searchbar_inputs": searchbar_inputs,
        }

    def _prepare_articles_helper(self, page=1, sections=None, tags=None, types=None, sortby=None, filterby=None, 
                                 search=None, search_in='content', domain=[], url="/knowsystem", **kw):
        """
        The helper method for apps list
        """
        values = {}
        article_object = request.env['knowsystem.article']
        website_id = request.website
        domain += [("website_id", "in", [False, website_id.id]),]

        if not sortby:
            if request.website.knowsystem_default_sort_option == "default":
                sortby = request.website.knowsystem_default_sort or "views"
            elif request.website.knowsystem_default_sort_option == "custom":
                sortby = request.website.knowsystem_default_sort_id.id \
                         and "{}".format(request.website.knowsystem_default_sort_id.id) or "views"
            else:
                sortby = 'views'
        if not filterby:
            filterby = 'all'

        searches_res = self._return_searchbar_sortings_articles(values)
        searchbar_sortings = searches_res.get("searchbar_sortings")
        searchbar_filters = searches_res.get("searchbar_filters")
        searchbar_inputs = searches_res.get("searchbar_inputs")

        if not searchbar_sortings.get(sortby):
            sortby = 'views'
        sort_order = searchbar_sortings[sortby]['order']

        domain += searchbar_filters[filterby]['domain']
        done_filters = filterby != 'all' and searchbar_filters[filterby]["label"] or False

        if search and search_in:
            search_domain = self._return_search_in_articles(search_in, search)
            domain += search_domain
        # count for pager
        domain_real = [("website_pinned", "=", False)] + domain 
        articles_count_count = article_object.search_count(domain_real)
        # make pager
        pager = portal_pager(
            url=url,
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
                'sections': sections,
                'tags': tags,
                'types': types,
            },
            total=articles_count_count,
            page=page,
            step=website_id.pager_knowsystem,
        )
        article_ids = article_object.search(
            domain_real,
            order=sort_order,
            limit=website_id.pager_knowsystem,
            offset=pager['offset']
        )
        all_article_ids = article_object.search([])
        show_tooltip = website_id.knowsystem_portal_tooltip
        section_ids = all_article_ids.mapped("section_id")
        section_ids = str(section_ids.return_nodes_with_restriction(show_tooltip))
        tag_ids = request.env["knowsystem.tag"].search([
            ("active", "=", True), 
            ("website_published", "=", True),
            ("website_id", "in", [False, website_id.id]),
        ])
        tag_ids = str(tag_ids.return_nodes_with_restriction(show_tooltip))
        type_ids = str(article_object.action_return_types(True, website_id.id))
        domain_pinned = [("website_pinned", "=", True)] + domain 
        pinned_articles = article_object.search(domain_pinned)
        values.update({
            "article_ids": article_ids,
            'section_ids': section_ids,
            'tag_ids': tag_ids,
            'type_ids': type_ids,
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            "done_filters": done_filters,
            "pinned_articles": pinned_articles,
        })
        return values

    def _prepare_vals_articles(self, page=1, sections=None, tags=None, types=None, sortby=None, filterby=None, 
                               search=None, search_in='content', **kw):
        """
        The method to prepare values for articles
        """
        domain = []
        url="/knowsystem"
        if sections:
            sections_list = sections.split(",")
            sections_int_list = [int(item) for item in sections_list]
            domain += [("section_id", "in", sections_int_list)]
        if tags:
            tags_list = tags.split(",")
            tags_int_list = [int(item) for item in tags_list]
            tags_number = len(tags_int_list) - 1
            itera = 0
            while itera != tags_number:
                domain += ["|"]
                itera += 1
            for tag_u in tags_int_list:
                domain += [("tag_ids", "=", tag_u)]
        if types and hasattr(request.env['knowsystem.article'], 'custom_type_id'):
            types_list = types.split(",")
            types_int_list = [int(item) for item in types_list]
            domain += [("custom_type_id", "in", types_int_list)]            
        values = self._prepare_articles_helper(page=page, sections=sections, tags=tags, types=types, sortby=sortby, 
                                               filterby=filterby, search=search, search_in=search_in, domain=domain, 
                                               url=url, **kw)
        values.update({
            'page_name': _('KnowSystem'),
            'default_url': '/knowsystem',
            'sections': sections,
            'tags': tags,
            'types': types,
        })
        request.session['all_articles'] = values.get("article_ids").ids[:100]
        return values

    def _check_rights(self, redirect_route="/knowsystem", redirect_params="{}", article_id=None):
        """
        The method to check whether this user is allowed to observe based on configured options
        1. If portal is turned but not website, and user is not logged in, we redirect to login
        2. If portal and website are turned on, but user is not logged in and doesn't have rights, also redirect to
           login

        Args:
         * redirect_route - in case of redirection after login
         * redirect_params - str representing dumped OrderDict
         * article_id - knowsystem.article object or none

        Returns:
         * False if no restrictions
         * Redirection otherwise
        """
        website_id = request.website
        show_portal = website_id.knowsystem_website_portal
        show_website = website_id.knowsystem_website_public
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
            elif article_id:
                try:
                    article_id.with_context(no_sudo_required="True").name_get()
                except Exception as error:
                    redirect_required = True
            if redirect_required:
                redirect_path = "/web/login?&redirect={}<knowsystem_redirect>{}".format(
                    redirect_route, redirect_params,
                )
                res = request.redirect(redirect_path)
        return res

    @http.route(['/knowsystem', '/knowsystem/page/<int:page>',], type='http', auth="public", website=True)
    def website_knowsystem(self, page=1, sections=None, tags=None, types=None, sortby=None, filterby=None, search=None,
                           search_in='indexed_description', **kw):
        """
        The route to open the knowsystem website page
        """
        page_str = page != 1 and "/page/{}".format(page) or ""
        redirect_route = u"/knowsystem{}".format(page_str)
        params_str = json.dumps(request.params)
        res = self._check_rights(redirect_route=redirect_route, redirect_params=params_str)
        if not res:
            website_id = request.website
            values = self._prepare_vals_articles(page=page, sections=sections, tags=tags, types=types, sortby=sortby, 
                                                 filterby=filterby, search=search, search_in=search_in, **kw)
            portal_likes = website_id.knowsystem_portal_likes
            values.update({
                "articles_portal": True,
                "portal_likes": portal_likes,
            })
            if search:
                values.update({"done_search": search})
            res = request.render("knowsystem_website.knowsystem", values)
        return res

    @http.route(['/knowsystem/<model("knowsystem.article"):article_id>',], type='http', auth="public", website=True)
    def website_knowsystem_article(self, article_id=None, **kw):
        """
        The route to open the article page

        Methods:
         * _check_rights
         * update_number_of_views of knowsystem.article
         * _prepare_portal_layout_values
        """
        redirect_route = "/knowsystem/{}".format(article_id.sudo().id)
        params_str = json.dumps(request.params)
        res = self._check_rights(redirect_route=redirect_route, redirect_params=params_str, article_id=article_id)
        if not res:
            website_id = request.website
            article_id.with_context(no_sudo_required="True").name_get()
            ICPSudo = request.env['ir.config_parameter'].sudo()
            website_editor = safe_eval(ICPSudo.get_param('knowsystem_website_editor', default='False'))
            print_portal = website_id.knowsystem_portal_print
            portal_likes = website_id.knowsystem_portal_likes
            social_share = website_id.knowsystem_portal_social_share
            if article_id:
                values = {
                    "article_id": article_id,
                    "main_object": article_id,
                    "page_name": "{}".format(article_id.action_get_published_name()),
                    "articles_portal": True,
                    "edit_website_possible": website_editor,
                    "print_portal": print_portal,
                    "portal_likes": portal_likes,
                    "social_share": social_share,
                    "article_safe_name": preprocessprint(article_id.action_get_published_name()),
                }
                history = request.session.get('all_articles', [])
                values.update(get_records_pager(history, article_id))
                res = request.render("knowsystem_website.knowsystem_article", values)
                article_id.update_number_of_views()
            else:
                res = request.render("http_routing.404")
        return res

    @http.route(['/knowtoken/<int:articleint>',], type='http', auth="public", website=True)
    def website_knowsystem_article_token(self, articleint=None, **kw):
        """
        The route to open the article page by access token

        Methods:
         * _check_rights
         * update_number_of_views of knowsystem.article
         * _prepare_portal_layout_values
        """
        article_id = request.env["knowsystem.article"].sudo().browse(articleint)
        if not articleint or not article_id.exists() or not kw.get("access_token") \
                or not consteq(article_id.access_token, kw.get("access_token")):
            res = request.render("http_routing.404")
        else:
            # SUPERUSER_ID is required for check rights because of has_group
            article_id = article_id.sudo().with_user(SUPERUSER_ID)
            values = {
                "article_id": article_id,
                "main_object": article_id,
                "page_name": "{}".format(article_id.action_get_published_name()),
                "articles_portal": True,
                "edit_website_possible": False,
                "print_portal": False,
                "portal_likes": False,
                "social_share": False,
                "article_safe_name": preprocessprint(article_id.action_get_published_name()),
            }
            res = request.render("knowsystem_website.knowsystem_article", values)
            article_id.update_number_of_views()
        return res

    @http.route(['/knowsystem/<model("knowsystem.article"):article_id>/download/<aname>',], type='http', auth="public",
                website=True)
    def website_knowsystem_article_print(self, article_id=None, aname=None, **kw):
        """
        The route to make and download printing version of the article

        Methods:
         * _check_rights
         * render_qweb_pdf of report
         * make_response of odoo.request
        """
        res = self._check_rights()
        if not res:
            if article_id:
                lang = request.env.user.lang
                report_id = request.env.ref('knowsystem.action_report_knowsystem_article')
                pdf_content, mimetype = report_id.sudo().with_context(lang=lang)._render_qweb_pdf(
                    res_ids=article_id.id,
                )
                pdfhttpheaders = [
                    ('Content-Type', 'application/pdf'),
                    ('Content-Length', len(pdf_content)),
                ]
                res = request.make_response(pdf_content, headers=pdfhttpheaders)
            else:
                res = request.render("http_routing.404")
        return res

    @http.route(['/knowsystem/like/<model("knowsystem.article"):article_id>'], type='http', auth="user", website=True)
    def like_article(self, article_id, **kw):
        """
        The route like the article

        Methods:
         * like_the_article() of knowsystem.article
        """
        res = self._check_rights()
        if not res:
            article_id.like_the_article()
            done = u"/knowsystem/{}?{}".format(article_id.id, url_encode(kw))
            res = request.redirect(done)
        return res

    @http.route(['/knowsystem/dislike/<model("knowsystem.article"):article_id>'], type='http', auth="user",
                website=True)
    def dislike_article(self, article_id, **kw):
        """
        The route like the article

        Methods:
         * dislike_the_article() of knowsystem.article
        """
        res = self._check_rights()
        if not res:
            article_id.dislike_the_article()
            done = u"/knowsystem/{}?{}".format(article_id.id, url_encode(kw))
            res = request.redirect(done)
        return res
