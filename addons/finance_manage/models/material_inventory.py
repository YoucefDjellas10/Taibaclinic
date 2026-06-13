from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MaterialInventory(models.Model):
    _name = "material.inventory"
    _description = "Material Inventory"

    name = fields.Char(string='Name', required=True)
    reference = fields.Char(string='Reference', readonly=True)
    category = fields.Selection([
        ('raw', 'Raw Material'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ], string='Category', default='raw', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    price_history_ids = fields.One2many(
        'material.price.history', 'material_id', string='Price History'
    )

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.reference = f"MAT-{record.id}"
        return record


class MaterialPriceHistory(models.Model):
    _name = "material.price.history"
    _description = "Material Price History"
    _order = "date desc"

    material_id = fields.Many2one(
        'material.inventory', string='Material', required=True, ondelete='cascade'
    )
    currency = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.ref('base.DZD')
    )
    price = fields.Monetary(currency_field='currency', string='Price')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    note = fields.Text(string='Note')

    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if record.price <= 0:
                raise ValidationError("The price must be greater than 0.")