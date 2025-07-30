{
    'name': 'Employee Sender ID',
    'version': '1.0',
    'summary': 'Adds sender ID to employees',
    'description': 'Adds an auto-incrementing sender ID field to employees',
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr'],
    'data': [
        'data/sequence_data.xml',
        'views/views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
