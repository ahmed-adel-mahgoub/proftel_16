# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class test_api(models.Model):
    _name = 'test.api'
    name = fields.Char()
    test_integer = fields.Integer()

     # 5eb8a1fcc12fea01185494c9fb003e3bbc063052 test11
    # b2eeaa8940980f795d049f7901d8080be2292137 custom
    # fa48006ec9f2f2488aea74827498b88f219fbc40 test
    # @api.model
    # def get_data_from_api(self, _logger=None):
    #     url = "http://www.proftelgroup.com/v1/api/arduino/get"
    #
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()  # Raise an error for bad responses
    #         data = response.json()  # Parse the JSON response
    #         print(data)
    #         # return data  # Return the data or process it as needed
    #         # Assuming the data is a list of dictionaries
    #         for item in data:
    #
    #             self.create({
    #                 'name': item.get('name'),
    #                 'test_integer': item.get('test_integer'),
    #             })
    #         return True  # Indicate success
    #     except requests.exceptions.RequestException as e:
    #         # Handle exceptions (e.g., log the error)
    #         _logger.error(f"Error fetching data from API: {e}")
    #         return None

