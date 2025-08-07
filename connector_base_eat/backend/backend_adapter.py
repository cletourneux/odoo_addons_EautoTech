# -*- coding: utf-8 -*-

"""

Backend Adapter

basic connection with 3rd system

"""


class BackendAdapter(object):
    """ Base Backend Adapter for the connectors """


class CRUDAdapter(BackendAdapter):

    def open(self, *args, **kwargs):
        """ open """
        raise NotImplementedError

    def close(self, *args, **kwargs):
        """ close """
        raise NotImplementedError

    def search(self, *args, **kwargs):
        """ Search records according to some criterias
        and returns a list of ids """
        raise NotImplementedError

    def read(self, *args, **kwargs):
        """ Returns the information of a record """
        raise NotImplementedError

    def search_read(self, *args, **kwargs):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, *args, **kwargs):
        """ Create a record on the external system """
        raise NotImplementedError

    def write(self, *args, **kwargs):
        """ Update records on the external system """
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        """ Delete a record on the external system """
        raise NotImplementedError
