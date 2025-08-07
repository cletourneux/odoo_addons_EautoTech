# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from ..backend import sftp_backend_adapter, ftp_backend_adapter

_logger = logging.getLogger(__name__)

process_items = (
    {'name': 'FTP/SFTP Order Feed', 'process_type': 'feed', 'process': 'process_ftp_feed_eat', 'business_type': 'order', 'properties': 'import_folder:/out/\nskip_folder:.,..\nfile_regex:order(.*).xlsx',},
    {'name': 'FTP/SFTP Product Feed', 'process_type': 'feed', 'process': 'process_ftp_feed_eat', 'business_type': 'product', 'properties': 'import_folder:/out/\nskip_folder:.,..\nfile_regex:product(.*).xlsx',},
    {'name': 'FTP/SFTP Shipment Feed', 'process_type': 'feed', 'process': 'process_ftp_feed_eat', 'business_type': 'shipment', 'properties': 'import_folder:/out/\nskip_folder:.,..\nfile_regex:shipment(.*).xlsx',},
    {'name': 'FTP/SFTP Inventory Feed', 'process_type': 'feed', 'process': 'process_ftp_feed_eat', 'business_type': 'inventory', 'properties': 'import_folder:/out/\nskip_folder:.,..\nfile_regex:inventory(.*).xlsx',},
    {'name': 'FTP/SFTP Invoice Feed', 'process_type': 'feed', 'process': 'process_ftp_feed_eat', 'business_type': 'invoice', 'properties': 'import_folder:/out/\nskip_folder:.,..\nfile_regex:invoice(.*).xlsx',},
    {'name': 'FTP/SFTP Ack', 'process_type': 'ack', 'process': 'process_ftp_ack_eat', 'business_type': 'other', 'properties': 'ack_folder:/out/',},
    {'name': 'Inventory Import XLSX', 'process_type': 'import', 'process': 'process_inventory_import_eat_xlsx', 'business_type': 'inventory',},
    {'name': 'FTP/SFTP Inventory Export XLSX', 'process_type': 'export', 'process': 'process_inventory_export_eat_xlsx_ftp', 'process_way': 'all', 'business_type': 'inventory', 'properties': 'export_folder:/in\nfile_prefix:inventory\ninventory_type:qty_available',},
    {'name': 'Invoice Import XLSX', 'process_type': 'import', 'process': 'process_invoice_import_eat_xlsx', 'business_type': 'invoice',},
    {'name': 'FTP/SFTP Invoice Export XLSX', 'process_type': 'export', 'process': 'process_invoice_export_eat_xlsx_ftp', 'process_way': 'last_update', 'business_type': 'invoice', 'properties': 'export_folder:/in\nfile_prefix:invoice',},
    {'name': 'Order Import XLSX', 'process_type': 'import', 'process': 'process_order_import_eat_xlsx', 'business_type': 'order',},
    {'name': 'FTP/SFTP Order Export XLSX', 'process_type': 'export', 'process': 'process_order_export_eat_xlsx_ftp', 'process_way': 'last_update', 'business_type': 'order', 'properties': 'export_folder:/in\nfile_prefix:order',},
    {'name': 'Product Import XLSX', 'process_type': 'import', 'process': 'process_product_import_eat_xlsx', 'business_type': 'product',},
    {'name': 'FTP/SFTP Product Export XLSX', 'process_type': 'export', 'process': 'process_product_export_eat_xlsx_ftp', 'process_way': 'last_update', 'business_type': 'product', 'properties': 'export_folder:/in\nfile_prefix:product',},
    {'name': 'Shipment Import XLSX', 'process_type': 'import', 'process': 'process_shipment_import_eat_xlsx', 'business_type': 'shipment',},
    {'name': 'FTP/SFTP Shipment Export XLSX', 'process_type': 'export', 'process': 'process_shipment_export_eat_xlsx_ftp', 'process_way': 'last_update', 'business_type': 'shipment', 'properties': 'export_folder:/in\nfile_prefix:shipment',},
)


class FTPEndpoint(models.Model):
    _name = 'process.endpoint.ftp.eat'
    _description = "FTP Endpoint"
    _inherit = 'process.endpoint.eat'
    _sequence = 'process_endpoint_eat_id_seq'

    type = fields.Char(string='Type', default='ftp', readonly=True)
    host = fields.Char(required=True)
    port = fields.Integer(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)
    no_passive = fields.Boolean(string="No Passive?")
    security = fields.Boolean(string="Security?")

    def init_check(self, instance):
        ftp = ftp_backend_adapter.FtpBackendAdapter(self, self.env)
        result = ftp.open()
        ftp.close()
        if not result:
            raise UserError('Ftp connection error, please check your config')
        return True

    def init_process_configs(self, instance):
        return process_items

    def current_module_name(self):
        return 'connector_ftp_eat'

class SFTPEndpoint(models.Model):
    _name = 'process.endpoint.sftp.eat'
    _description = "SFTP Endpoint"
    _inherit = 'process.endpoint.eat'
    _sequence = 'process_endpoint_eat_id_seq'

    type = fields.Char(string='Type', default='sftp', readonly=True)
    host = fields.Char(required=True)
    port = fields.Integer(required=True)
    user = fields.Char(required=True)
    password = fields.Char(required=True)

    def init_check(self, instance):
        sftp = sftp_backend_adapter.SFtpBackendAdapter(instance, self.env)
        result = sftp.open()
        sftp.close()
        if not result:
            raise UserError('SFtp connection error, please check your config')
        return True

    def init_process_configs(self, instance):
        return process_items

    def current_module_name(self):
        return 'connector_ftp_eat'
