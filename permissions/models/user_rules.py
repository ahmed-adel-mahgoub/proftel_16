""" Initialize Rules """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class user_rules(models.Model):
    """
        Initialize Rules:
         -
    """
    _name = 'user.rules'
    _description = 'user_rules'

    name = fields.Char(required=True)

    company_ids = fields.Many2many(
        'res.company',
        string='Companies',
        required=True
    )
    department_ids = fields.Many2many(
        'hr.department',
        string='Departments',
        store=True
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        store=True
    )
    rules_id = fields.Many2many(
        'rules',
        store=True
    )
    app_module_id = fields.Many2many(
        'modules.rules',
    store = True
    )

    def action_sync_to_summary(self):
        """Sync data to employee rules summary"""
        summary_model = self.env['employee.rules.summary']
        summary_model.load_data()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Employee Rules Summary',
            'res_model': 'employee.rules.summary',
            'view_mode': 'tree,form',
            'target': 'current',
        }
