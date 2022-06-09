# -*- coding: utf-8 -*-

{
    'name': 'Pos Exact Search',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Allows you to search exactly what you want.',
    'description': """

=======================
Allows you to search exactly what you want.

""",
    'depends': ['point_of_sale'],
    'data': [
            'views/template.xml',
            'views/views.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/pos.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 20,
    'currency': 'EUR',
}
