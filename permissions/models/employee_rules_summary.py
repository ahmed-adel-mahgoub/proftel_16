from odoo import models, fields, api

class EmployeeRulesSummary(models.TransientModel):
    _name = 'employee.rules.summary'
    _description = 'Employee Rules Summary'


    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    rule_ids = fields.Many2many('rules', string='Rules', readonly=True)

