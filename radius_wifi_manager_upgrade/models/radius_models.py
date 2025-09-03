
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class RadiusCompany(models.Model):
    _name = "radius.company"
    _description = "RADIUS Company"
    name = fields.Char(required=True)
    res_company_id = fields.Many2one('res.company', string="Odoo Company")
    notes = fields.Text()

class RadiusAccessPoint(models.Model):
    _name = "radius.access.point"
    _description = "Access Point / NAS"
    name = fields.Char(required=True)
    shortname = fields.Char()
    nas_identifier = fields.Char(help="NAS-Identifier/Called-Station-Id")
    public_ip = fields.Char()
    company_id = fields.Many2one('radius.company', required=False)
    secret = fields.Char(help="Shared secret for this client")
    server_id = fields.Many2one('radius.server', required=True, string="RADIUS Server")

class RadiusCertificate(models.Model):
    _name = "radius.certificate"
    _description = "RADIUS Certificate"
    name = fields.Char(required=True)
    cert_type = fields.Selection([('server','Server'),('client','Client/AP')], required=True, default='client')
    company_id = fields.Many2one('radius.company')
    server_id = fields.Many2one('radius.server')
    cn = fields.Char(string="Common Name", required=True)
    valid_from = fields.Datetime(default=lambda self: fields.Datetime.now())
    valid_to = fields.Datetime()
    key_attachment_id = fields.Many2one('ir.attachment', string="Private Key")
    cert_attachment_id = fields.Many2one('ir.attachment', string="Certificate (PEM)")
    ca_attachment_id = fields.Many2one('ir.attachment', string="CA (PEM)")

class RadiusEvent(models.Model):
    _name = "radius.event"
    _description = "RADIUS Event"
    _order = "event_time desc"
    name = fields.Char()
    event_time = fields.Datetime(default=lambda self: fields.Datetime.now())
    event_type = fields.Selection([('auth','Auth'),('acct','Accounting'),('coa','CoA'),('system','System')], default='auth')
    username = fields.Char()
    company = fields.Char()
    ap = fields.Char()
    details = fields.Text()
    server_id = fields.Many2one('radius.server')
