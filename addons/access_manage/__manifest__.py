{
    'name': 'User Manage',
    'summary': 'Internal registry of user access (name, email, password, groups)',
    'description': "Internal registry of user access (name, email, password, groups)",
    'depends': ['base'],
    'data': [
        'views/access_manage_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
