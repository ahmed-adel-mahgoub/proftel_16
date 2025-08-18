from odoo import models, fields, api
class manger(models.Model):
    _name = 'company.type'

    name = fields.Char()
