# -*- coding: utf-8 -*-

import requests
import logging

from .backend_adapter import CRUDAdapter
from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ApiBackendAdapter(CRUDAdapter):
    """ API Backend Adapter """

    def __init__(self, config, env):
        self.config = config
        self.env = env

    def open(self, *args, **kwargs):
        return True

    def close(self, *args, **kwargs):
        return True

    def search(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def read(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def search_read(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def create(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def write(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def delete(self, *args, **kwargs):
        return self._do_common_request(args, kwargs)

    def _do_common_request(self, args, kwargs):
        url = kwargs.get('url')
        return self._do_request(url, kwargs.get('params'), kwargs.get('headers'), kwargs.get('type'))

    def _do_request(self, uri, params={}, headers={}, type='POST'):
        """ Execute the request
            :param uri : the url to contact
            :param params : dict or already encoded parameters for the request to make
            :param headers : headers of request
            :param type : the method to use to make the request
        """
        _logger.debug("Uri: %s - Type : %s - Headers: %s - Params : %s !", (uri, type, headers, params))
        if isinstance(params, dict):
            timeout = params.pop('timeout', 30)
        else:
            timeout = 30
        try:
            if type.upper() in ('GET', 'DELETE'):
                res = requests.request(type.lower(), uri, params=params, timeout=timeout)
            elif type.upper() in ('POST', 'PATCH', 'PUT'):
                res = requests.request(type.lower(), uri, data=params, headers=headers, timeout=timeout)
            else:
                raise Exception(_('Method not supported [%s] not in [GET, POST, PUT, PATCH or DELETE]!') % (type))
            res.raise_for_status()
            status = res.status_code

            if int(status) in (204, 404):  # Page not found, no response
                response = False
            else:
                response = res.content

        except requests.HTTPError as error:
            if error.response.status_code in (204, 404):
                status = error.response.status_code
                response = ""
            else:
                _logger.exception("Bad request : %s !", error.response.content)
                if error.response.status_code in (400, 401, 403, 410):
                    raise error
                raise UserError("Something went wrong with your request")
        return response
