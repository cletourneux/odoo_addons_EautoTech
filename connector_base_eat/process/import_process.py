# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool
import base64
from io import BytesIO

_logger = logging.getLogger(__name__)


class ImportProcess(models.AbstractModel):
    _name = "process.import.eat"
    _inherit = "process.process.eat"
    _description = "Import process"

    def process(self, env, process_config, process_id):
        now = self.now()
        # in case of the all files with many data will make system crash
        file_count_limit = process_config.get_property('file_count_limit') or 20
        log_files = env['process.log.eat'].search([
            ('state', '=', 'running'), ('instance_id.id', '=', process_config.instance_id.id),
            ('type', '=', process_config.business_type), ('process_channel', '=', process_config.process_channel)],
            limit=int(file_count_limit))
        self.do_process(env, process_config, log_files)
        process_config['last_process_date'] = now

    def do_process(self, env, process_config, log_files):
        if not log_files:
            return
        idx = 0
        for log_file in log_files:
            content = log_file.file or b''
            decode_content = base64.b64decode(content)
            errors = self.do_import(env, process_config, decode_content)
            # submit
            if errors:
                log_file.write({'comment': str(errors), 'state': 'error'})
            else:
                log_file.write({'state': 'done'})
            if idx % 5 == 4:
                # need commit, or had the issue as well
                env.cr.commit()
            idx = idx + 1

    def do_import(self, env, process_config, log_file):
        try:
            data_list = self.map(env, process_config, log_file)
        except Exception as e:
            message = str(e)
            _logger.info('Import process map error {}'.format(message), stack_info=True)
            return [message]
        # if data list is a simple dict, we need use list as need
        if not isinstance(data_list, (tuple, list)):
            data_list = [data_list]
        return self.do_save(env, process_config, data_list)

    def do_save(self, env, process_config, data_list):
        """
        save all data
        :param env:
        :param process_config:
        :param data_list:
        :return: False means no error, or there is error response
        """
        errors = []
        for data in data_list:
            try:
                message = self.do_save_record(env, process_config, data)
            except Exception as e:
                message = str(e)
                _logger.info('Import process error {}'.format(message), stack_info=True)
            if message:
                errors.append(message)

        return errors

    def do_save_record(self, env, process_config, data):
        """
        we save data, and also record the error message, and also save successfully data
        :param env:
        :param process_config:
        :param data:
        :return:
        """
        return False
