# -*- coding: utf-8 -*-
{
    'name': "CheckAttendance",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "AHMED MAHGOUB",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_attendance'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/checkAttendance_root_menu.xml',
        'views/views.xml',
        'views/emp_inhiret.xml',

    ],
    'application' : True,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
