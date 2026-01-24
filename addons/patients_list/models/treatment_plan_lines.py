from odoo import fields, models, api


class TreatmentPlan(models.Model):
    _name = 'treatment.plan.lines'
    _description = 'lines plan of patients treatments'

    name = fields.Char(string='ID', readonly=True)
    plan = fields.Many2one('treatment.plan', string='Deal')
    treatment = fields.Many2one('treatments', string='Treatment')
    quantity = fields.Integer(string='Qte', default="1")
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    price = fields.Monetary(string='Price', currency_field='currency', related='treatment.price')
    total = fields.Monetary(string='Total', currency_field='currency', compute='computed_total')
    teeth = fields.Many2many('teeth', string='Teeth')

    @api.depends('price', 'quantity')
    def computed_total(self):
        for record in self:
            record.total = record.price * record.quantity

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"Quota-{record.id}"
        return record
