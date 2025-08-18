{
    'name': 'Task Websocket Notifications',
    'version': '1.0',
    'summary': 'Websocket notifications for tasks',
    'description': 'Real-time task notifications via websocket',
    'author': 'Your Name',
    'depends': ['base', 'hr', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'external_dependencies': {
        'python': ['websockets'],
    },
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
