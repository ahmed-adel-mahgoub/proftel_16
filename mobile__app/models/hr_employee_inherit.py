from odoo import models, fields, api
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    is_manger=fields.Boolean()
