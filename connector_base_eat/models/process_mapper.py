# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class Mapper(models.Model):
    _name = 'process.mapper.eat'
    _description = "Process Mapper"

    name = fields.Char(string="Name", required=True)
    type = fields.Selection([('object', 'OBJECT'), ('json', 'JSON'), ('xml', 'XML'), ('xlsx', 'XLSX'), ('csv', 'CSV')])
    model_name = fields.Char(string="Mapper", required=True)
