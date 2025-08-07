# -*- coding: utf-8 -*-

import requests
from datetime import datetime

import logging

from .backend_adapter import CRUDAdapter
from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MockBackendAdapter(CRUDAdapter):
    """ Mock Backend Adapter """

    @classmethod
    def proxy(cls, backend, env):
        if env.context.get('test', False):
            return MockBackendAdapter(backend, env)
        return backend

    def __init__(self, ftp, env):
        self.ftp = ftp
        self.env = env
        self._show_objects(ftp, env)

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, item):
        return getattr(self.ftp, item)

    def open(self, *args, **kwargs):
        return True

    def close(self, *args, **kwargs):
        return True

    def search(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return []

    def read(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return False

    def search_read(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return False

    def create(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return False

    def write(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return False

    def delete(self, *args, **kwargs):
        self._show_objects(*args, **kwargs)
        return False

    def create_order(self, xml):
        _logger.info(xml)
        return []

    def _show_objects(self, *args, **kwargs):
        for arg in args:
            if '_io.StringIO' in str(type(arg)):
                _logger.info('IO Parameters: {}'.format(arg.getvalue()))
            elif '_io.BytesIO' in str(type(arg)):
                _logger.info('IO Parameters: {}'.format(str(arg.getvalue(), 'utf-8')))
            else:
                _logger.info('Parameters: {}'.format(str(arg)))
        for k, value in kwargs.items():
            if '_io.StringIO' in str(type(value)):
                _logger.info('IO Parameters: {}={}'.format(k, value.getvalue()))
            elif '_io.BytesIO' in str(type(value)):
                _logger.info('IO Parameters: {}={}'.format(k, str(value.getvalue(), 'utf-8')))
            else:
                _logger.info('Parameters: {}={}'.format(k, str(value)))

