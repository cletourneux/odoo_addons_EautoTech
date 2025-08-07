# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class InvoiceFtpExportProcess(models.AbstractModel):
    _name = "process.invoice.ftp.export.eat"
    _inherit = ["process.invoice.export.eat", "process.ftp.export.eat"]
    _description = "Invoice Export process"
