from odoo import models, fields


class ExpenseTypeRecord(models.Model):
    _name = 'expense.type.record'
    _description = 'expense type record'

    name = fields.Char(string='Name', translate=True)
