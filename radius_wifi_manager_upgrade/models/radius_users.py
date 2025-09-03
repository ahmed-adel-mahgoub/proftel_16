
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import random, string

class RadiusWifiUser(models.Model):
    _name = "radius.wifi.user"
    _description = "RADIUS WiFi User"
    _order = "id desc"

    name = fields.Char(string="Username", required=True)
    password = fields.Char(string="Password", required=True)
    company_id = fields.Many2one('radius.company', string="Company")
    server_id = fields.Many2one('radius.server', string="RADIUS Server", required=True)
    start_time = fields.Datetime(string="Start Time", default=lambda self: fields.Datetime.now())
    end_time = fields.Datetime(string="End Time")
    pushed = fields.Boolean(string="Pushed to RADIUS", default=False)
    note = fields.Text()

    @api.model
    def _generate_password(self, first_name, last_name, the_id):
        # Password rule: first 4 letters of first name + ID full + first letter of last name uppercase
        fn = (first_name or "")[:4]
        ln = (last_name or "")[:1].upper() if last_name else ""
        return f"{fn}{the_id}{ln}"

    @api.model
    def generate_random_users(self, server_id, company_id=None, count=10, first_name_prefix="User", last_name="L"):
        server = self.env['radius.server'].browse(server_id)
        if not server:
            raise UserError("Server not found")
        created = []
        for i in range(count):
            uid = f"{first_name_prefix.lower()}{random.randint(1000,9999)}{i}"
            pwd = self._generate_password(first_name_prefix, last_name, uid)
            rec = self.create({
                'name': uid,
                'password': pwd,
                'company_id': company_id,
                'server_id': server_id,
                'start_time': fields.Datetime.now(),
                'end_time': fields.Datetime.to_string(fields.Datetime.add(fields.Datetime.now(), days=1))
            })
            created.append(rec)
        return created

    def push_batch_to_radius(self):
        # Push selected users to the radcheck table using Odoo DB (same Postgres)
        for rec in self:
            if not rec.server_id:
                raise UserError("User %s has no server assigned" % rec.name)
            server = rec.server_id
            # Use current DB cursor for same-DB insertion
            cr = self.env.cr
            # Ensure radcheck exists
            try:
                cr.execute(
                    "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s,'Cleartext-Password',':=',%s) "
                    "ON CONFLICT (username, attribute) DO UPDATE SET value = EXCLUDED.value",
                    (rec.name, rec.password)
                )
                # Optionally add radreply entries for session timeout using end_time
                if rec.end_time:
                    # compute seconds for Session-Timeout
                    try:
                        dt_end = fields.Datetime.from_string(rec.end_time)
                        dt_start = fields.Datetime.from_string(rec.start_time or fields.Datetime.now())
                        timeout = int((dt_end - dt_start).total_seconds())
                        cr.execute("DELETE FROM radreply WHERE username=%s AND attribute='Session-Timeout'", (rec.name,))
                        cr.execute("INSERT INTO radreply (username, attribute, op, value) VALUES (%s,'Session-Timeout',':=',%s)", (rec.name, str(timeout)))
                    except Exception:
                        pass
                # mark pushed
                rec.pushed = True
            except Exception as e:
                raise UserError("Failed to push user %s to RADIUS: %s" % (rec.name, e))

    def action_delete_from_radius(self):
        for rec in self:
            cr = self.env.cr
            cr.execute("DELETE FROM radreply WHERE username=%s", (rec.name,))
            cr.execute("DELETE FROM radusergroup WHERE username=%s", (rec.name,))
            cr.execute("DELETE FROM radcheck WHERE username=%s", (rec.name,))
            rec.pushed = False

    def extend_time(self, extra_minutes=60):
        for rec in self:
            if not rec.end_time:
                rec.end_time = fields.Datetime.to_string(fields.Datetime.add(fields.Datetime.now(), minutes=extra_minutes))
            else:
                prev = fields.Datetime.from_string(rec.end_time)
                rec.end_time = fields.Datetime.to_string(prev + timedelta(minutes=extra_minutes))
            # If already pushed, update radreply Session-Timeout
            if rec.pushed:
                cr = self.env.cr
                try:
                    dt_end = fields.Datetime.from_string(rec.end_time)
                    dt_start = fields.Datetime.from_string(rec.start_time or fields.Datetime.now())
                    timeout = int((dt_end - dt_start).total_seconds())
                    cr.execute("DELETE FROM radreply WHERE username=%s AND attribute='Session-Timeout'", (rec.name,))
                    cr.execute("INSERT INTO radreply (username, attribute, op, value) VALUES (%s,'Session-Timeout',':=',%s)", (rec.name, str(timeout)))
                except Exception as e:
                    raise UserError(f"Failed to update Session-Timeout: {e}")


    def action_disconnect_coa(self):
        # call radius.sync to perform CoA disconnect for these users
        sync = self.env['radius.sync'].create({})
        for u in self:
            sync.action_coa_disconnect_user(u.id)
        return True
