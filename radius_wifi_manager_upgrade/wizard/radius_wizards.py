from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
try:
    import openpyxl
except Exception:
    openpyxl = None
import random, string

class RadiusImportWizard(models.TransientModel):
    _name = 'radius.import.wizard'
    _description = 'Import RADIUS users from Excel (.xlsx)'

    file = fields.Binary('Excel File (.xlsx)', required=True)
    filename = fields.Char('Filename')
    default_start = fields.Datetime('Default Start', default=fields.Datetime.now)
    default_end = fields.Datetime('Default End')

    def _build_password(self, first, last, idval):
        first = (first or '').strip()
        last = (last or '').strip()
        idstr = str(idval).strip()
        return f"{first[:4].lower()}{idstr}{(last[:1] or '').upper()}"

    def action_import(self):
        if openpyxl is None:
            raise UserError('openpyxl not installed on the server (pip3 install openpyxl)')
        data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(filename=None, data=data, read_only=True)
        ws = wb.active
        created = 0
        first_row = True
        for row in ws.iter_rows(values_only=True):
            if first_row:
                first_row = False
                continue
            first = row[0] or ''
            last = row[1] or ''
            idval = row[2] or ''
            comp = row[3] or False
            proj = row[4] or False
            ev = row[5] or False
            start = row[6] or self.default_start
            end = row[7] or self.default_end or fields.Datetime.add(self.default_start, days=7)

            username_base = f"{str(first).strip().lower()}.{str(last).strip().lower()}"
            username = username_base
            suffix = 1
            while self.env['radius.entry'].search_count([('radius_username','=',username)]):
                username = f"{username_base}{suffix}"
                suffix += 1

            password = self._build_password(first, last, idval)
            company = False
            project = False
            event = False
            if comp:
                company = self.env['res.partner'].search([('is_company','=',True),('name','=',str(comp).strip())], limit=1)
            if proj:
                project = self.env['project.project'].search([('name','=',str(proj).strip())], limit=1)
            if ev:
                event = self.env['event.event'].search([('name','=',str(ev).strip())], limit=1)

            rec = self.env['radius.entry'].create({
                'first_name': first,
                'last_name': last,
                'company_id': company.id if company else False,
                'project_id': project.id if project else False,
                'event_id': event.id if event else False,
                'radius_username': username,
                'radius_password': password,
                'start_time': start,
                'end_time': end,
                'active': True,
            })
            now = fields.Datetime.now()
            if rec.start_time <= now <= rec.end_time:
                try:
                    rec.action_push_to_radius()
                except Exception:
                    pass
            created += 1
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Import finished','message':f'Created {created} users','sticky':False}}


class RadiusRandomWizard(models.TransientModel):
    _name = 'radius.random.wizard'
    _description = 'Generate Random RADIUS Users'

    number = fields.Integer('Number of Users', required=True, default=1)
    start_time = fields.Datetime('Start Time', required=True, default=fields.Datetime.now)
    end_time = fields.Datetime('End Time', required=True)
    company_id = fields.Many2one('res.partner', string='Company', domain=[('is_company','=',True)])
    project_id = fields.Many2one('project.project', string='Project')
    event_id = fields.Many2one('event.event', string='Event')

    def _build_password(self, first, last, idval):
        first = (first or '').strip()
        last = (last or '').strip()
        idstr = str(idval).strip()
        return f"{first[:4].lower()}{idstr}{(last[:1] or '').upper()}"

    def action_generate(self):
        created = 0
        for i in range(max(0, int(self.number or 0))):
            first = ''.join(random.choices(string.ascii_lowercase, k=6))
            last = ''.join(random.choices(string.ascii_lowercase, k=6))
            idval = random.randint(1000, 99999)
            username_base = f"{first}.{last}"
            username = username_base
            suffix = 1
            while self.env['radius.entry'].search_count([('radius_username','=',username)]):
                username = f"{username_base}{suffix}"
                suffix += 1
            password = self._build_password(first, last, idval)
            rec = self.env['radius.entry'].create({
                'first_name': first,
                'last_name': last,
                'company_id': self.company_id.id if self.company_id else False,
                'project_id': self.project_id.id if self.project_id else False,
                'event_id': self.event_id.id if self.event_id else False,
                'radius_username': username,
                'radius_password': password,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'active': True,
            })
            now = fields.Datetime.now()
            try:
                if rec.start_time <= now <= rec.end_time:
                    rec.action_push_to_radius()
            except Exception:
                pass
            created += 1
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'Generation finished','message':f'Created {created} users','sticky':False}}
