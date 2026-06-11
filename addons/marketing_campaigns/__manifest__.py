{
    'name': 'Marketing Campaigns',
    'version': '1.0.0',
    'category': 'Marketing',
    'summary': 'Gestion des campagnes Meta & Google Ads avec tracking des leads',
    'description': """
        Module de gestion marketing :
        - Campagnes Meta (Facebook/Instagram) et Google Ads
        - Tracking Ad ID / Ad Name par plateforme
        - Source des leads (d'où vient le patient)
        - Budget et dépenses des campagnes
        - Lien avec les patients (optionnel)
    """,
    'author': 'Custom',
    'depends': ['base', 'mail'],
    'data': [
        'data/lead_source_data.xml',
        'views/marketing_campaign_views.xml',
        'views/ad_record_views.xml',
        'views/lead_source_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}