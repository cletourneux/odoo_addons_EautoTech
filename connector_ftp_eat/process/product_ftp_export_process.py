# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductFtpExportProcess(models.AbstractModel):
    _name = "process.product.ftp.export.eat"
    _inherit = ["process.product.export.eat", "process.ftp.export.eat"]
    _description = "Product Export process"
