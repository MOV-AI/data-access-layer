"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Alexandre Pires  (alexandre.pires@mov.ai) - 2020
"""
from movai_core_shared.logger import Log
LOGGER = Log.get_logger("API2")
LOGGER.warning(f"DeprecationWarning: \"API2\" module will be deprecated from version Mov.ai 2.2.4, use dal.scopes / dal.models instead")