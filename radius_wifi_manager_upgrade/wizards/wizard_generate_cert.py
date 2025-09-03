
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import base64

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
except Exception:
    x509 = None

class WizardGenerateCert(models.TransientModel):
    _name = "wizard.radius.generate.cert"
    _description = "Generate RADIUS Certificate"

    cert_type = fields.Selection([('server','Server'),('client','Client/AP')], default='client', required=True)
    cn = fields.Char(required=True, string="Common Name")
    days = fields.Integer(default=1095)
    company_id = fields.Many2one('radius.company')
    server_id = fields.Many2one('radius.server', required=True)

    def action_generate(self):
        if x509 is None:
            raise UserError("cryptography library is required on Odoo server. pip install cryptography")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, self.cn)])
        cert = (x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.utcnow())
                .not_valid_after(datetime.utcnow() + timedelta(days=self.days))
                .add_extension(x509.BasicConstraints(ca=(self.cert_type=='server'), path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
        key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        key_attach = self.env['ir.attachment'].create({
            'name': f"{self.cn}.key",
            'datas': base64.b64encode(key_pem),
            'res_model': 'radius.certificate',
            'type': 'binary',
            'mimetype': 'application/x-pem-file',
        })
        cert_attach = self.env['ir.attachment'].create({
            'name': f"{self.cn}.pem",
            'datas': base64.b64encode(cert_pem),
            'res_model': 'radius.certificate',
            'type': 'binary',
            'mimetype': 'application/x-pem-file',
        })
        rec = self.env['radius.certificate'].create({
            'name': self.cn,
            'cert_type': self.cert_type,
            'cn': self.cn,
            'valid_to': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=self.days)),
            'key_attachment_id': key_attach.id,
            'cert_attachment_id': cert_attach.id,
            'company_id': self.company_id.id,
            'server_id': self.server_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'radius.certificate',
            'res_id': rec.id,
            'view_mode': 'form',
            'target': 'current',
        }
