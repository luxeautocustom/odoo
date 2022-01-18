# -*- coding: utf-8 -*-
##############################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
##############################################################################

{
    'name': "Section Subtotal (Enterprise)",
    'version': '1.0',
    'category': 'sales, purchase, account',
    'description': """
        Show order/invoice line total by section
    """,
    'price': 25.00,
    'currency': 'EUR',
    'author': 'Acespritech Solutions Pvt. Ltd',
    'website': 'http://www.acespritech.com',
    'summary': 'This module will show total of section in order/invoice '
               'line.',
    'depends': ['base', 'sale', 'sale_management', 'purchase', 'account'],
    'images': ['static/description/sale_order_section.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_view.xml',
        'views/purchase_order_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'aspl_section_sub_total_ee/static/src/js/section_and_note_fields_backend.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
