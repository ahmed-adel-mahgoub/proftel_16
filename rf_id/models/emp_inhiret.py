from odoo import models, fields, api
class emp_inherit(models.Model):
    _inherit = 'hr.employee'

    rf_id = fields.Char()
    x_app_username = fields.Char()