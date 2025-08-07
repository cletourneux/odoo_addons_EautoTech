# -*- coding: utf-8 -*-

{
    'name': 'Odoo FTP/SFTP Connector',
    'version': '0.2',
    'category': 'Sales',
    'summary': 'Odoo Common Connector, FTP/SFTP Connector, EDI Connector, SPS Commerce, Commercehub Connector',
    'author': 'Eauto Tech',
    'maintainer': 'Eauto Tech',
    'license': 'OPL-1',
    'support': 'Eauto Tech',
    'website': 'https://eauto-tech.odoo.com',
    'depends': ['connector_base_eat'],
    'external_dependencies': {
        'python': ['paramiko'],  # pip3 install paramiko==2.7.2
    },
    'data': [
        'security/ir.model.access.csv',
        'data/process_data.xml',
        'views/process_endpoint_view.xml',
        'views/connector_menus.xml',
    ],
    'installable': True,
    'price': 80.00,
    'currency': 'EUR',
    'images': ['static/description/images/connector_ftp_eat.png'],
    'qweb': [],
    'pre_init_hook': 'create_required_table',
}
