# -*- coding: utf-8 -*-

from odoo import models, fields, api


class company_manger(models.Model):
    _name = 'company.manger'
    _description = 'company_manger'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee',string="Manger")
    res_company_id = fields.Many2one(
        'res.company',
        string='company',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
    )
    email = fields.Char(related='employee_id.work_email')

