"""Copyright (C) Mov.ai  - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential

Developers:
- Moawiya Mograbi (moawiya@mov.ai) - 2022

Archive main module, suppose to be an interface in order to interact
with general archive/database module (git/redis/...)

in order to use it an instance of Archive should be called
for example:
    archive = Archive(user=None)
    archive.get('file', remote, version)
"""
from os import getenv
from .basearchive import BaseArchive
# in order to register Git Archive
from dal.api.gitapi import GitManager

# default archive is GIT
BaseArchive.set_active_archive(getenv("ACTIVE_ARCHIVE", "Git"))
Archive = BaseArchive()

__all__ = [
    "Archive"
]
