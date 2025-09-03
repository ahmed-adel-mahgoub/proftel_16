{
    'name': 'RADIUS Manager Full',
    'version': '16.0.1.0.0',
    'summary': 'Manage RADIUS users with Excel import, random generation, company/project/event links and cleanup',
    'description': 'Create/manage RADIUS users. Password rule: first4(lower)+ID+LastInitial(Upper). Import from Excel, generate random users, auto-clean expired users. Compatible with Odoo 16.',
    'category': 'Tools',
    'author': 'Custom',
    'depends': ['base', 'project', 'event'],
    'data': [
        'security/ir.model.access.csv',
        'views/radius_entry_view.xml',
        'views/radius_request_view.xml',
        'views/radius_server.xml',
        'views/radius_sync.xml',
        'views/radius_wifi_user.xml',
        'wizard/radius_wizards_views.xml',
        'data/cron_job.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
