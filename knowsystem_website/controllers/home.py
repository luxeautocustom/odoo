# -*- coding: utf-8 -*-

import json

from werkzeug.urls import url_encode

from odoo import http

from odoo.addons.website.controllers.main import Home


class KnowSystemHome(Home):
    """
    Re-write to pass params in login redirect correctly
    """

    @http.route(website=True, auth="public")
    def web_login(self, redirect=None, *args, **kw):
        """
        We would try to retrieve other redirect params, since '&' add those to kwargs altough passed in redirect
        Take into account that such approach relies upon key 'knowsystem_redirect' inside redirect
        """
        final_redirect = redirect
        if redirect:
            parts = redirect.split("<knowsystem_redirect>")
            if len(parts) > 1:
                extra_params = url_encode(json.loads(parts[1]))
                final_redirect = u"{}?{}".format(parts[0], extra_params)
        response = super(KnowSystemHome, self).web_login(redirect=final_redirect, *args, **kw)
        return response
