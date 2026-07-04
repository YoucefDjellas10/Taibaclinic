from odoo import api, fields, models


class AccessManage(models.Model):
    _name = 'access.manage'
    _description = 'Access Manage'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='Phone Number')
    password = fields.Char(string='Password')
    group_list = fields.Many2many(
        'res.groups',
        string='Groups',
        domain=[('name', 'in', ['CEO', 'ADMIN', 'RECEPTION', 'DOCTOR', 'SALESPERSON'])],
    )
    user_id = fields.Many2one('res.users', string='Linked User', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        internal_user_group = self.env.ref('base.group_user')
        for record, vals in zip(records, vals_list):
            if vals.get('user_id'):
                # already linked to an existing real user (e.g. via the sync action), don't create a new one
                continue
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.name,
                'email': record.email,
                'phone': record.phone_number,
                'password': record.password,
                'group_ids': [(6, 0, (record.group_list | internal_user_group).ids)],
            })
            record.user_id = user
        return records

    def write(self, vals):
        res = super().write(vals)
        internal_user_group = self.env.ref('base.group_user')
        for record in self:
            if not record.user_id:
                continue
            user_vals = {}
            if 'name' in vals:
                user_vals['name'] = record.name
                user_vals['login'] = record.name
            if 'email' in vals:
                user_vals['email'] = record.email
            if 'phone_number' in vals:
                user_vals['phone'] = record.phone_number
            if 'password' in vals:
                user_vals['password'] = record.password
            if 'group_list' in vals:
                user_vals['group_ids'] = [(6, 0, (record.group_list | internal_user_group).ids)]
            if user_vals:
                record.user_id.write(user_vals)
        return res

    def unlink(self):
        users = self.mapped('user_id')
        res = super().unlink()
        users.unlink()
        return res

    def action_sync_missing_users(self):
        linked_user_ids = self.search([]).mapped('user_id').ids
        known_groups = self.env['res.groups'].search([
            ('name', 'in', ['CEO', 'ADMIN', 'RECEPTION', 'DOCTOR', 'SALESPERSON']),
        ])
        missing_users = self.env['res.users'].search([
            ('id', 'not in', linked_user_ids),
            ('share', '=', False),
        ])
        vals_list = [{
            'name': user.login,
            'email': user.email,
            'phone_number': user.phone,
            'group_list': [(6, 0, (user.group_ids & known_groups).ids)],
            'user_id': user.id,
        } for user in missing_users]
        if vals_list:
            self.create(vals_list)
