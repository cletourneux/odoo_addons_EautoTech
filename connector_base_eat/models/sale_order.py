# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    instance_id = fields.Many2one('connector.instance.eat', 'Connector Instance')
    client_order_id = fields.Char(string="Client Order ID")
    carrier_router = fields.Char('Carrier Router')
    carrier_accepted = fields.Boolean(string='Carrier Accepted')


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    client_order_line_id = fields.Char(string="Client Order Line ID")
