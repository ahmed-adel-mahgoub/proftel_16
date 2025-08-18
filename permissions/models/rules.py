""" Initialize Rules """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class Rules(models.Model):
    """
        Initialize Rules:
         -
    """
    _name = 'rules'
    _description = 'Rules'

    name = fields.Char(required=True)
    http_read = fields.Boolean(string="Read")
    http_write = fields.Boolean(string="Write")
    http_update = fields.Boolean(string="Update")
    http_delete = fields.Boolean(string="Delete")
    http_select_all = fields.Boolean(string="Select All")

    ws_read = fields.Boolean(string="Read")
    ws_write = fields.Boolean(string="Write")
    ws_update = fields.Boolean(string="Update")
    ws_delete = fields.Boolean(string="Delete")
    ws_select_all = fields.Boolean(string="Select All")

    @api.onchange('http_select_all')
    def _onchange_http_select_all(self):
        for rec in self:
            if rec.http_select_all:
                rec.http_read = True
                rec.http_write = True
                rec.http_update = True
                rec.http_delete = True
            else:
                rec.http_read = False
                rec.http_write = False
                rec.http_update = False
                rec.http_delete = False

    @api.onchange('ws_select_all')
    def _onchange_ws_select_all(self):
        for rec in self:
            if rec.ws_select_all:
                rec.ws_read = True
                rec.ws_write = True
                rec.ws_update = True
                rec.ws_delete = True
            else:
                rec.ws_read = False
                rec.ws_write = False
                rec.ws_update = False
                rec.ws_delete = False