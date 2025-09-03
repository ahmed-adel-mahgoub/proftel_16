# -*- coding: utf-8 -*-

from odoo import models, fields, api


class company_manger(models.Model):
    _name = 'company.manger'
    _description = 'company_manger'

    name = fields.Char()
    res_company_id = fields.Many2one(
        'res.company'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Manger'
    )
    department_id = fields.Char(related='employee_id.department_id.name',
                                string='Department'
                                , readonly=True)
    email = fields.Char(related='employee_id.work_email')

