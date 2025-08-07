# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class InventoryFtpExportProcess(models.AbstractModel):
    _name = "process.inventory.ftp.export.eat"
    _inherit = ["process.inventory.export.eat", "process.ftp.export.eat"]
    _description = "Inventory Export process"
