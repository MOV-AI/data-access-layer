"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020

   Module for the Package namespace
"""
import copy
import hashlib
import os

from ..movaidb.database import MovaiDB
from .scope import Scope
from .structures import Struct
from deprecated.api.core.helpers import Helpers

from deprecated.logger import StdoutLogger
LOGGER = StdoutLogger("spawner.mov.ai")


class FileStruct(Struct):
    """ Helper class to provide callbacks on attributes set """

    def __init__(self, name, struct_dict, prev_struct, db):
        super().__init__(name=name, struct_dict=struct_dict, prev_struct=prev_struct, db=db)
        self.__dict__['setattr_callback'] = {"Value": self.set_checksum}

    def __setattr__(self, name, value):
        if name in self.attrs:
            self.__dict__[name] = value
            MovaiDB(self.db).set(Helpers.join_first(
                {name: value}, self.prev_struct))
            if name in self.__dict__['setattr_callback']:
                self.setattr_callback[name](name, value)
        elif name in self.lists:
            raise AttributeError(('"%s" is a list not an attribute') % name)
        elif name in self.hashs:
            raise AttributeError(('"%s" is a hash not an attribute') % name)
        else:
            raise AttributeError(('Attribute "%s" does not exist') % name)

    def set_checksum(self, name, value):
        """ Callback to calculate and save the checksum """
        checksum = hashlib.md5()
        if isinstance(value, bytes):
            checksum.update(value)
        else:
            checksum.update(value.encode("utf-8"))
        result = checksum.hexdigest()
        self.__dict__["Checksum"] = result
        MovaiDB(self.db).set(Helpers.join_first(
            {"Checksum": result}, self.prev_struct))


class Package(Scope):
    """Package class deals with packages/files uploaded to the db"""
    scope = 'Package'

    def __init__(self, name, version='latest', new=False, db='global'):
        super().__init__(scope='Package', name=name, version=version, new=new, db=db)

    def add(self, key, name, **kwargs):  # check if exixts and give error
        new_struct = dict()
        for elem in self.struct_dict[key]:
            # the value in the struct
            new_struct[name] = self.struct_dict[key][elem]

        temp = copy.deepcopy(self.prev_struct)

        if key == "File":
            self.__dict__[key][name] = FileStruct(
                key, new_struct, temp, self.db)
        else:
            self.__dict__[key][name] = Struct(key, new_struct, temp, self.db)

        for arg_key, arg_value in kwargs.items():
            setattr(self.__dict__[key][name], arg_key, arg_value)

        return self.__dict__[key][name]

    def get_checksum(self, file_name):
        """ get the file checksum from the db """
        return self.File[file_name].Checksum

    def get_file_checksum(self, file_path):
        """ Opens a file and calculates the checksum """
        tst_checksum = hashlib.md5()

        try:
            with open(file_path, "rb") as infile:
                for line in infile:
                    tst_checksum.update(line)
        except Exception:
            pass

        return tst_checksum.hexdigest()

    def is_checksum_valid(self, file_name, checksum):
        """ Compares db checksum with file checksum """
        return checksum == self.get_checksum(file_name)

    def dump_file(self, file_name, path_to):
        """ Dump a file from redis. Uses the checksum to validate the dump. """
        file = self.File[file_name]

        # check if file already exists
        dumped_file_checksum = self.file_exists(file_name, path_to)

        if not dumped_file_checksum:
            with open(path_to, "wb") as infile:
                value = file.Value
                if isinstance(value, bytes):
                    infile.write(value)
                else:
                    infile.write(value.encode('utf-8'))
            dumped_file_checksum = self.file_exists(file_name, path_to)
            if not dumped_file_checksum:
                LOGGER.error(f"{file_name} Checksum is not valid")
            return (dumped_file_checksum is not None, path_to, dumped_file_checksum)

        return (True, path_to, dumped_file_checksum)

    def file_exists(self, file_name, path_to):
        """ check if file already exists and checksum is valid """
        if os.path.exists(path_to):
            dumped_file_checksum = self.get_file_checksum(path_to)
            if self.is_checksum_valid(file_name, dumped_file_checksum):
                return dumped_file_checksum
        return None

    @classmethod
    def dump(cls, package, file_name, path_to):
        """ Dump redis file to disk """
        res = (False, path_to, None)
        try:
            pack = Package(package)
            res = pack.dump_file(file_name, path_to)
        except Exception as error:
            LOGGER.error(repr(error))
        return res

    @staticmethod
    def get_or_create(package_name):
        try:
            return Package(package_name)
        except Exception as e:
            return Package(package_name, new=True)
