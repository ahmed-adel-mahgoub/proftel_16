
from odoo import models, fields, api
from odoo.exceptions import UserError
import subprocess, shlex, psycopg2, socket, json

class RadiusServer(models.Model):
    _name = "radius.server"
    _description = "FreeRADIUS Server"

    name = fields.Char(required=True)
    host = fields.Char(string="Server Host/IP", required=True)
    api_type = fields.Selection([('systemd','systemd (local)'),('ssh','SSH remote')], default='systemd', required=True)
    systemd_service = fields.Char(default="freeradius")
    ssh_user = fields.Char()
    ssh_port = fields.Integer(default=22)
    ssh_key_path = fields.Char(help="Path on Odoo server to private key for SSH")
    allow_systemctl = fields.Boolean(default=False, help="If True, Odoo will attempt to run systemctl. Configure sudoers.")
    # PostgreSQL radius DB connection
    pg_host = fields.Char(default="localhost")
    pg_port = fields.Integer(default=5432)
    pg_db = fields.Char(string="Radius DB", default="radius")
    pg_user = fields.Char(default="radius_user")
    pg_password = fields.Char()
    pg_sslmode = fields.Selection([('disable','disable'),('require','require')], default='disable')
    connection_ok = fields.Boolean(compute="_compute_connection_ok", store=False)
    notes = fields.Text()

    def _pg_conn(self):
        self.ensure_one()
        try:
            conn = psycopg2.connect(
                host=self.pg_host, port=self.pg_port, dbname=self.pg_db,
                user=self.pg_user, password=self.pg_password,
                sslmode=self.pg_sslmode
            )
            conn.autocommit = True
            return conn
        except Exception as e:
            raise UserError(f"PostgreSQL connection failed: {e}")

    @api.depends('pg_host','pg_port','pg_db','pg_user','pg_password')
    def _compute_connection_ok(self):
        for rec in self:
            try:
                conn = psycopg2.connect(
                    host=rec.pg_host, port=rec.pg_port, dbname=rec.pg_db,
                    user=rec.pg_user, password=rec.pg_password,
                    sslmode=rec.pg_sslmode
                )
                conn.close()
                rec.connection_ok = True
            except Exception:
                rec.connection_ok = False

    def action_systemctl(self, command):
        self.ensure_one()
        if not self.allow_systemctl:
            raise UserError("Systemctl not allowed. Enable 'allow_systemctl' and configure sudoers for odoo.")
        cmd = f"sudo systemctl {command} {shlex.quote(self.systemd_service)}"
        try:
            out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=20)
            return {'type': 'ir.actions.client','tag':'display_notification','params':{'title':'systemctl','message':out.decode(errors='ignore'),'sticky':False}}
        except subprocess.CalledProcessError as e:
            raise UserError(f"systemctl error: {e.output.decode(errors='ignore')}")

    def action_restart(self): return self.action_systemctl("restart")
    def action_start(self): return self.action_systemctl("start")
    def action_stop(self): return self.action_systemctl("stop")

    # Basic radcheck/radreply operations
    def sql_upsert_radcheck(self, username, password):
        self.ensure_one()
        q = """INSERT INTO radcheck (username, attribute, op, value)
               VALUES (%s,'Cleartext-Password',':=',%s)
               ON CONFLICT ON CONSTRAINT radcheck_username_attribute_op_key
               DO UPDATE SET value = EXCLUDED.value"""
        try:
            conn = self._pg_conn()
            with conn.cursor() as cur:
                try:
                    cur.execute(q, (username, password))
                except Exception:
                    # Fallback if constraint doesn't exist
                    cur.execute("DELETE FROM radcheck WHERE username=%s AND attribute='Cleartext-Password'", (username,))
                    cur.execute("INSERT INTO radcheck (username, attribute, op, value) VALUES (%s,'Cleartext-Password',':=',%s)", (username, password))
        except Exception as e:
            raise UserError(f"radcheck upsert failed: {e}")

    def sql_delete_user(self, username):
        self.ensure_one()
        conn = self._pg_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM radreply WHERE username=%s", (username,))
            cur.execute("DELETE FROM radusergroup WHERE username=%s", (username,))
            cur.execute("DELETE FROM radcheck WHERE username=%s", (username,))


    # def generate_company_rule(self, ap_nas_identifier, company_id, reply_attributes=None):
    #     '''Create mapping rule so that users connecting from AP with nas_identifier are mapped to company.
    #        This will create or update an entry in a helper table `radius_ap_company_map` (created here if missing).
    #     '''
    #     self.ensure_one()
    #     cr = self.env.cr
    #     # create helper table if not exists
    #     cr.execute(\"\"\"
    #     CREATE TABLE IF NOT EXISTS radius_ap_company_map (
    #         id serial PRIMARY KEY,
    #         nas_identifier varchar,
    #         company_id integer
    #     )\"\"\")
    #     # upsert mapping
    #     cr.execute(\"\"\"
    #         INSERT INTO radius_ap_company_map (nas_identifier, company_id)
    #         VALUES (%s,%s)
    #         ON CONFLICT (nas_identifier) DO UPDATE SET company_id = EXCLUDED.company_id
    #     \"\"\", (ap_nas_identifier, company_id))
    #     # Optionally write a radreply rule for the AP (not required here)
    #     return True
