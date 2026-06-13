from odoo import fields, models, api


class LaboratoryList(models.Model):
    _name = 'laboratory.list'
    _description = 'laboratory list'

    name = fields.Char(string='Name')
    order_ids = fields.One2many('dental.lab.order', 'lab_id', string='Orders')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search(
            [('name', '=', 'DZD')], limit=1
        ),
    )
    total_orders = fields.Monetary(currency_field='currency_id', string='Total orders',
                                   compute='_compute_total_orders', store=True)
    total_paid = fields.Monetary(currency_field='currency_id', string='Total Paid',
                                 compute='_compute_total_paid', store=True)
    total_remaining = fields.Monetary(currency_field='currency_id', string='Total Remaining',
                                      compute='_compute_total_remaining', store=True)

    @api.depends('order_ids.amount_total')
    def _compute_total_orders(self):
        for record in self:
            total = sum(record.order_ids.mapped('amount_total'))
            record.total_orders = total

    @api.depends('order_ids.amount_paid')
    def _compute_total_paid(self):
        for record in self:
            total = sum(record.order_ids.mapped('amount_paid'))
            record.total_paid = total

    @api.depends('order_ids.amount_remaining')
    def _compute_total_remaining(self):
        for record in self:
            total = sum(record.order_ids.mapped('amount_remaining'))
            record.total_remaining = total
