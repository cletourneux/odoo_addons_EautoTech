# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class ProcessConfig(models.Model):
    _name = 'process.config.eat'
    _description = "Process Config"

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True)
    instance_id = fields.Many2one('connector.instance.eat', 'Instance')
    endpoint_id = fields.Many2one('process.endpoint.eat', 'Endpoint', help="Current process endpoint(or we could use instance endpoint if this is empty)")
    # process
    business_type = fields.Selection([('product', 'Product'), ('order', 'Order'), ('shipment', 'Shipment'),
                                      ('inventory', 'Inventory'), ('invoice', 'Invoice'), ('other', 'Other')])
    process_type = fields.Selection([('import', 'Import'), ('export', 'Export'), ('feed', 'Feed'), ('ack', 'ACK')])
    # Process protocol
    process_protocol = fields.Many2one('process.protocol.eat', 'Process', required=True)
    # identity the detail business for which channel to be consumed
    process_channel = fields.Char('Channel')
    process_way = fields.Selection([('create', 'Create'), ('last_update', 'Last Update'), ('all', 'All')])
    properties = fields.Text(string='Property', help='Use key:value to config properties, eg: name:test\nage:30')
    last_process_date = fields.Datetime('Last Process Date')

    # def _register_hook(self):
    #     exists = tools.constraint_definition(self._cr, 'process_config_eat', 'process_config_eat_endpoint_id_fkey')
    #     if exists is not None:
    #         tools.drop_constraint(self._cr, 'process_config_eat', 'process_config_eat_endpoint_id_fkey')
    #     self.env['ir.model.constraint'].search([
    #         ('model.model', '=', 'process_config_eat'), ('name', '=', 'process_config_eat_endpoint_id_fkey')
    #     ]).unlink()

    def get_property(self, names):
        self.ensure_one()
        prop_dict = tool.build_process_properties(self)
        if isinstance(names, str):
            return prop_dict.get(names, False)
        return (prop_dict.get(name, False) for name in names)
