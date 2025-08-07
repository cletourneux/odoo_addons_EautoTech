# -*- coding: utf-8 -*-

import logging
import re
import base64

from odoo import api, fields, models, tools, _
from io import BytesIO

_logger = logging.getLogger(__name__)


class FTPFeedProcess(models.AbstractModel):
    _name = "process.ftp.feed.eat"
    _inherit = "process.other.eat"
    _description = "FTP(SFTP) feed process"

    def do_process(self, env, process_config, process_id):
        backend = self.backend(env, process_config)
        import_folder, skip_folders, file_regex = process_config.get_property(
            ('import_folder', 'skip_folder', 'file_regex'))
        skip_folder_list = []
        if skip_folders:
            skip_folder_list = skip_folders.split(',')
        with backend:
            files = backend.search(folder=import_folder)
            if not files:
                return
            for file in files:
                if file in skip_folder_list:
                    continue
                if not self._validate_file(file, file_regex):
                    continue
                content = self._read_file(backend, import_folder, file)
                if content == b'':
                    continue
                log = self.build_log_object(process_config.instance_id.id, process_config.business_type,
                                            process_id, False, content, file)
                self.create_log(env, log)
        return True

    def _read_file(self, backend, import_folder, file):
        # add unique id for the document with duplicated check
        file_data = BytesIO()
        backend.read(folder="{}{}".format(import_folder, file), fp=file_data, callback=file_data.write)
        file_data.seek(0)
        return file_data.read()

    def _validate_file(self, file, file_regex):
        if not file_regex:
            return True
        return re.search(file_regex, file) is not None


