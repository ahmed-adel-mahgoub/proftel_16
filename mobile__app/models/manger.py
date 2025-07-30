from odoo import models, fields, api
class manger(models.Model):
    _name = 'manger'
    _inherit = 'mail.thread'
    _description = "manger"
    name = fields.Char()
    order_by_id = fields.Many2one("hr.employee", string="Order By")