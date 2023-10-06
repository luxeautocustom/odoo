# -*- coding: utf-8 -*-
{
    'name': "Project task check list",
    'summary': """
        Project Task Check List
        Develop by Magenest JSC""",
    'description': """
        Project task check list
    """,
    'author': "Magenest",
    'website': "http://www.magenest.com",
    'category': 'Extra Tools',
    'version': '0.1',
    'license': 'OPL-1',
    'depends': ['base', 'project'],
    'images': ['static/images/0.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_task.xml',
    ],
}
