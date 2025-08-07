# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProcessProtocol(models.Model):
    _name = 'process.protocol.eat'
    _description = "Process Protocol"

    name = fields.Char(string="name", required=True)
    process = fields.Char(string="Process", required=True)
    mapper = fields.Many2one('process.mapper.eat', 'Mapper')
    business_type = fields.Selection([('other', 'Other'), ('product', 'Product'), ('order', 'Order'), ('shipment', 'Shipment'),
                                      ('inventory', 'Inventory'), ('invoice', 'Invoice')])
    process_type = fields.Selection([('feed', 'Feed'), ('ack', 'ACK'), ('import', 'Import'), ('export', 'Export')])
    description = fields.Text('Description')
