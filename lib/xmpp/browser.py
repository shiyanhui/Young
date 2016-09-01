# -*- coding: utf-8 -*-

import logging
from collections import defaultdict

from bson.objectid import ObjectId

from app.chat.document import ChatMessageDocument
from lib.message import WriterManager, MessageTopic

__all__ = ['BrowserClientManager']


class BrowserClientManager(object):
    # {'current_user_id': {'chat_with_user_jid': callback}}
    _callbacks = defaultdict(dict)

    @classmethod
    def add(cls, current_user_id, chat_with_id, callback):
        cls._callbacks[current_user_id][chat_with_id] = callback

    @classmethod
    def remove(cls, current_user_id, chat_with_id):
        try:
            cls._callbacks[current_user_id].pop(chat_with_id)
        except:
            pass

    @classmethod
    def get(cls, current_user_id, chat_with_id):
        callback = None
        try:
            callback = cls._callbacks[current_user_id][chat_with_id]
        except:
            pass

        return callback

    @classmethod
    def new_message(cls, msg):
        '''收到XMPPClient端发来的消息'''

        current_user_id = str(msg['to']).split('@')[0]
        chat_with_id = str(msg['from']).split('@')[0]
        _id = ObjectId(str(msg['subject']))

        callback = cls.get(current_user_id, chat_with_id)

        # 在线, 并且打开了聊天窗口
        if callback:
            try:
                callback(msg)
            except:
                logging.error("Error in browser client callback", exc_info=True)

            ChatMessageDocument.get_collection(pymongo=True).update(
                {'_id': ObjectId(_id)}, {'$set': {'read': True}})

        # 在线但是没有打开聊天窗口. 这种情况下, 交给nsq消息系统处理.
        else:
            WriterManager.pub(MessageTopic.CHAT_MESSAGE_NEW, str(msg['subject']))
