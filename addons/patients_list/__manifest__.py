{
    'name': 'HMS',
    'description': "Dental clinic Managment",
    'depends': ['base'],
    'data': [
        'views/countries_views.xml',
        'views/patients_views.xml',
        'views/cities_views.xml',
        'views/appointment_view.xml',
        'views/contact_view.xml',
        'views/medical_histiry_views.xml',
        'views/quotations_views.xml',
        'views/treatments_views.xml',
        'views/quotation_treatment_viwes.xml',
        'views/teeth_views.xml',
        'views/treatment_plan_views.xml',
        'views/trealment_plan_lines_views.xml',
        'views/patient_attachments_views.xml',
        'views/payment_patient_views.xml',
],
'assets': {
    'web.assets_backend': [
        'patients_list/static/src/css/style.css',
    ],
},
    'license': 'LGPL-3',
}
