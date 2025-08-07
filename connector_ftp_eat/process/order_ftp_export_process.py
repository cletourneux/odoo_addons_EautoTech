# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class OrderFtpExportProcess(models.AbstractModel):
    _name = "process.order.ftp.export.eat"
    _inherit = ["process.order.export.eat", "process.ftp.export.eat"]
    _description = "Order Export process"
