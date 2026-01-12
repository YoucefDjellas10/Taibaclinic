# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Groups',
    'summary': 'Groups for access rights',
    'description': "Groups for access rights",
    'depends': ['base', 'patients_list'],
    'data': [
        'security/access_groups.xml',
        'security/ir.model.access.csv',

    ],

    'installable': True,
    'application': True,

    'license': 'LGPL-3',
}
