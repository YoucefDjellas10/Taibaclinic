{
    'name': 'Taiba Statistics',
    'author': 'Taiba Dental Clinic',
    'version': '19.0.1.0.0',
    'summary': 'Statistics dashboards for Taiba Dental Clinic',
    'description': "Statistics dashboards: revenue by doctor, laboratory, CRM, appointments, finance, purchases, stock and expenses.",
    'depends': ['web', 'patients_list', 'doctors_list', 'finance_manage', 'access_rights'],
    'data': [
        'views/stats_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'taiba_stats/static/src/css/stats_dashboard.css',
            'taiba_stats/static/src/js/stats_dashboard.js',
            'taiba_stats/static/src/xml/stats_dashboard.xml',
        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
