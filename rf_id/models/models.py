# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RfId(models.Model):
    _name = 'rf.id'
    _description = 'rf_id'

    name = fields.Char()
    category = fields.Selection([
        ("employee","Employee"),("door","Door"),
    ])
    employee_id =fields.Many2one('hr.employee')
    door_id  = fields.Many2one('lock.door')

    def update_rf_field(self):
        for rec in self:
            if rec.category == 'employee' and rec.employee_id:
                # Find the employee record using the employee_id
                employee = self.env['hr.employee'].search([('id', '=', rec.employee_id.id)], limit=1)
                if employee:
                    # Prepare the values to update
                    amounts_vals = {
                        'rf_id': rec.name,  # Update the 'rf' field with the name of rf.id
                    }
                    # Update the employee record
                    employee.write(amounts_vals)

    def update_rf_door(self):
        for rec in self:
            if rec.category == 'door' and rec.door_id:
                # Find the door record using the door_id field
                door = self.env['lock.door'].search([('id', '=', rec.door_id.id)], limit=1)
                if door:
                    # Prepare the values to update
                    amounts_vals = {
                        'rf_id': rec.name,  # Update the 'rf_id' field with the name of rf.id
                    }
                    # Update the door record
                    door.write(amounts_vals)


