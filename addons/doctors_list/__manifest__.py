{
    'name': 'Doctors list',
    'description': "Doctors list",
    'depends': ['base', 'finance_manage'],
    'data': [
        'views/doctors_view.xml',
        'views/doctor_speciality_view.xml',
        'views/appointment_inherit_views.xml',
        'views/laboratory_list_views.xml',
        'views/laboratory_order_views.xml',
        'views/quotations_inherit_views.xml',
        'views/doctor_dashboard_views.xml',
        'wizards/send_order_views.xml',
        'wizards/adjustment_stage_views.xml',
        'wizards/declare_payment_wizard_view.xml',
        'wizards/lab_order_wizard_views.xml',
        'report/report_dental_lab_order.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'doctors_list/static/src/css/doctor_dashboard.css',
            'doctors_list/static/src/js/doctor_dashboard.js',
            'doctors_list/static/src/xml/doctor_dashboard.xml',
        ],
    },
    'license': 'LGPL-3',
}