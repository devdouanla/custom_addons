{
    'name': "production_boulangerie",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "Djouda douanla",
    'website': "https://www.yourcompany.com",
    'application':True,
    'license': 'LGPL-3',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','uom','product','stock'],

    # always loaded
    'data': [
    'security/groupe_secu.xml',
    'security/ir.model.access.csv',
    'views/custom_login/login_templates.xml',
    'views/utils/sequence_views.xml',
    'views/bakery_product_views.xml',
    'views/production_views.xml',
    'views/production_day_views.xml',
    'views/type_production_views.xml',
    'views/raw_material_views.xml',
    'views/production_dashboard_views.xml',
    'views/menu.xml',

    #'views/menu_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    #  assets 
    'assets': {
        'web.assets_frontend': [
            'production_boulangerie/static/src/scss/login.scss',
        ],
    },
}

