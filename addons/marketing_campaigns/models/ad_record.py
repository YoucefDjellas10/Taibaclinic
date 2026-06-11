from odoo import fields, models, api


class AdRecord(models.Model):
    _name = 'ad.record'
    _description = 'Publicité (Ad)'
    _inherit = ['mail.thread']
    _order = 'campaign_id, name'

    # ── Identification ───────────────────────────────────────────────────────
    name = fields.Char(string='Nom de la publicité (Ad Name)', required=True, tracking=True)
    ad_id = fields.Char(string='Ad ID', required=True, tracking=True,
                        help='Identifiant unique de la publicité sur Meta ou Google')
    adset_name = fields.Char(string='Ad Set / Ad Group', help='Nom de l\'ensemble publicitaire')

    campaign_id = fields.Many2one('marketing.campaign', string='Campagne', required=True, ondelete='cascade')
    platform = fields.Selection(related='campaign_id.platform', string='Plateforme', store=True, readonly=True)
    lead_source_id = fields.Many2one(related='campaign_id.lead_source_id', string='Source Lead', store=True, readonly=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('paused', 'En pause'),
        ('stopped', 'Arrêtée'),
    ], string='Statut', default='active', tracking=True)

    # ── Contenu ──────────────────────────────────────────────────────────────
    ad_format = fields.Selection([
        ('image', 'Image'),
        ('video', 'Vidéo'),
        ('carousel', 'Carrousel'),
        ('story', 'Story'),
        ('reel', 'Reel'),
        ('text', 'Texte'),
        ('responsive', 'Responsive (Google)'),
    ], string='Format')

    headline = fields.Char(string='Titre / Headline')
    description = fields.Text(string='Description de l\'annonce')
    destination_url = fields.Char(string='URL de destination')

    # ── KPIs de la pub ───────────────────────────────────────────────────────
    currency = fields.Many2one(related='campaign_id.currency', string='Devise', readonly=True)
    impressions = fields.Integer(string='Impressions')
    clicks = fields.Integer(string='Clics')
    spend = fields.Monetary(currency_field='currency', string='Dépense')
    leads_generated = fields.Integer(string='Leads générés')

    note = fields.Text(string='Notes')

    # Lien vers les patients (si le module patients_list est installé)
    patient_ids = fields.Many2many(
        'patients', string='Patients issus de cette pub',
        help='Patients/leads qui viennent de cette publicité'
    )
    patient_count = fields.Integer(string='Nb Patients', compute='_compute_patient_count')

    def _compute_patient_count(self):
        for rec in self:
            rec.patient_count = len(rec.patient_ids)

    def action_view_patients(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patients',
            'res_model': 'patients',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.patient_ids.ids)],
        }


class CampaignDeposit(models.Model):
    _name = 'campaign.deposit'
    _description = 'Dépôt / Recharge de budget campagne'
    _order = 'date desc'

    campaign_id = fields.Many2one('marketing.campaign', string='Campagne', required=True, ondelete='cascade')
    currency = fields.Many2one(related='campaign_id.currency', string='Devise', readonly=True)

    date = fields.Date(string='Date du dépôt', required=True, default=fields.Date.today)
    amount = fields.Monetary(currency_field='currency', string='Montant déposé', required=True)

    platform = fields.Selection(related='campaign_id.platform', string='Plateforme', readonly=True, store=True)

    payment_method = fields.Selection([
        ('card', 'Carte bancaire'),
        ('bank_transfer', 'Virement bancaire'),
        ('paypal', 'PayPal'),
        ('cash', 'Espèces'),
        ('other', 'Autre'),
    ], string='Mode de paiement')

    reference = fields.Char(string='Référence paiement')
    note = fields.Text(string='Note')
    responsible_id = fields.Many2one('res.users', string='Fait par', default=lambda self: self.env.user)