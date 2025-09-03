""" Initialize Wan Ip """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class WanIp(models.Model):
    """
        Initialize Wan Ip:
         -
    """
    _name = 'wan.ip'
    _description = 'Wan Ip'

    name = fields.Char(
        required=True,
        translate=True,
    )
