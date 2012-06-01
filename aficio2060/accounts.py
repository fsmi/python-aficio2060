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


from suds.client import Client
import logging
import os, sys, traceback

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
        self.modified = False

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
        copy_a4 = 0
        copy_a3 = 0
        print_a4 = 0
        print_a3 = 0
        scan_a4 = 0
        scan_a3 = 0
        for item in items:
            if item.name == "copyBlack":
                copy_a4 = int(item.value)
            if item.name == "copyBlackA3Over":
                copy_a3 = int(item.value)
            if item.name == "printerBlack":
                print_a4 = int(item.value)
            if item.name == "printerBlackA3Over":
                print_a3 = int(item.value)
            if item.name == "scannerBlack":
                scan_a4 = int(item.value)
            if item.name == "scannerBlackA3Over":
                scan_a3 = int(item.value)
        return UserStatistics(copy_a4, copy_a3, print_a4, print_a3, scan_a4, scan_a3)
        
    def to_fieldList(self):
        return { "item" : [
            { "name" : "copyBlack", "value" : str(self.copy_a4), "type" : "DM_FIELD_UNSIGNED_INT" },
            { "name" : "copyBlackA3Over", "value" : str(self.copy_a3), "type" : "DM_FIELD_UNSIGNED_INT" },
            { "name" : "printerBlack", "value" : str(self.printer_a4), "type" : "DM_FIELD_UNSIGNED_INT" },
            { "name" : "printerBlackA3Over", "value" : str(self.printer_a3), "type" : "DM_FIELD_UNSIGNED_INT" },
            { "name" : "scannerBlack", "value" : str(self.scanner_a4), "type" : "DM_FIELD_UNSIGNED_INT" },
            { "name" : "scannerBlackA3Over", "value" : str(self.scanner_a3), "type" : "DM_FIELD_UNSIGNED_INT" }
        ]}

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
        self._grant_copy = grant_copy
        self._grant_printer = grant_printer
        self._grant_scanner = grant_scanner
        self._grant_storage = grant_storage
        self.modified = False

    def __repr__(self):
        return '<UserRestrict c%d, p%d, s%d, st%d>' % (self.grant_copy,
                self.grant_printer, self.grant_scanner, self.grant_storage)
    
    def _get_grant_copy(self):
        return self._grant_copy
    def _set_grant_copy(self, copy):
        if copy != self._grant_copy:
            self.modified = True
        self._grant_copy = copy
    grant_copy = property(_get_grant_copy, _set_grant_copy)
    
    def _get_grant_printer(self):
        return self._grant_printer
    def _set_grant_printer(self, printer):
        if printer != self._grant_printer:
            self.modified = True
        self._grant_printer = printer
    grant_printer = property(_get_grant_printer, _set_grant_printer)
    
    def _get_grant_scanner(self):
        return self._grant_scanner
    def _set_grant_scanner(self, scanner):
        if scanner != self._grant_scanner:
            self.modified = True
        self._grant_scanner = scanner
    grant_scanner = property(_get_grant_scanner, _set_grant_scanner)
    
    def _get_grant_storage(self):
        return self._grant_storage
    def _set_grant_storage(self, storage):
        if storage != self._grant_storage:
            self.modified = True
        self._grant_storage = storage
    grant_storage = property(_get_grant_storage, _set_grant_storage)
    
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

    @staticmethod
    def from_soap_object(obj):
        items = obj.fieldList.item
        grant_copy = False
        grant_printer = False
        grant_scanner = False
        grant_storage = False
        for item in items:
            if item.name == "copyBlack" and item.value == "OFF":
                grant_copy = True
            if item.name == "printerBlack" and item.value == "OFF":
                grant_printer = True
            if item.name == "scannerBlack" and item.value == "OFF":
                grant_scanner = True
            if item.name == "localStorage" and item.value == "OFF":
                grant_storage = True
        return UserRestrict(grant_copy, grant_printer, grant_scanner, grant_storage)
        
    def to_fieldList(self):
        return { "item" : [
            { "name" : "copyBlack", "value" : "OFF" if self.grant_copy else "ON", "type" : "DM_FIELD_ENUM" },
            { "name" : "printerBlack", "value" : "OFF" if self.grant_printer else "ON", "type" : "DM_FIELD_ENUM" },
            { "name" : "scannerBlack", "value" : "OFF" if self.grant_scanner else "ON", "type" : "DM_FIELD_ENUM" },
            { "name" : "localStorage", "value" : "OFF" if self.grant_storage else "ON", "type" : "DM_FIELD_ENUM" }
        ]}

class User(object):
    """This class represents a single user in the printer's user accounting.  It
    can have a user name `name`, a user code `user_code`, a set of access
    restrictions `restrict` of type :class:`UserRestrict` and printing
    statistics of type :class:`UserStatistics` associated with itsself.

    It supports serialisation to and deserialisation from XML using
    :meth:`to_xml` and :meth:`from_xml`.
    """

    MAX_NAME_LEN = 20

    def __init__(self, user_code, name, restrict=None, stats=None, internal_name=None):
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
        if self.restrict is not None and self.restrict.modified:
            self.restrict.modified = False

    def _set_name(self, name):
        if len(name) > self.MAX_NAME_LEN:
            raise UserMaintError('user name "%s" too long, max %d ' \
                    'characters' % (name, self.MAX_NAME_LEN))
        self.__name = name
    def _get_name(self):
        return self.__name
    name = property(_get_name, _set_name)
    
    def _set_internal_name(self, internal_name):
        self._internal_name = internal_name
    def _get_internal_name(self):
        return self._internal_name
    internal_name = property(_get_internal_name, _set_internal_name)
    
    def _get_stats(self):
        return self._stats
    def _set_stats(self, stats):
        self._stats = stats
        if self._stats is not None:
            self._stats.modified = True
    stats = property(_get_stats, _set_stats)
    
    def _get_restriction(self):
        return self._restriction
    def _set_restriction(self, restriction):
        self._restriction = restriction
        if self._restriction is not None:
            self._restriction.modified = True
    restriction = property(_get_restriction, _set_restriction)

    def __repr__(self):
        return '<User "%s" (#%s, %s, %s, %s)>' % (unicode(self.name),
                str(self.user_code), str(self.internal_name), str(self.restrict), str(self.stats))
                
    @staticmethod
    def from_soap_object(obj):
        items = obj.item.item
        name = ""
        code = ""
        for item in items:
            if item.propName == "name":
                name = unicode(item.propVal)
            if item.propName == "auth:name":
                code = int(item.propVal)
        return User(code, name)

    def to_propListList(self):
        return { "item" : { "item" : [
                    { "propName" : "entryType", "propVal" : "user" },
                    { "propName" : "isDestination", "propVal" : "true" },
                    { "propName" : "isSender", "propVal" : "true" },
                    { "propName" : "name", "propVal" : self.name },
                    { "propName" : "longName", "propVal" : self.name },
                    { "propName" : "auth:name", "propVal" : self.user_code },
                    { "propName" : "auth:password", "propVal" : "m9gZWJtcmJtaW9oZ3JseWdrdGZnbnByZW9iZHhqdnJwaG13dXVoZnB1cWF3YXRwanBpbW5ocGx3aWFraWthcHJvbGpydXRldm9qaHZ1aHNpYHNhZ2hmaHdzbmBpYWh2aWlkZWh5dmF2ZGplaXdgemZyZm51cGpibWZnYHFgc2hocHRpdGxrbmp4=" },
                    { "propName" : "passwordEncoding", "propVal" : "gwpwes002" }
                    ]}}
class UserMaintSession(object):
    """
    Objects of this class represent a user maintainance session. They provide
    methods to retrieve and modify user accounts.

    There is no session on the network level: Each request initiates a
    self-contained SOAP request. There is a session on the API level thought.
    """

    def __init__(self, pass_string, wsdl):
        self.pass_string = pass_string
        self.wsdl = wsdl if wsdl.startswith("file://") else "file://" + wsdl
        
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
        if not "SUDS_DEBUG" in os.environ.keys():
            logging.disable(logging.ERROR)

        self.soap_client = Client(self.wsdl, cache=None)
        self.dm_service = self.soap_client.service["DeviceManagementService"]
        self.ud_service = self.soap_client.service["UserDirectoryService"]
        self.dm_session = self.dm_service.StartSession(self.pass_string, 0).stringOut
        self.ud_session = self.ud_service.StartSession(self.pass_string, 0, "S").stringOut
        
        self.users = {}
        user_counter_ids = self.dm_service.GetObjects(self.dm_session, 0, "usageCounter.userCounter").item
        user_restrict_ids = self.dm_service.GetObjects(self.dm_session, 0, "usageControl.userRestrict").item
        
        for user_counter_id in user_counter_ids:
            try:
                user_counter = self.dm_service.GetObject(self.dm_session, 0, user_counter_id, {"item" : ["copyBlack", "copyBlackA3Over", "printerBlack", "printerBlackA3Over", "scannerBlack", "scannerBlackA3Over"]})
                user_internal_name = user_counter.name
                tmp_user_stats = UserStatistics.from_soap_object(user_counter)
                tmp_user_stats.modified = False
                user_properties = self.ud_service.GetObjectsProps(self.ud_session, { "item" : ["entry:"+str(user_internal_name)] }, { "item" : [ "name", "auth:name" ] }, {})
                tmp_user = User.from_soap_object(user_properties)
                tmp_user.internal_name = user_internal_name
                tmp_user.stats = tmp_user_stats
                self.users[user_internal_name] = tmp_user
            except Exception, e:
                pass
        
        for user_restrict_id in user_restrict_ids:
            try:
                user_restrict = self.dm_service.GetObject(self.dm_session, 0, user_restrict_id, {"item" : ["copyBlack", "printerBlack", "scannerBlack", "localStorage"]})
                if user_restrict.name in self.users:
                    self.users[user_restrict.name].restrict = UserRestrict.from_soap_object(user_restrict)
            except Exception, e:
                pass
        
        self.dm_service.TerminateSession(self.dm_session)
        del self.dm_session
        self.ud_service.TerminateSession(self.ud_session)
        del self.ud_session
        
    def __del__(self):
        if hasattr(self, 'dm_service') and hasattr(self, 'dm_session'):
            self.dm_service.TerminateSession(self.dm_session)
        if hasattr(self, 'ud_service') and hasattr(self, 'ud_session'):
            self.ud_service.TerminateSession(self.ud_session)

    def add_user(self, user):
        """Add object `user` of type :class:`User` as user account."""
        self.ud_session = self.ud_service.StartSession(self.pass_string, 0, "X").stringOut
        response = self.ud_service.PutObjects(self.ud_session, "entry", {}, user.to_propListList(), {})
        user.internal_name = response.item
        self.ud_service.TerminateSession(self.ud_session)
        del self.ud_session
        
        self.dm_session = self.dm_service.StartSession(self.pass_string, 0).stringOut
        lock = self.dm_service.LockDevice(self.dm_session, 0, 0)
        response = self.dm_service.UpdateObject(self.dm_session, 0, { "name" : int(user.internal_name), 
                                                                      "class" : "usageControl.userRestrict", 
                                                                      "oid" : int("110002"+str(user.internal_name)),
                                                                      "fieldList" : user.restrict.to_fieldList() },
                                                                    { "item" : { "propName" : "replaceAll", "propVal" : "false" } } )
        unlock = self.dm_service.UnlockDevice(self.dm_session, 0)
        self.dm_service.TerminateSession(self.dm_session)
        del self.dm_session
        
        user.notify_flushed()

    def delete_user(self, user_code):
        """Delete user account with user code number `user_code`."""
        user = self.get_user_info(user_code)
        if user == None:
            return
       
        self.ud_session = self.ud_service.StartSession(self.pass_string, 0, "X").stringOut
        
        response = self.ud_service.PutObjectProps(self.ud_session, "entry:" + str(user.internal_name),
                                                    { "item" : { "propName" : "auth:", "propVal" : "false" } },
                                                    { "item" : { "propName" : "replaceAll", "propVal" : "false" } } )
        self.ud_service.TerminateSession(self.ud_session)
        del self.ud_session


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
        for user_internal_name, user in self.users.iteritems():
            if user.user_code == user_code:
                return user
        return None

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
        return self.users.values()

    def set_user_info(self, user):
        """Modify user account associated with `user`, which is an instance of
        :class:`User`.
        Throws :class:`UserMaintError` in case of an error.
        """
        self.dm_session = self.dm_service.StartSession(self.pass_string, 0).stringOut
        lock = self.dm_service.LockDevice(self.dm_session, 0, 0)
        if user.restrict.modified:
            response = self.dm_service.UpdateObject(self.dm_session, 0, { "name" : int(user.internal_name), 
                                                                          "class" : "usageControl.userRestrict", 
                                                                          "oid" : int("110002"+str(user.internal_name)),
                                                                          "fieldList" : user.restrict.to_fieldList() },
                                                                        { "item" : { "propName" : "replaceAll", "propVal" : "false" } } )
            if response.returnValue is not "OK":
                raise UserMaintError("Could not update the user restrictions for user " + str(user.name))
        if user.stats.modified:
            response = self.dm_service.UpdateObject(self.dm_session, 0, { "name" : int(user.internal_name), 
                                                                          "class" : "usageCounter.userCounter", 
                                                                          "oid" : int("110002"+str(user.internal_name)),
                                                                          "fieldList" : user.stats.to_fieldList() },
                                                                        { "item" : { "propName" : "replaceAll", "propVal" : "false" } } )
            if response.returnValue is not "OK":
                raise UserMaintError("Could not update the user counter for user " + str(user.name))
        unlock = self.dm_service.UnlockDevice(self.dm_session, 0)
        self.dm_service.TerminateSession(self.dm_session)
        del self.dm_session
        user.notify_flushed()
