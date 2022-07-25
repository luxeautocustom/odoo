# -*- coding: utf-8 -*-
{
    "name": "Odoo Documentation Builder",
    "version": "15.0.1.0.9",
    "category": "Website",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/odoo-documentation-builder-576",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "knowsystem_website"
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/data.xml",
        "views/res_config_settings.xml",
        "views/documentation_section.xml",
        "views/documentation_category.xml",
        "views/documentation_version.xml",
        "views/knowsystem_article.xml",
        "wizard/add_to_documentation.xml",
        "views/templates.xml",
        "views/menu.xml"
    ],
    "assets": {
        "web.assets_backend": [
                "documentation_builder/static/src/js/docu_kwowsystem_kanbancontroller.js"
        ],
        "web.assets_frontend": [
                "documentation_builder/static/src/css/documentation.css",
                "documentation_builder/static/src/js/documentation.js"
        ],
        "web.assets_qweb": [
                "documentation_builder/static/src/xml/*.xml"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The tool to create website documentation based on your knowledge base",
    "description": """
For the full details look at static/description/index.html

* Features * 




#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "89.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=137&ticket_version=15.0&url_type_id=3",
}