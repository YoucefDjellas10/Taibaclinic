from odoo import fields, models, api


class ContactRecord(models.Model):
    _name = 'contact.record'
    _description = 'list of contacts with patients'

    name = fields.Char(string='ID', readonly=True)
    patient = fields.Many2one('patients', string='Patient',required=True)
    type = fields.Selection([
        ('call', 'Call'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('whatsapp_call', 'Whatsapp call'),
        ('whatsapp_message', 'Whatsapp message'),
        ('facebook_call', 'Facebook Call'),
        ('facebook_message', 'Facebook Message'),
        ('instagram_call', 'Instagram Call'),
        ('instagram_message', 'Instagram Message'),
        ('tiktok_call', 'TikTok Call'),
        ('tiktok_message', 'TikTok Message'),
    ], string='Status', required=True, tracking=True)
    report = fields.Text(string='Report')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"App-{record.id}"
        return record
