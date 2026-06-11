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
        'wizards/send_order_views.xml',
        'wizards/adjustment_stage_views.xml',
        'wizards/declare_payment_wizard_view.xml',
],
    'license': 'LGPL-3',
}
