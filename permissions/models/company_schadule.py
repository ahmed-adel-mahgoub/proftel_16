""" Initialize Company Schedule """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CompanySchedule(models.Model):
    """
    Initialize Company Schedule:
    - Manages company working schedules with days and time ranges
    """
    _name = 'company.schedule'
    _description = 'Company Schedule'

    name = fields.Char(required=True)

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    sunday = fields.Boolean()
    monday = fields.Boolean()
    tuesday = fields.Boolean()
    wednesday = fields.Boolean()
    thursday = fields.Boolean()
    friday = fields.Boolean()
    saturday = fields.Boolean()
    alldays = fields.Boolean(string="All Days")
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)

    @api.onchange('alldays')
    def _onchange_alldays(self):
        """
        When 'All Days' is selected, automatically check all day checkboxes
        When deselected, uncheck all day checkboxes
        """
        for record in self:
            if record.alldays:
                record.sunday = True
                record.monday = True
                record.tuesday = True
                record.wednesday = True
                record.thursday = True
                record.friday = True
                record.saturday = True
            else:
                # Only uncheck if all were previously checked (to avoid losing manual selections)
                if (record.sunday and record.monday and record.tuesday and
                        record.wednesday and record.thursday and record.friday and record.saturday):
                    record.sunday = False
                    record.monday = False
                    record.tuesday = False
                    record.wednesday = False
                    record.thursday = False
                    record.friday = False
                    record.saturday = False

    @api.onchange('sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
                  'friday', 'saturday')
    def _onchange_days(self):
        """
        Automatically check/uncheck 'All Days' based on individual day selections
        """
        for record in self:
            if (record.sunday and record.monday and record.tuesday and
                    record.wednesday and record.thursday and record.friday and record.saturday):
                record.alldays = True
            else:
                record.alldays = False

    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        """
        Validate that:
        1. Start time is before end time
        2. Time range doesn't exceed 24 hours
        3. Times are within valid range (0-24)
        """
        for record in self:
            if record.start_time < 0 or record.start_time > 24:
                raise ValidationError(
                    _("Start time must be between 0 and 24 hours."))

            if record.end_time < 0 or record.end_time > 24:
                raise ValidationError(
                    _("End time must be between 0 and 24 hours."))

            if record.start_time >= record.end_time:
                raise ValidationError(_("Start time must be before end time."))

            # Check if time range exceeds 24 hours
            time_difference = record.end_time - record.start_time
            if time_difference > 24:
                raise ValidationError(_("Time range cannot exceed 24 hours."))

    @api.constrains('sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
                    'friday', 'saturday')
    def _check_at_least_one_day(self):
        """
        Validate that at least one day is selected
        """
        for record in self:
            if not (record.sunday or record.monday or record.tuesday or
                    record.wednesday or record.thursday or record.friday or
                    record.saturday):
                raise ValidationError(_("At least one day must be selected."))

    def get_working_days(self):
        """
        Return a list of selected working days
        """
        self.ensure_one()
        days = []
        if self.sunday: days.append('sunday')
        if self.monday: days.append('monday')
        if self.tuesday: days.append('tuesday')
        if self.wednesday: days.append('wednesday')
        if self.thursday: days.append('thursday')
        if self.friday: days.append('friday')
        if self.saturday: days.append('saturday')
        return days

    def is_working_day(self, day_name):
        """
        Check if a specific day is a working day
        :param day_name: string representing day (e.g., 'monday', 'tuesday')
        :return: boolean
        """
        self.ensure_one()
        day_mapping = {
            'sunday': self.sunday,
            'monday': self.monday,
            'tuesday': self.tuesday,
            'wednesday': self.wednesday,
            'thursday': self.thursday,
            'friday': self.friday,
            'saturday': self.saturday
        }
        return day_mapping.get(day_name.lower(), False)
