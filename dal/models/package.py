"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Package Model
"""

import hashlib
from typing import Tuple
from dal.scopes import scopes
from .model import Model

class Package(Model):
   """
      Currently disabled, use deprecated one instead
   """

    # default __init__

   def get_checksum(self, file_name: str) -> str:
      """ Get file's checksum """
      return self.File[file_name].Checksum

   @staticmethod
   def get_file_checksum(file_path: str) -> str:
      """ Calculates a file's checksum """
      csum = hashlib.md5()
      # let it blow
      with open(file_path, "rb") as fd:
         for line in fd:
            csum.update(line)

      return csum.hexdigest()

   def add(*args, **kwargs):
      """ This shouldn't be needed in the new API """
      raise NotImplementedError()

   def is_checksum_valid(self, file_name: str, checksum: str) -> bool:
      """ Check checksum """
      return checksum == self.get_checksum(file_name)

   def file_exists(self, file_name: str,  path_to: str) -> str:
      """ Check existing file against computed checksum """
      try:
         csum = self.get_file_checksum(path_to)
         if self.is_checksum_valid(file_name, csum):
            return csum
      except FileNotFoundError:
         pass
      return None

   def dump_file(self, file_name: str, path_to: str) -> Tuple[bool, str, str]:
      """ Dump a file to storage """
      file = self.File[file_name]

      csum = self.file_exists(file_name, path_to)

      if csum is None:
         with open(path_to, 'wb') as fd:
            contents = file.Value
            try:
               fd.write(contents.encode())
            except AttributeError:
               # bytes has no attribute encode
               fd.write(contents)
         # check checksum again
         csum = self.file_exists(file_name, path_to)
         if csum is None:
            raise RuntimeError("File checksum mismatch")
      return (True, path_to, csum)

   @staticmethod
   def dump(package:str, file_name:str, path_to: str) -> Tuple[bool, str, str]:
      """ Dump a file to storage """
      try:
         return scopes.from_path(package, scope='Package').dump_file(file_name, path_to)
      except KeyError:  # Scope does not exist
         return (False, path_to, None)

   @staticmethod
   def get_or_create(package_name: str) -> Model:
      """ Tries to get a package, creates it if doesn't exist """
      try:
         return scopes.from_path(package_name, scope='Package')
      except KeyError:
         return scopes().create('Package', package_name)


Model.register_model_class('Package', Package)
