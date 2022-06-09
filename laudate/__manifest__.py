# -*- coding: utf-8 -*-
{
    'name': "laudate",

    'summary': """
        Customization Laudate""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Oxilia-info",
    'website': "https://oxilia-info.fr",

    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','point_of_sale', 'odoo_multi_channel_sale', 'stock'],

    # always loaded
    'data': [
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        # 'views
        'views/pos_templates.xml',
        'views/pos_payment_method_views.xml',
        'views/sale_order_view.xml',
        'views/report_invoice_document.xml',
        'views/product_pricelist_views.xml',
        'views/product_views.xml',
        'views/gold_price_views.xml',
        # report
        'report/product_product_templates.xml',
        'report/purchase_order_templates.xml',
        'report/stock_picking_templates.xml',
        'report/sale_report_templates.xml',
        # data
        'data/ir_cron_data.xml',
        # wizard
        'wizard/print_multiple_label_views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
