from odoo import fields, models


class PatientsMarketing(models.Model):
    """
    Extension du modèle 'patients' (patients_list) pour ajouter
    les champs marketing sans modifier le module d'origine.
    """
    _name = 'patients'
    _inherit = 'patients'

    # Source du lead (d'où vient ce patient)
    lead_source_id = fields.Many2one(
        'lead.source',
        string='Source du lead',
        tracking=True,
        help='D\'où vient ce patient ? (Facebook Ads, Google, bouche à oreille...)'
    )

    # Lien vers la publicité précise
    ad_id = fields.Many2one(
        'ad.record',
        string='Publicité (Ad)',
        tracking=True,
        help='Publicité précise qui a généré ce lead'
    )

    # Lien vers la campagne
    campaign_id = fields.Many2one(
        related='ad_id.campaign_id',
        string='Campagne',
        store=True,
        readonly=True
    )

    # Champs bruts Meta / Google (si pas de campagne dans le système)
    meta_ad_id = fields.Char(
        string='Meta Ad ID',
        help='ID de la publicité Meta (Facebook/Instagram) — fbclid ou ad_id du lead form'
    )
    meta_ad_name = fields.Char(
        string='Meta Ad Name',
        help='Nom de la publicité Meta'
    )
    google_ad_id = fields.Char(
        string='Google Ad ID',
        help='ID de l\'annonce Google (gclid ou creative ID)'
    )
    google_campaign_id = fields.Char(
        string='Google Campaign ID',
        help='ID de la campagne Google Ads'
    )
    utm_source = fields.Char(string='UTM Source', help='ex: facebook, google')
    utm_medium = fields.Char(string='UTM Medium', help='ex: cpc, paid_social')
    utm_campaign = fields.Char(string='UTM Campaign', help='Nom de campagne UTM')
    utm_content = fields.Char(string='UTM Content', help='Variante de l\'annonce')