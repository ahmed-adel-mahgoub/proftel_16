from odoo import models, fields, api


class type(models.Model):
    _name = 'type'
    _inherit = 'mail.thread'
    _description = "type"

    name = fields.Char()