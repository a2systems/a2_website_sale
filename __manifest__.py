# -*- coding: utf-8 -*-
{
    "name": "Escanort - Website Sale",
    'version': '17.0.1.0.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'A2 Systems, Moldeo Interactive,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'base','account','product','sale','website_sale'
    ],
    'external_dependencies': {
    },
    'data': [
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/catalog.xml',
        'views/template.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
