""" Initialize Rules """

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, Warning


class modules_rules(models.Model):
    """
        Initialize Rules:
         -
    """
    _name = 'modules.rules'
    _description = 'App Module'

    name = fields.Char(required=True)

    company_ids = fields.Many2many(
        'res.company',
        string='Companies',
        required=True
    )
    department_ids = fields.Many2many(
        'hr.department',
        string='Departments',
        store=True
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Admins',
        store=True
    )
    employee_details = fields.Html(string='Employee Details',
                                   compute='_compute_employee_details')

    @api.depends('employee_ids')
    def _compute_employee_details(self):
        for record in self:
            if record.employee_ids:
                html_content = """
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Employee</th>
                            <th>Department</th>
                            <th>Company</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                for employee in record.employee_ids:
                    html_content += f"""
                    <tr>
                        <td>{employee.name}</td>
                        <td>{employee.department_id.name if employee.department_id else 'No Department'}</td>
                        <td>{employee.company_id.name if employee.company_id else 'No Company'}</td>
                    </tr>
                    """

                html_content += """
                    </tbody>
                </table>
                """
                record.employee_details = html_content
            else:
                record.employee_details = "<p>No employees selected</p>"
