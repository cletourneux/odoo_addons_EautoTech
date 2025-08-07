# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class OtherProcess(models.AbstractModel):
    _name = "process.other.eat"
    _inherit = "process.process.eat"
    _description = "Import process"

    def process(self, env, process_config, process_id):
        now = self.now()
        result = self.do_process(env, process_config, process_id)
        if result:
            process_config['last_process_date'] = now

    def do_process(self, env, process_config, log_files):
        return True
