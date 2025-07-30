from odoo import models, fields, api
import json
import html


class SmartInventory(models.Model):
    _name = 'smart.inventory'
    name = fields.Text()
    Qyt = fields.Integer()
    type = fields.Text()
    location = fields.Text()
    owner = fields.Text()
    category = fields.Text()
    condition = fields.Text()
    _image_path = fields.Text(string="Image Paths")  # JSON list
    _user_name = fields.Text()
    _user_id = fields.Integer()
    RF_ID = fields.Text()
    image_links_html = fields.Html(string="Image Links", compute="_compute_image_links_html", sanitize=False)

    @api.depends('_image_path')
    def _compute_image_links_html(self):
        for rec in self:
            try:
                urls = json.loads(rec._image_path or "[]")
                links = []
                for url in urls:
                    safe_url = html.escape(url)
                    links.append(f'<a href="{safe_url}" target="_blank">{safe_url}</a>')
                rec.image_links_html = "<br/>".join(links)
            except Exception:
                rec.image_links_html = ""

    # Custom getter and setter
    @property
    def image_path(self):
        try:
            return json.loads(self._image_path or "[]")
        except Exception:
            return []

    @image_path.setter
    def image_path(self, value):
        if isinstance(value, list):
            self._image_path = json.dumps(value)
        elif isinstance(value, str):
            try:
                json.loads(value)
                self._image_path = value
            except Exception:
                raise ValueError("image_path must be a valid JSON list or list of strings")
        else:
            raise ValueError("image_path must be a list or a JSON string")


    @property
    def user_id(self):
        try:
            return self.user_id
        except Exception:
            return ""

    @user_id.setter
    def user_id(self, value):
        try:
            if isinstance(value, int):
                self.user_id = value
            else:
                raise ValueError("user_id must be a numeric value")
        except Exception:
            raise ValueError("user_id must be a numeric value")

    @property
    def user_name(self):
        try:
            return self.user_name
        except Exception:
            return ""


    @user_name.setter
    def user_name(self, value):
        try:
            if isinstance(value, str):
                self.user_name = value
            else:
                raise ValueError("user_name must be a str ")
        except Exception:
            raise ValueError("user_name must be a str")