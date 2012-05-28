# vim:set ft=python ts=4 sw=4 et fileencoding=utf-8:
"""
Adapter for the SOAP account management interfaces of Ricoh Aficio 2060
printers.

Provides :class:`UserMaintSession` which allows :class:`User`s to be queried,
added, modified and deleted.  A user has associated :class:`UserStatistics` and
:class:`UserRestrict` instances, which represent printer statistics and access
restrictions (respectively).
"""
# Copyright (C) 2007 Philipp Kern <philipp.kern@fsmi.uni-karlsruhe.de>
# Copyright (C) 2008, 2010, 2012 Fabian Knittel <fabian.knittel@lettink.de>
# Copyright (C) 2012 Felix Maurer <felix.maurer@fsmi.uni-karlsruhe.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.


from suds import suds.Client
import time
from aficio2060.encoding import encode, decode, DEFAULT_STRING_ENCODING


class UserMaintError(RuntimeError):
    def __init__(self, msg, code=None):
        RuntimeError.__init__(self, msg)
        self.code = code

class UserStatistics(object):
    """This class represents a set of access restrictions.

    If `grant_copy` is ``True``, then use of the printer's copy function is
    granted.
    If `grant_printer` is ``True``, then use of the printer's print function is
    granted.
    If `grant_scanner` is ``True``, then use of the printer's scan function is
    granted.
    If `grant_storage` is ``True``, then use of the printer's document storage
    function is granted.

    It supports serialisation to and deserialisation from XML using
    :meth:`to_xml` and :meth:`from_xml`.

    The class tracks whether it was modified, using the `modified` attribute.
    Class users need to reset `modified` as needed.
    """
    def __init__(self, copy_a4=0, copy_a3=0, print_a4=0,
            print_a3=0, scan_a4=0, scan_a3=0):
        self._copy_a4 = copy_a4
        self._copy_a3 = copy_a3
        self._print_a4 = print_a4
        self._print_a3 = print_a3
        self._scan_a4 = scan_a4
        self._scan_a3 = scan_a3
        self.modified = True

    def __repr__(self):
        return '<UserStatistics c%u,%u p%u,%u s%u,%u %s>' % (self.copy_a4,
                self.copy_a3, self.print_a4, self.print_a3,
                self.scan_a4, self.scan_a3,
                'modified' if self.modified else 'unmodified')

    def set_zero(self):
        self.copy_a4 = 0
        self.copy_a3 = 0
        self.print_a4 = 0
        self.print_a3 = 0
        self.scan_a4 = 0
        self.scan_a3 = 0

    def get_copy_a4(self):
        return self._copy_a4
    def set_copy_a4(self, val):
        self.modified = True
        self._copy_a4 = val
    copy_a4 = property(get_copy_a4, set_copy_a4)

    def get_copy_a3(self):
        return self._copy_a3
    def set_copy_a3(self, val):
        self.modified = True
        self._copy_a3 = val
    copy_a3 = property(get_copy_a3, set_copy_a3)

    def get_print_a4(self):
        return self._print_a4
    def set_print_a4(self, val):
        self.modified = True
        self._print_a4 = val
    print_a4 = property(get_print_a4, set_print_a4)

    def get_print_a3(self):
        return self._print_a3
    def set_print_a3(self, val):
        self.modified = True
        self._print_a3 = val
    print_a3 = property(get_print_a3, set_print_a3)

    def get_scan_a4(self):
        return self._scan_a4
    def set_scan_a4(self, val):
        self.modified = True
        self._scan_a4 = val
    scan_a4 = property(get_scan_a4, set_scan_a4)

    def get_scan_a3(self):
        return self._scan_a3
    def set_scan_a3(self, val):
        self.modified = True
        self._scan_a3 = val
    scan_a3 = property(get_scan_a3, set_scan_a3)

    @property
    def copy_a4_total(self):
        return self.copy_a4 + (self.copy_a3 * 2)

    @property
    def print_a4_total(self):
        return self.print_a4 + (self.print_a3 * 2)

    @property
    def scan_a4_total(self):
        return self.scan_a4 + (self.scan_a3 * 2)

    def is_zero(self):
        return self.copy_a4_total == 0 and \
                self.print_a4_total == 0 and \
                self.scan_a4_total == 0

    @staticmethod
    def from_soap_object(obj):
        items = obj.fieldList.item

class UserRestrict(object):
    """This class represents a set of access restrictions.

    If `grant_copy` is ``True``, then use of the printer's copy function is
    granted.
    If `grant_printer` is ``True``, then use of the printer's print function is
    granted.
    If `grant_scanner` is ``True``, then use of the printer's scan function is
    granted.
    If `grant_storage` is ``True``, then use of the printer's document storage
    function is granted.

    It supports serialisation to and deserialisation from XML using
    :meth:`to_xml` and :meth:`from_xml`.
    """
    def __init__(self, grant_copy=False, grant_printer=False,
            grant_scanner=False, grant_storage=False):
        self.grant_copy = grant_copy
        self.grant_printer = grant_printer
        self.grant_scanner = grant_scanner
        self.grant_storage = grant_storage

    def __repr__(self):
        return '<UserRestrict c%dp%ds%dst%d>' % (self.grant_copy,
                self.grant_printer, self.grant_scanner, self.grant_storage)

    def revoke_all(self):
        """Revoke all privileges."""
        self.grant_copy = False
        self.grant_printer = False
        self.grant_scanner = False
        self.grant_storage = False

    def has_any_permissions(self):
        """Are there any granted permissions at all?"""
        return self.grant_copy or self.grant_printer or self.grant_scanner or \
                self.grant_storage


class User(object):
    """This class represents a single user in the printer's user accounting.  It
    can have a user name `name`, a user code `user_code`, a set of access
    restrictions `restrict` of type :class:`UserRestrict` and printing
    statistics of type :class:`UserStatistics` associated with itsself.

    It supports serialisation to and deserialisation from XML using
    :meth:`to_xml` and :meth:`from_xml`.
    """

    MAX_NAME_LEN = 20

    def __init__(self, user_code, name, internal_name, restrict=None, stats=None):
        self.user_code = user_code
        self.name = name
        self.internal_name = internal_name
        self.restrict = restrict
        self.stats = stats

    def _set_user_code(self, user_code):
        if not hasattr(self, '_orig_user_code'):
            # Remember the original user code, as currently known to the
            # printer, so that any changes can be properly associated with that
            # user code.
            if hasattr(self, '_user_code'):
                self._orig_user_code = self._user_code
        self._user_code = user_code
    def _get_user_code(self):
        """The account's user code property."""
        return self._user_code
    user_code = property(_get_user_code, _set_user_code)

    def _get_orig_user_code(self):
        """Get the user code assigned to the user on the server-side."""
        if hasattr(self, '_orig_user_code'):
            return self._orig_user_code
        else:
            return self._user_code
    orig_user_code = property(_get_orig_user_code)

    def notify_flushed(self):
        """Inform the object, that the data was flushed to the server."""
        if hasattr(self, '_orig_user_code'):
            # The server now knows of the updated user code.
            del self._orig_user_code
        if self.stats is not None and self.stats.modified:
            self.stats.modified = False

    def _set_name(self, name):
        if len(name) > self.MAX_NAME_LEN:
            raise UserMaintError('user name "%s" too long, max %d ' \
                    'characters' % (name, self.MAX_NAME_LEN))
        self.__name = name
    def _get_name(self):
        return self.__name
    name = property(_get_name, _set_name)

    def __repr__(self):
        return '<User "%s" (#%s, %s, %s)>' % (unicode(self.name),
                str(self.user_code), str(self.restrict), str(self.stats))


class UserMaintSession(object):
    """
    Objects of this class represent a user maintainance session. They provide
    methods to retrieve and modify user accounts.

    There is no session on the network level: Each request initiates a
    self-contained XML-RPC request.
    """
    BUSY_CODE = 'systemBusy'

    def __init__(self, passString, wsdl):
        self.pass_string = passString
        self.wsdl = wsdl
        self.soap_client = Client(wsdl, cache=None)
        self.dm_service = self.soap_client.service["DeviceManagementService"]
        self.ud_service = self.soap_client.service["UserDirectoryService"]
        self.dm_session = self.dm_service.StartSession(passString, 0).stringOut
        self.ud_session = self.ud_service.StartSession(passString, 0, "S").stringOut
        
        user_ids = self.dm_service.GetObjects(self.dm_session, 0, "usageCounter.userCounter").item
        
        for user_id in user_ids:
            user_counter = self.dm_service.GetObject(self.dm_session, 0, user_id, {"item" : ["copyBlack", "copyBlackA3Over", "printBlack", "printerBlackA3Over", "scannerBlack", "scannerBlackA3Over"]})
            tmp_user_statistics = UserStatistics()


    def add_user(self, user):
        """Add object `user` of type :class:`User` as user account."""

        user.notify_flushed()

    def delete_user(self, user_code):
        """Delete user account with user code number `user_code`."""


    def get_user_info(self, user_code, req_user_code=True,
            req_user_code_name=True, req_restrict_info=True,
            req_statistics_info=True):
        """Get information about user account with user code number `user_code`.
        Returns a :class:`User` instance in case the user was found or else
        throws :class:`UserMaintError`.
        If `req_user_code` is ``True``, the user's user code is requested.
        If `req_user_code_name` is ``True``, the user's name is requested.
        If `req_restrict_info` is ``True``, the user's access restrictions are
        requested.
        If `req_statistics_info` is ``True``, the user's printing statistics are
        requested.
        """
        return self._get_user_info(user_code=user_code,
                req_user_code=req_user_code,
                req_user_code_name=req_user_code_name,
                req_restrict_info=req_restrict_info,
                req_statistics_info=req_statistics_info)[0]

    def get_user_infos(self, req_user_code=True,
            req_user_code_name=True, req_restrict_info=True,
            req_statistics_info=True):
        """Request information about all user accounts.
        Returns a list of :class:`User` instances. Throws
        :class:`UserMaintError` in case of an error.
        If `req_user_code` is ``True``, the users' user codes are requested.
        If `req_user_code_name` is ``True``, the users' names are requested.
        If `req_restrict_info` is ``True``, the users' access restrictions are
        requested.
        If `req_statistics_info` is ``True``, the users' printing statistics are
        requested.
        """
        return self._get_user_info(req_user_code=req_user_code,
                req_user_code_name=req_user_code_name,
                req_restrict_info=req_restrict_info,
                req_statistics_info=req_statistics_info)

    def _get_user_info(self, user_code='', req_user_code=True,
            req_user_code_name=True, req_restrict_info=True,
            req_statistics_info=True):

        return users

    def set_user_info(self, user):
        """Modify user account associated with `user`, which is an instance of
        :class:`User`.
        Throws :class:`UserMaintError` in case of an error.
        """
        user.notify_flushed()
