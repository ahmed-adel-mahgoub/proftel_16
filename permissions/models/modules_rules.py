""" Initialize Rules """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class modules_rules(models.Model):
    """
        Initialize Rules:
         -
    """
    _name = 'modules.rules'
    _description = 'App Module'

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
        string='Admins',
        store=True
    )
    modules_ids = fields.Many2many('permissions')



