
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Zones(models.Model):
    """
        Initialize Zones:
         -
    """
    _name = 'zones'
    _description = 'Zones'

    name = fields.Char()
    description = fields.Char()
    note = fields.Char()
    regions = fields.Char()
    countries = fields.Char()
    cities = fields.Char()
    company_ids = fields.Many2many(
        'res.company'
    )
    polygon_points = fields.Json(string="Polygon Points")
