from odoo import fields, models, api
from odoo.exceptions import ValidationError


class MarketingCampaign(models.Model):
    _name = 'marketing.campaign'
    _description = 'Campagne Marketing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    # ── Informations générales ──────────────────────────────────────────────
    name = fields.Char(string='Nom de la campagne', required=True, tracking=True)
    reference = fields.Char(string='Référence', readonly=True, copy=False, default='Nouveau')

    platform = fields.Selection([
        ('meta', 'Meta (Facebook / Instagram)'),
        ('google', 'Google Ads'),
        ('tiktok', 'TikTok'),
        ('other', 'Autre'),
    ], string='Plateforme', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Active'),
        ('paused', 'En pause'),
        ('closed', 'Terminée'),
    ], string='Statut', default='draft', tracking=True)

    lead_source_id = fields.Many2one('lead.source', string='Source Lead', tracking=True)
    objective = fields.Selection([
        ('awareness', 'Notoriété'),
        ('traffic', 'Trafic'),
        ('leads', 'Génération de leads'),
        ('conversions', 'Conversions'),
        ('messages', 'Messages'),
    ], string='Objectif', tracking=True)

    # ── Dates ───────────────────────────────────────────────────────────────
    date_start = fields.Date(string='Date de début', required=True)
    date_end = fields.Date(string='Date de fin')

    # ── IDs publicitaires ───────────────────────────────────────────────────
    campaign_id_ext = fields.Char(string='Campaign ID (externe)', help='ID de la campagne sur Meta ou Google')
    adset_id = fields.Char(string='Ad Set ID / Ad Group ID', help='ID de l\'ensemble de publicités')
    ad_ids = fields.One2many('ad.record', 'campaign_id', string='Publicités (Ads)')

    # ── Budget & Dépenses ───────────────────────────────────────────────────
    currency = fields.Many2one(
        'res.currency', string='Devise',
        default=lambda self: self.env.ref('base.DZD')
    )
    budget_total = fields.Monetary(
        currency_field='currency',
        string='Budget total alloué',
        tracking=True
    )
    budget_daily = fields.Monetary(
        currency_field='currency',
        string='Budget journalier'
    )
    amount_spent = fields.Monetary(
        currency_field='currency',
        string='Montant dépensé',
        compute='_compute_amount_spent',
        store=True,
        tracking=True
    )
    amount_remaining = fields.Monetary(
        currency_field='currency',
        string='Reste du budget',
        compute='_compute_amount_remaining',
        store=True
    )
    deposit_ids = fields.One2many('campaign.deposit', 'campaign_id', string='Dépôts / Recharges')
    total_deposited = fields.Monetary(
        currency_field='currency',
        string='Total déposé',
        compute='_compute_total_deposited',
        store=True
    )

    # ── Résultats & KPIs ────────────────────────────────────────────────────
    impressions = fields.Integer(string='Impressions')
    clicks = fields.Integer(string='Clics')
    leads_count = fields.Integer(string='Leads générés', compute='_compute_leads_count')
    ctr = fields.Float(string='CTR (%)', compute='_compute_ctr', digits=(6, 2))
    cpl = fields.Monetary(currency_field='currency', string='Coût par lead', compute='_compute_cpl')

    # ── Notes ───────────────────────────────────────────────────────────────
    note = fields.Text(string='Notes')
    responsible_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)

    # ── Computed ────────────────────────────────────────────────────────────
    ad_count = fields.Integer(string='Nb Ads', compute='_compute_ad_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nouveau') == 'Nouveau':
                vals['reference'] = self.env['ir.sequence'].next_by_code('marketing.campaign') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('deposit_ids.amount')
    def _compute_total_deposited(self):
        for rec in self:
            rec.total_deposited = sum(rec.deposit_ids.mapped('amount'))

    @api.depends('budget_total', 'total_deposited')
    def _compute_amount_spent(self):
        # amount_spent = ce qui a été prélevé = budget_total (défini manuellement)
        # On laisse l'utilisateur mettre à jour ce champ via les dépôts
        for rec in self:
            rec.amount_spent = rec.budget_total

    @api.depends('total_deposited', 'budget_total')
    def _compute_amount_remaining(self):
        for rec in self:
            rec.amount_remaining = rec.total_deposited - rec.budget_total

    def _compute_leads_count(self):
        for rec in self:
            rec.leads_count = self.env['ad.record'].search_count([
                ('campaign_id', '=', rec.id)
            ])

    def _compute_ad_count(self):
        for rec in self:
            rec.ad_count = len(rec.ad_ids)

    @api.depends('clicks', 'impressions')
    def _compute_ctr(self):
        for rec in self:
            rec.ctr = (rec.clicks / rec.impressions * 100) if rec.impressions else 0.0

    @api.depends('budget_total', 'leads_count')
    def _compute_cpl(self):
        for rec in self:
            rec.cpl = (rec.budget_total / rec.leads_count) if rec.leads_count else 0.0

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_end < rec.date_start:
                raise ValidationError("La date de fin doit être après la date de début.")

    # ── Actions ─────────────────────────────────────────────────────────────
    def action_activate(self):
        self.write({'state': 'active'})

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_view_ads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Publicités',
            'res_model': 'ad.record',
            'view_mode': 'list,form',
            'domain': [('campaign_id', '=', self.id)],
            'context': {'default_campaign_id': self.id},
        }