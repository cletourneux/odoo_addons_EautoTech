# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from odoo.addons.connector_base_eat import tool

_logger = logging.getLogger(__name__)


class FTPAckProcess(models.AbstractModel):
    _name = "process.ftp.ack.eat"
    _inherit = "process.other.eat"
    _description = "FTP(SFTP) ACK process"

    def do_process(self, env, process_config, process_id):
        instance_id = process_config.instance_id
        log_files = env['process.log.eat'].search([('state', '=', 'draft'), ('instance_id.id', '=', instance_id.id)])
        ok_log_files = self.do_process2(env, process_config, log_files)
        ok_log_files.write({'state': 'running'})

    def do_process2(self, env, process_config, log_files):
        if not log_files:
            return log_files
        properties = tool.build_process_properties(process_config)
        ack_folder = properties.get('ack_folder')
        backend = self.backend(env, process_config)
        with backend:
            for log_file in log_files:
                backend.delete(folder="{}{}".format(ack_folder, log_file.file_name))
        return log_files
