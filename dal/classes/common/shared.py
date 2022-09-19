"""
   Copyright (C) Mov.ai  - All Rights Reserved
   Unauthorized copying of this file, via any medium is strictly prohibited
   Proprietary and confidential

   Developers:
   - Manuel Silva (manuel.silva@mov.ai) - 2020
   - Tiago Paulino (tiago@mov.ai) - 2020
"""
from threading import RLock

class Shared:
    ''' Shared class implements thread safe local storage '''

    store = {}          # store to save shared data
    lock = RLock()      # lock to make write access thread safe

    def __setattr__(self, name, value):
        ''' use: obj.var_name = var_value'''
        type(self).lock.acquire()
        type(self).store.update({name: value})
        type(self).lock.release()

    def __call__(self, name, value):
        ''' use: obj(var_name, var_value) '''
        self.__setattr__(name, value)

    def __getattr__(self, name):
        ''' use: obj.var_name '''
        try:
            return type(self).store[name]
        except KeyError:
            return None

    def __delattr__(self, name):
        ''' use: del obj.var_name '''
        try:
            type(self).lock.acquire()
            del type(self).store[name]
            type(self).lock.release()
            return True
        except KeyError:
            return False

    def __repr__(self):
        return type(self).store.__repr__()

    def set(self, name, value):
        '''Same as setattr'''
        self.__setattr__(name, value)

    def get(self, name):
        '''Same as getattr'''
        return self.__getattr__(name)

    def delete(self, name):
        '''Same as delattr'''
        return self.__delattr__(name)
