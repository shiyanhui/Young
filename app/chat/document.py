# -*- coding: utf-8 -*-

import pymongo
from bson.objectid import ObjectId
from bson.dbref import DBRef
from tornado import gen
from monguo import (
    Document, StringField, ListField, ReferenceField, DateTimeField,
    BooleanField
)

import setting
from app.user.document import UserDocument

__all__ = ['ChatMessageDocument']


class ChatMessageDocument(Document):
    '''两个人之间的私聊, 把两个人之间的聊天历史保存起来.

    :Variables:
      - `body`: 消息内容
      - `betwwen`: 谁跟谁之间的私聊, 添加此属性是为了方便查询两人之间的私聊信息.
      - `sender`: 发送者
      - `send_time`: 发送时间
      - `recipient`: 接收者
      - `received`: 是否被接收, 如果对方离线(未和Ejabberd服务器建立连接), 那么将会存储为离线消息
      - `read`: 是否被阅读, 接收后不一定被阅读
    '''

    body = StringField(required=True, max_length=1000)
    between = ListField(ReferenceField(UserDocument), required=True)
    sender = ReferenceField(UserDocument, required=True)
    send_time = DateTimeField(required=True)
    recipient = ReferenceField(UserDocument, required=True)
    received = BooleanField(required=True, default=False)
    read = BooleanField(required=True, default=False)

    meta = {
        'collection': 'chat_message'
    }

    @gen.coroutine
    def get_chat_message_list(user_id, skip=0, limit=None):
        '''得到与某人有关的私聊信息'''

        user_dbref = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        query = {
            '$or': [{'sender': user_dbref}, {'recipient': user_dbref}]
        }

        cursor = ChatMessageDocument.find(query).sort(
            [('send_time', pymongo.DESCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        chat_message_list = yield ChatMessageDocument.to_list(cursor)
        chat_message_list = yield ChatMessageDocument.translate_dbref_in_document_list(
            chat_message_list)

        raise gen.Return(chat_message_list)

    @gen.coroutine
    def get_history_messages(id_a, id_b, since):
        '''得到两人之间的历史消息'''

        limit = setting.history_messages_number_per_time

        user_a = DBRef(UserDocument.meta['collection'], ObjectId(id_a))
        user_b = DBRef(UserDocument.meta['collection'], ObjectId(id_b))

        cursor = ChatMessageDocument.find({
            'between': user_a, 'between': user_b, 'send_time': {'$lt': since}
        })

        cursor = ChatMessageDocument.find(
            {'$or': [{'between': [user_a, user_b]},
                     {'between': [user_b, user_a]}], 'send_time': {'$lt': since}}
        ).sort([('send_time', pymongo.DESCENDING)]).limit(limit)

        result = yield ChatMessageDocument.to_list(cursor)
        raise gen.Return(result[::-1])

    def set_read(recipient_id):
        '''将某人所有的未读信息设置为已读'''

        ChatMessageDocument.get_collection(True).update(
            {'recipient': DBRef(UserDocument.meta['collection'], ObjectId(recipient_id))},
            {'$set': {'read': True}},
            multi=True
        )

    def has_unread_chat_message(recipient_id):
        '''判断是否有未读的信息'''

        message = ChatMessageDocument.get_collection(pymongo=True).find_one({
            'recipient': DBRef(UserDocument.meta['collection'], ObjectId(recipient_id)),
            'read': False
        })

        return True if message else False

    def get_message_number(recipient_id, read=None):
        '''得到消息数量'''

        query = {
            'recipient': DBRef(UserDocument.meta['collection'], ObjectId(recipient_id))
        }

        if read is not None:
            assert isinstance(read, bool)
            query.update({'read': read})

        count = ChatMessageDocument.get_collection(True).find(query).count()
        return count

    def get_unread_messages(user_id):
        '''得到某人未读信息'''

        recipient = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        result = ChatMessageDocument.get_collection(True).aggregate([
            {'$match': {'recipient': recipient, 'received': True, 'read': False}},
            {'$sort': {'send_time': 1}},
            {'$group': {'_id': '$sender',
                        'messages': {'$push': {'send_time': '$send_time',
                                               'body': '$body',
                                               'sender': '$sender'}}}}
        ])
        return result['result']
