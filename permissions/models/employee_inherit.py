from odoo import models, fields, api


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    user_rules_ids = fields.Many2many(
        'user.rules',
        string='User Rules',
        compute='_compute_user_rules_ids',
        store=True,
        readonly=True
    )
    role_admin = fields.Boolean()
    role_user = fields.Boolean()

    @api.depends('department_id', 'company_id')
    def _compute_user_rules_ids(self):
        for employee in self:
            # Find all rules that match this employee's department and company
            domain = [
                ('department_ids', 'in', employee.department_id.id),
                ('company_ids', 'in', employee.company_id.id),
            ]

            rules = self.env['user.rules'].search(domain)
            employee.user_rules_ids = rules