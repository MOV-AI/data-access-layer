"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi  (moawiya@mov.ai) - 2022

   DAL module - Data Access Layer
   handles all kind of data processing/fetching/modifying
   all data related operations will be delt within this module.
"""

from .classes.filesystem import FileSystem
from .api.dalapi import SlaveDAL, MasterDAL, RedisProtocols
from .api.gitapi import (
    SlaveGitManager,
    MasterGitManager,
    GitManager
)
from .movaidb import MovaiDB, Configuration

__all__ = [
    # classes
    "SlaveDAL",
    "MasterDAL",
    "RedisProtocols",
    "FileSystem",
    "SlaveGitManager",
    "MasterGitManager",
    "GitManager",
    "MovaiDB",
    "Configuration"
    ]
