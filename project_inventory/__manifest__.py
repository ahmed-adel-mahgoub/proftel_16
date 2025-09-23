{
    'name': 'Project Inventory Integration',
    'version': '16.0.1.0.0',
    'category': 'Project',
    'summary': 'Add inventory functionality to projects',
    'description': """
        
    """,
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'depends': ['base','project', 'stock','product'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/product_view.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}