# -*- coding: utf-8 -*-
{
    'name': "index_custom_cnam",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        EXTERNAL CNAM APP CUSTOM
    """,

    'author': "INDEX CONSULTING",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'edu_management', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/regrouping_views.xml',
        'views/exam_calandar_view.xml',
        'views/email_template.xml',
        'views/report.xml',
        'views/invoice_view.xml',
        'views/cron.xml',
        'views/sale_analysis.xml',
        'views/action_manager.xml',
        'views/wizard_view.xml',
        'wizard/xls_comparison.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
