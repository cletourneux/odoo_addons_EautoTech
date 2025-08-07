# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from ..backend import sftp_backend_adapter, ftp_backend_adapter

_logger = logging.getLogger(__name__)


class ProcessProcess(models.AbstractModel):
    _name = 'process.process.eat'
    _inherit = 'process.process.eat'

    def customize_backend(self, env, endpoint_type, endpoint_config):
        if endpoint_type == 'sftp':
            return sftp_backend_adapter.SFtpBackendAdapter(endpoint_config, env)
        elif endpoint_type == 'ftp':
            return ftp_backend_adapter.FtpBackendAdapter(endpoint_config, env)
        else:
            return super(ProcessProcess, self).customize_backend(env, endpoint_type, endpoint_config)
