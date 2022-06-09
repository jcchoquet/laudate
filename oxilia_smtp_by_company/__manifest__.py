# -*- coding: utf-8 -*-

{
    'name': 'OXILIA SMTP',
    'description':"""Module which allows to configure
            outgoing email server by company.
                """,
    'version': '1.0',
    'category': 'Mail',
    'author': 'Oxilia-Info',
    'website': 'www.oxilia-info.fr',
    'depends': ['mail'],
    'summary':"""Configure different outgoing mail server for each company
    """,
    'data': [
        'views/res_config_views.xml',
        'views/ir_mail_server_view.xml',
             ],
    'application': False,
    'installable': True,
    'auto_install': False,    
}
