from odoo import models, fields, api, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sender_id = fields.Char(string='Sender ID', readonly=True, copy=False, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('sender_id'):
                vals['sender_id'] = self.env['ir.sequence'].next_by_code('hr.employee.sender.id') or _('New')
        return super(HrEmployee, self).create(vals_list)

    def action_generate_sender_id(self):
        """Generate a sender ID for employees missing one"""
        for employee in self:
            if not employee.sender_id:
                employee.sender_id = self.env['ir.sequence'].next_by_code('hr.employee.sender.id') or _('New')
