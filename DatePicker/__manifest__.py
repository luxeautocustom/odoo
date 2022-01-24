# -*- coding: utf-8 -*-
{
    'name': "DatePicker",

    'summary': """
        DatePicker 
        """,

    'description': """
        DatePicker
    """,
    'version': '15.0.0.1',
    'license': 'OPL-1',    

    'author': "yao",

    'category': 'Tools',

    'depends': ['base'],

    # always loaded
    'data': [
        # 'views/views.xml',
        'views/res_lang_view.xml',
        'data/res.lang.csv',
    ],
     'images': [
        'static/description/Banner.gif',
    ],
     
    'assets': {
         'web.assets_common': [
            'DatePicker/static/js/*.js',
        ],
        },
     
    'installable': True,
    'auto_install': False,
    "price": 29.99,
    'currency': 'USD',
}
