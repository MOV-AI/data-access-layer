"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2022

   Archive main module, suppose to be an interface in order to interact
   with general archive/database module (git/redis/...)

   in order to use it an instance of Archive should be called
   for example:
       archive = Archive()
       archive.get('file', remote, version)
"""


from .basearchive import BaseArchive
# in order to register Git Archive
from dal.api.gitapi import GitManager

BaseArchive.set_active_archive("Git")
Archive = BaseArchive()

__all__ = [
    "Archive"
]
