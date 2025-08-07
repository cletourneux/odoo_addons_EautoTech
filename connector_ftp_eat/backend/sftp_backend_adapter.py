# -*- coding: utf-8 -*-

import logging
from odoo.addons.connector_base_eat.backend.backend_adapter import CRUDAdapter

_logger = logging.getLogger(__name__)

try:
    import paramiko
except ImportError:
    raise ImportError(
        'This module needs paramiko to automatically write backups to the FTP through SFTP. '
        'Please install paramiko on your system. (sudo pip3 install paramiko)')


class SFtpBackendAdapter(CRUDAdapter):
    """ Ftp Backend Adapter """

    def __init__(self, config, env):
        self._sftp = False
        self._sftp_session = False
        self.ftp_connector = config
        self.env = env

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def check_connection(self):
        return self._sftp and self._sftp_session

    def open(self):
        if self._sftp and self._sftp_session:
            return True
        host = self.ftp_connector.host
        port = self.ftp_connector.port
        user = self.ftp_connector.user
        password = self.ftp_connector.password
        try:
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(host, port, user, password, banner_timeout=20, timeout=20)
            self._sftp = s
            self._sftp_session = s.open_sftp()
            return True
        except Exception as e:
            _logger.error('Exception for sftp %s open with error %s' % (host, str(e)))
            self.close()
        return False

    def close(self):
        try:
            if self._sftp_session:
                self._sftp_session.close()
                self._sftp_session = False
            if self._sftp:
                self._sftp.close()
                self._sftp = False
            return True
        except Exception as e:
            _logger.error('Exception for sftp close with error %s' % (str(e)))
        return False

    def search(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                assert folder

                self._sftp_session.chdir(folder)
                return self._sftp_session.listdir(folder)
            except Exception as e:
                _logger.error('Exception for sftp search with error %s' % (str(e)))

        return False

    def read(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                fp = kwargs.get('fp', False)
                assert folder
                assert fp

                self._sftp_session.getfo(folder, fp)
                return True
            except Exception as e:
                _logger.error('Exception for sftp read with error %s' % (str(e)))

        return False

    def search_read(self, *args, **kwargs):
        pass

    def create(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                fp = kwargs.get('fp', False)
                assert folder, fp

                self._sftp_session.putfo(fp, folder)
                return True
            except Exception as e:
                _logger.error('Exception for sftp create with error %s' % (str(e)))

        return False

    def write(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                assert folder

                self._sftp_session.remove(folder)
                return True
            except Exception as e:
                _logger.error('Exception for sftp delete with error %s' % (str(e)))

        return False

    def rename(self, *args, **kwargs):
        if self.check_connection():
            try:
                folder = kwargs.get('folder', False)
                to_folder = kwargs.get('to_folder', False)
                assert folder
                assert to_folder
                self._sftp_session.rename(folder, to_folder)
                return True
            except Exception as e:
                _logger.error('Exception for sftp rename with error %s' % (str(e)))
        return False
