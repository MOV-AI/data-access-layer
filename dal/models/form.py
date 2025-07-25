"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Form Model
"""
from .model import Model


class Form(Model):
    """Form Model"""


Model.register_model_class("Form", Form)
