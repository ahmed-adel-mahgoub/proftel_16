from email.policy import default
import requests
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    user_id = fields.Many2one('res.users', string='User ', ondelete='set null')
    x_app_password = fields.Char()
    x_app_username =fields.Char()
    update_api = fields.Boolean()
    # call this button in view
    @api.model
    def get_data_from_api_employee(self, _logger=None):
          url = "http://172.16.13.150:8069/api/update_records/employee"
          try:
               response = requests.get(url)
               response.raise_for_status()  # Raise an error for bad responses
               data = response.json()  # Parse the JSON response
               print(data)
               # return data  # Return the data or process it as needed
               # Assuming the data is a list of dictionaries
               for item in data:
                    self.create({
                         'name': item.get('name'),
                         'work_email': item.get('work_email'),
                    })
               return True  # Indicate success
          except requests.exceptions.RequestException as e:
               # Handle exceptions (e.g., log the error)
               _logger.error(f"Error fetching data from API: {e}")
               return None



