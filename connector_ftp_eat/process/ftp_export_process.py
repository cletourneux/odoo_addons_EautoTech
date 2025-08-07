# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class FtpExportProcess(models.AbstractModel):
    _name = "process.ftp.export.eat"
    _inherit = "process.export.eat"
    _description = "Export process"

    def do_export(self, env, process_config, data):
        export_folder, file_prefix, suffix = process_config.get_property(('export_folder', 'file_prefix', 'file_suffix'))
        suffix = suffix or process_config.process_protocol.mapper.type
        backend = self.backend(env, process_config)
        with backend:
            if type(data) == list:
                for data_line in data:
                    backend.create(folder='{}/{}'.format(export_folder, self.get_file_name(env, file_prefix, suffix)),
                                   fp=data_line)
            else:
                backend.create(folder='{}/{}'.format(export_folder, self.get_file_name(env, file_prefix, suffix)), fp=data)
        return [], []

    def get_file_name(self, env, file_prefix, suffix):
        sequence = self.get_sequence(env)
        return '{}{}.{}'.format(file_prefix, sequence, suffix)
