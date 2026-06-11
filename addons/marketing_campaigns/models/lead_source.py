from odoo import fields, models


class LeadSource(models.Model):
    _name = 'lead.source'
    _description = 'Source des Leads'
    _order = 'name asc'

    name = fields.Char(string='Source', required=True)
    platform = fields.Selection([
        ('meta', 'Meta (Facebook / Instagram)'),
        ('google', 'Google Ads'),
        ('tiktok', 'TikTok'),
        ('organic', 'Organique / SEO'),
        ('referral', 'Bouche à oreille'),
        ('walk_in', 'Visite directe'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('other', 'Autre'),
    ], string='Plateforme', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    color = fields.Integer(string='Couleur')

    campaign_ids = fields.One2many('marketing.campaign', 'lead_source_id', string='Campagnes')
    campaign_count = fields.Integer(string='Nb Campagnes', compute='_compute_campaign_count')

    def _compute_campaign_count(self):
        for rec in self:
            rec.campaign_count = len(rec.campaign_ids)