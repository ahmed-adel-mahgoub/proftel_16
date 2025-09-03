
from odoo import models, fields, api
from odoo.exceptions import UserError
import socket, struct, time

class RadiusSync(models.Model):
    _name = "radius.sync"
    _description = "RADIUS Sync & CoA utilities"

    name = fields.Char(default="Radius Sync Utility")

    def action_sync_radacct(self):
        """Sync radacct table into radius.event records. Assumes radacct exists in same DB."""
        cr = self.env.cr
        # Ensure radacct exists
        try:
            cr.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='radacct'")
            if cr.fetchone()[0] == 0:
                raise UserError('radacct table not found in DB. Ensure FreeRADIUS is configured to use this DB for accounting.')
        except Exception as e:
            raise UserError('Error checking radacct: %s' % e)
        # Fetch recent accounting rows (last 1000)
        cr.execute("SELECT acctsessionid, username, nasipaddress, acctstarttime, acctstoptime, acctterminatecause FROM radacct ORDER BY acctstarttime DESC LIMIT 1000")
        rows = cr.fetchall()
        created = 0
        for r in rows:
            acctsessionid, username, nasip, startt, stopt, term = r
            # check existence
            cr.execute("SELECT id FROM radius_event WHERE name=%s", (acctsessionid,))
            if cr.fetchone():
                continue
            vals = {
                'name': acctsessionid or f'acct-{int(time.time())}',
                'event_type': 'acct',
                'username': username,
                'ap': nasip,
                'details': f"stop={stopt} cause={term}",
            }
            self.env['radius.event'].create(vals)
            created += 1
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Sync complete','message':f'{created} events created','sticky':False}}

    def send_coa_disconnect(self, ip, secret, username):
        """Send CoA Disconnect-Request using pyrad if available, else raise error.
           This attempts a basic Disconnect-Request for a username to NAS IP on port 3799.
        """
        try:
            from pyrad.client import Client
            from pyrad.dictionary import Dictionary
            from pyrad.packet import Packet, AccessRequest
        except Exception as e:
            raise UserError("pyrad library required for CoA. Install with: pip3 install pyrad")
        srv = Client(server=ip, secret=secret.encode(), dict=Dictionary())
        try:
            req = srv.CreateCoAPacket(code=40)  # 40 = Disconnect-Request (CoA)
        except Exception:
            # fallback create packet
            req = srv.CreatePacket(code=40)
        # set attributes commonly used - NAS-IP-Address or NAS-Identifier may be required
        req['User-Name'] = username
        # send and don't wait long
        try:
            reply = srv.SendPacket(req)
            return reply
        except Exception as e:
            raise UserError(f"CoA send failed: {e}")

    def action_coa_disconnect_user(self, user_id):
        """Disconnect an online user by username using mapped AP info from radius.wifi.user or radius.access.point"""
        users = self.env['radius.wifi.user'].browse(user_id)
        if not users:
            raise UserError("User not found")
        for u in users:
            # find AP mapping via radius_ap_company_map or radius.access.point
            cr = self.env.cr
            # prefer AP record with company match
            ap = None
            if u.company_id:
                cr.execute("SELECT ap.name, ap.public_ip, ap.secret FROM radius_access_point ap WHERE ap.company_id=%s LIMIT 1", (u.company_id.id,))
                row = cr.fetchone()
                if row:
                    ap = {'name': row[0], 'ip': row[1], 'secret': row[2]}
            # fallback to any AP for server
            if not ap:
                cr.execute("SELECT name, public_ip, secret FROM radius_access_point WHERE server_id=%s LIMIT 1", (u.server_id.id,))
                row = cr.fetchone()
                if row:
                    ap = {'name': row[0], 'ip': row[1], 'secret': row[2]}
            if not ap or not ap.get('ip') or not ap.get('secret'):
                raise UserError("No AP with IP/secret found to send CoA")
            # send CoA
            self.send_coa_disconnect(ap['ip'], ap['secret'], u.name)
        return True
