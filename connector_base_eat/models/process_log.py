# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProcessLog(models.Model):
    _name = 'process.log.eat'
    _description = "Process Log"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    type = fields.Selection([('product', 'Product'), ('order', 'Order'), ('shipment', 'Shipment'),
                             ('inventory', 'Inventory'), ('invoice', 'Invoice'), ('comment', 'Comment')])
    comment = fields.Text(string="Comment")
    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running'), ('done', 'Done'),
                              ('error', 'Error'), ('cancel', 'Cancel')], default='draft')
    process_id = fields.Char(string='Process ID')
    instance_id = fields.Many2one('connector.instance.eat', 'Instance')
    # check the process config
    process_channel = fields.Char('Channel')
