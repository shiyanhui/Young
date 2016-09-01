# -*- coding: utf-8 -*-

__all__ = ['BrowserCallbackManager']


class BrowserCallbackManager(object):
    '''管理服务器挂起的浏览器端请求.

    _callbacks的结构为:
    {
        user_id: callback,
    }
    '''

    _callbacks = {}

    @classmethod
    def add(cls, user_id, callback):
        cls._callbacks.update({str(user_id): callback})

    @classmethod
    def remove(cls, user_id):
        try:
            cls._callbacks.pop(str(user_id))
        except:
            pass

    @classmethod
    def get(cls, user_id):
        return cls._callbacks.get(str(user_id), None)
