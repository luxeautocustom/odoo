# -*- coding: utf-8 -*-
{
    "name": "KnowSystem: Website and Portal",
    "version": "15.0.1.0.11",
    "category": "Website",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/knowsystem-website-and-portal-575",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "knowsystem",
        "website"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/knowsystem_article.xml",
        "views/knowsystem_tag.xml",
        "views/res_partner.xml",
        "wizard/article_update.xml",
        "views/assets.xml",
        "views/templates.xml",
        "views/res_config_settings.xml"
    ],
    "assets": {
        "web.assets_frontend": [
                "knowsystem_website/static/src/css/style.css",
                "knowsystem_website/static/src/js/sections.js"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The extension to KnowSystem to publish articles to portal and public users",
    "description": """
For the full details look at static/description/index.html

* Features * 




#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "36.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=84&ticket_version=15.0&url_type_id=3",
}