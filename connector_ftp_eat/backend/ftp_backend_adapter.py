# -*- coding: utf-8 -*-

import logging
import ftplib
import ssl

from odoo.addons.connector_base_eat.backend.backend_adapter import CRUDAdapter

_logger = logging.getLogger(__name__)


class ImplicitFTPTLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


class FtpBackendAdapter(CRUDAdapter):
    """ Ftp Backend Adapter """

    def __init__(self, config, env):
        self._ftp = False
        self.ftp_connector = config
        self.env = env

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def check_connection(self):
        return self._ftp

    def open(self):
        if self._ftp:
            return True

        host = self.ftp_connector.host
        port = self.ftp_connector.port
        user = self.ftp_connector.user
        password = self.ftp_connector.password
        security = self.ftp_connector.security

        try:
            if security:
                self._ftp = ImplicitFTPTLS()
            else:
                self._ftp = ftplib.FTP()
            if self.ftp_connector.no_passive:
                self._ftp.set_pasv(0)
            self._ftp.connect(host, port or 21, 20)
            self._ftp.login(user, password)
            if security:
                self._ftp.prot_p()
            return True
        except Exception as e:
            _logger.error('Exception for ftp %s with error %s' % (host, str(e)))
        return False

    def close(self):
        try:
            if self._ftp:
                self._ftp.quit()
                self._ftp = False
            return True
        except Exception as e:
            _logger.error('Exception for ftp close with error %s' % (str(e)))
        return False

    def search(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                assert folder

                self._ftp.cwd(folder)
                return self._ftp.nlst()
            except Exception as e:
                _logger.error('Exception for ftp search with error %s' % (str(e)))

        return False

    def read(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                callback = kwargs.get('callback', False)
                assert folder
                assert callback

                self._ftp.retrbinary('RETR %s' % folder, callback)
                return True
            except Exception as e:
                _logger.error('Exception for ftp read with error %s' % (str(e)))

        return False

    def search_read(self, *args, **kwargs):
        pass

    def create(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                fp = kwargs.get('fp', False)
                assert folder
                assert fp

                self._ftp.storbinary('STOR %s' % folder, fp)
                return True
            except Exception as e:
                _logger.error('Exception for ftp create with error %s' % (str(e)))

        return False

    def write(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                assert folder

                self._ftp.delete(folder)
                return True
            except Exception as e:
                _logger.error('Exception for ftp delete with error %s' % (str(e)))

        return False

    def rename(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                to_folder = kwargs.get('to_folder', False)
                assert folder
                assert to_folder
                self._ftp.rename(folder, to_folder)
                return True
            except Exception as e:
                _logger.error('Exception for ftp rename with error %s' % (str(e)))
        return False

