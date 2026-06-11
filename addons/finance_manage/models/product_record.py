from odoo import models, fields, api


class ProductRecord(models.Model):
    _name = "product.record"
    _description = "product list"

    name = fields.Char(string='Name', required=True)
    remaining_qt = fields.Integer(string='Remaining Qt')
    min = fields.Integer(string='Minimum must be')
    purchase_ids = fields.Many2many('purchase.order.record')
    appointment_ids = fields.Many2many('appointment.record')
    availability = fields.Selection([
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ], string='Availability', compute='_compute_availability', store=True)
    category_id = fields.Many2one(
        'product.category.record',
        string='Category'
    )

    @api.depends('remaining_qt', 'min')
    def _compute_availability(self):
        for record in self:
            if record.remaining_qt <= 0:
                record.availability = 'out_of_stock'
            elif record.remaining_qt <= record.min:
                record.availability = 'low_stock'
            else:
                record.availability = 'available'


class ProductCategory(models.Model):
    _name = "product.category.record"
    _description = "Product Category"

    name = fields.Char(string='Category Name', required=True)
