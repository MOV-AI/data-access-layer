"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Tiago Teixeira  (tiago.teixeira@mov.ai) - 2020

   Widget Model
"""
from .model import Model


class Widget(Model):
    """Widget Model"""

    # default __init__


Model.register_model_class("Widget", Widget)
