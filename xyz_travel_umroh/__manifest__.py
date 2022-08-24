# -*- coding: utf-8 -*-
{
    'name': "XYZ Travel Umroh",

    'summary': """
        Custom module for PT. XYZ Travel Umroh""",

    'description': """
        Module for management umroh
    """,

    'author': "Fadli Fatanah",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Travel Umroh',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'mrp', 'sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_travel_package.xml',
        'report/travel_package_report.xml',
        'views/views.xml',
        'views/action_view.xml',
        'views/menu_view.xml',
    ],
    # only loaded in demonstration mode
    'application': True,
}
