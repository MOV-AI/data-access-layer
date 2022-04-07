"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Moawiya Mograbi (moawiya@mov.ai) - 2021

    Module that implements a Singleton Base class.
"""
class Singleton(type):
    """
    A Singleton metaclass, every class that is intended to be a Singleton
    have to inherit this class as metaclass, for example:

    class Logger(metaclass=Singleton):
        pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
