from werkzeug.exceptions import BadRequest
from odoo import models
from odoo.http import request
class ApiHttp(models.AbstractModel):
    _inherit = "ir.http"

    # e12b545695b7bd0c8800ea727975235e54253df0
    @classmethod
    def _auth_method_custom_auth(cls):
        access_token =request.httprequest.headers.get('Authorization')
        if not access_token :
            raise BadRequest("Access Token Messing")
        if access_token.startswith('Bearer '):
            access_token=access_token[7:]
        user_id= request.env["res.users.apikeys"]._check_credentials(scope='odoo.restapi',key=access_token)
        if not user_id:
            raise BadRequest("Access Token Messing")
        request.update_env(user=user_id)