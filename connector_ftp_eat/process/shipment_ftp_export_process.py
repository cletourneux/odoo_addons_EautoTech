# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ShipmentFtpExportProcess(models.AbstractModel):
    _name = "process.shipment.ftp.export.eat"
    _inherit = ["process.shipment.export.eat", "process.ftp.export.eat"]
    _description = "Shipment Export process"
