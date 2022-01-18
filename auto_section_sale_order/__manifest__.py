# -*- coding: utf-8 -*-
{
    'name': 'Auto Section Sale Order',
    'version': '1.0',
    'summary': """
This module allows you to define the section inside the product. once you select the the product in sale order line 
save the sale order it will move sale order lines to the respected section define in the products. it will also manage 
the dynamic creation of section in sale order line.in case section not exist in sale order line it will create 
new section and move sale order line under the correct sections.
""",
    "description": """
        Auto Section Sale Order,
        Auto Section Invoice,
        move sale order line to define section,
        product section,
        auto product section,
        Section Auto Sale Order,
        Dynamic Sections,
        Auto Section,
        auto section
    """,
    'price': "40",
    'website': 'https://www.fiverr.com/share/3229Vx',
    'currency': 'USD',
    'author': 'Avision Infosoft',
    'images': ['static/description/img_4.png'],
    'company': 'Avision Infosoft',
    'depends': ['base', 'sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'view/product_product.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
}