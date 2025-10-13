# -*- coding: utf-8 -*-
{
    'name': "permissions",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr','hr_employee_sender_id','mobile__app'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/rules.xml',
        'views/user_ules.xml',
        'views/module_rules.xml',
        'views/employee_rules_views.xml',
        'views/company_subscription_views.xml',
        'views/company_manger_view.xml',
        'views/user_data_views.xml',
        'views/company_schadule.xml',
        'views/employee_inherit.xml',
        'views/zones.xml',
        'data/cron_data.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

}
