{
    'name': "Mobile_APP",

    'summary': """
    mobile app for tracking tasks
        """,

    'description': """
        this app will attach with other apps to tracking emloyees tasks
    """,

    'author': "Proftel",


    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'mail',
                'hr',
                'calendar',
                'wss_test',
                'project'
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/tracking_cron.xml',
        'views/views.xml',
        'views/task_veiw.xml',
        'views/templates.xml',
        'views/type_veiw.xml',
        'views/manger_veiw.xml',
        'views/hr_employee_inherit_veiw.xml',
        'views/task_history_veiw.xml',
        'views/cancel_reason_wizard_views.xml',
        'views/tracking_send_views.xml',
        'views/kind_view.xml',
        'views/company_type_view.xml',
        'views/reschadul_type.xml',
    ],

}
