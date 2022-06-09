# -*- coding: utf-8 -*-
{
    'name': 'Restriction of Journal User',
    'version': '13.0.1.0.1',
    'category': 'Account',
    'author': 'Oxilia-info',
    'website': 'https://oxilia-info.fr',
    'license': 'LGPL-3',
    'summary': """Restrict Journal Users.""",
    'description': 'The module allows to restrict access to Journal for users.',
    'depends': [
        'account',
    ],
    'data': [
        'security/journal_user_restrict_security.xml',
        'views/res_users_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
