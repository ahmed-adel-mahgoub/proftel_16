from odoo import models, fields, api

class EmployeeRulesSummary(models.TransientModel):
    _name = 'employee.rules.summary'
    _description = 'Employee Rules Summary'
    _log_access = True

    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    rule_ids = fields.Many2many('rules', string='Rules', readonly=True)

    def load_data(self):
        """Load data from user.rules model"""
        self.search([]).unlink()  # Clear existing data

        rules = self.env['user.rules'].search([])
        employee_dict = {}

        for rule in rules:
            for employee in rule.employee_ids:
                if employee.id not in employee_dict:
                    employee_dict[employee.id] = {
                        'employee_id': employee.id,
                        'company_id': employee.company_id.id,
                        'department_id': employee.department_id.id,
                        'rule_ids': set()
                    }
                employee_dict[employee.id]['rule_ids'].update(rule.rules_id.ids)

        for emp_id, values in employee_dict.items():
            self.create({
                'employee_id': emp_id,
                'company_id': values['company_id'],
                'department_id': values['department_id'],
                'rule_ids': [(6, 0, list(values['rule_ids']))]
            })
        return True

    @api.model
    def action_auto_load(self):
        """Auto load data when opening the view"""
        self.load_data()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Rules Summary',
            'res_model': 'employee.rules.summary',
            'view_mode': 'tree,form',
            'target': 'current',
        }