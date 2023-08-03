{
    'name': "Website Multilingual Multimedia",
	'name_vi_VN': "Đa ngôn ngữ Đa phương tiện trang Web",
    'summary': """Translate multimedia such as videos and images in multilingual environment""",
    'summary_vi_VN': """Dịch đa phương tiện như hình ảnh và video trong môi trường đa ngôn ngữ""",

    'description': """
Problem
=======
By default, translating multimedia such as videos and images in multilingual environment is impossible. For example, you have a demonstration image containing English content for an English page (original) and you are not be able to have its Vietnamese version for the corresponding Vietnamese page.

Key Features
============

* Translate images (by choosing another image URL during page translation).
* Translate video (by choosing another URL during page translation). Youtube, Vimeo, Dailymotion and Youku are supported. Video link and video iframe are supported.

See demonstration video here: https://youtu.be/32iOuuXiXUs

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,
    'description_vi_VN': """
Vấn đề
======
Theo mặc định, dịch đa phương tiện như hình ảnh và video trong môi trường đa ngôn ngữ là không thể. Ví dụ: bạn có một hình ảnh minh họa chứa nội dung tiếng Anh cho một trang tiếng Anh (bản gốc) và bạn không thể có hình ảnh minh họa chứa nội dung tiếng Việt cho trang tiếng Việt tương ứng.

Tính năng chính
===============

* Dịch hình ảnh (bằng cách chọn một hình ảnh khác trong khi dịch trang).
* Dịch video (bằng cách chọn một video khác trong khi dịch trang). Youtube, Vimeo, Dailymotion và Youku được hỗ trợ. Liên kết video và iframe video được hỗ trợ.

Xem video mô phỏng: https://youtu.be/32iOuuXiXUs

Ấn bản được Hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,

    'author': "Viindoo",
    'website': "https://viindoo.com/apps/app/15.0/viin_website_multilingual_multimedia",
    'live_test_url': "https://v15demo-int.viindoo.com",
    'live_test_url_vi_VN': "https://v15demo-vn.viindoo.com",
    'demo_video_url': "https://youtu.be/j8MWWhu92q8",
    'support': "apps.support@viindoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/Viindoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images' : [
        'static/description/main_screenshot.png'
        ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
    'auto_install': True,
    'price': 18.9,
    'currency': 'EUR',
    'assets': {
        'website.assets_editor': [
            'viin_website_multilingual_multimedia/static/src/js/menu/translate.js',
        ],
    },
    'license': 'OPL-1',
}
