# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Backend Stripe Payment',
    'version' : '1.0',
    'summary': """Allow Admin/Account user to pay using stripe from backend""",
    'sequence': 15,
    'description': """Allow Admin/Account user to pay using stripe from backend""",
    'category': 'Accounting',
    'author': 'Synconics Technologies Pvt. Ltd.',
    'website': 'https:www.synconics.com',
    'depends': ['payment_stripe', 'portal'],
    'data': [
        'security/security.xml',
        'data/mail_template_data.xml',
        'views/account_invoice_view.xml',
        'views/payment_stripe_ext.xml',
        'views/payment_views.xml',
        'views/report_invoice.xml'
    ],
    'demo': [],
    'images': [
        'static/description/main_screen.png'
    ],
    'assets': {
        'web.assets_backend': [
            'payment_stripe_ext/static/src/scss/style.scss',
            '/payment_stripe_ext/static/src/js/checkout.js',
        ],
    },
    'price': 50.0,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
