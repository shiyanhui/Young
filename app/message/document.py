# -*- coding: utf-8 -*-

import pymongo
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from monguo import (
    Document, ReferenceField, StringField, DateTimeField, BooleanField)

from lib.message.topic import MessageTopic
from app.home.document import StatusDocument
from app.user.document import UserDocument
from app.chat.document import ChatMessageDocument

__all__ = ['MessageDocument', "MessageTopic"]


class MessageDocument(Document):
    '''消息系统中的消息

    :Variables:
      - `sender`: 发送者, 系统消息发送者不存在, 用户之间的消息必须存在, 哪些是系统消息,
                  见MessageTopic
      - `recipient`: 接收者
      - `message_type`: 消息类型
      - `time`: 消息产生的时间
      - `received`: 是否被接收, 前端是否已接收, 接收后未必已读
      - `read`: 接收者是否已经阅读
      - `data`: 相关的数据
    '''

    sender = ReferenceField(UserDocument)
    recipient = ReferenceField(UserDocument, required=True)
    message_type = StringField(
        required=True,
        candidate=[
            'comment:status', 'comment:topic', 'comment:market_goods',
            'comment:market_need', 'comment:activity',

            'reply:status', 'reply:topic', 'reply:surround_shop',
            'reply:surround_goods', 'reply:market_goods', 'reply:market_need',
            'reply:activity', 'reply:news', 'reply:leavemessage',

            'like:status', 'like:topic', 'like:market_goods',
            'like:market_need', 'like:activity'
        ].extend(MessageTopic.all_topic)
    )
    time = DateTimeField(required=True)
    received = BooleanField(required=True, default=False)
    read = BooleanField(required=True, default=False)
    data = ReferenceField()

    meta = {
        'collection': 'message'
    }

    @gen.coroutine
    def get_message_list(recipient_id, message_topic=None, read=None,
                         skip=0, limit=None):
        '''得到消息列表'''

        query = MessageDocument.get_query(recipient_id, message_topic)

        if read is not None:
            assert isinstance(read, bool)
            query.update({'read': read})

        cursor = MessageDocument.find(query).sort(
            [('time', pymongo.DESCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        message_list = yield MessageDocument.to_list(cursor)
        for message in message_list:
            if 'sender' in message:
                message['sender'] = yield UserDocument.translate_dbref(
                    message['sender']
                )

            message['recipient'] = yield UserDocument.translate_dbref(
                message['recipient']
            )

            if 'data' not in message:
                continue

            if str(message['data'].collection) == str(
                    StatusDocument.meta['collection']):
                message['data'] = yield StatusDocument.get_status(
                    message['data'].id
                )
                continue

            message['data'] = yield Document.translate_dbref(
                message['data']
            )

            if message['data']:
                message['data'] = yield Document.translate_dbref_in_document(
                    message['data'], depth=2
                )

                if 'status' in message['data']:
                    message['data']['status'] = yield StatusDocument.get_status(
                        message['data']['status']['_id']
                    )

        raise gen.Return(message_list)

    @gen.coroutine
    def set_read(recipient_id, message_topic=None):
        '''将消息设置为已读'''

        query = MessageDocument.get_query(recipient_id, message_topic)
        yield MessageDocument.update(
            query, {'$set': {'received': True, 'read': True}}, multi=True
        )

        raise gen.Return()

    def set_read_sync(recipient_id, message_topic=None):
        '''将消息设置为已读'''

        query = MessageDocument.get_query(recipient_id, message_topic)
        MessageDocument.get_collection(True).update(
            query, {'$set': {'received': True, 'read': True}}, multi=True
        )

    def set_received(recipient_id, message_topic=None):
        '''将消息设置为已接受'''

        query = MessageDocument.get_query(recipient_id, message_topic)
        MessageDocument.get_collection(True).update(
            query, {'$set': {'received': True}}, multi=True
        )

    def get_query(recipient_id, message_topic=None):
        '''得到查询'''

        query = {
            'recipient': DBRef(
                UserDocument.meta['collection'],
                ObjectId(recipient_id)
            )
        }

        if message_topic is not None:
            if message_topic == MessageTopic._COMMENT_AND_REPLY:
                query.update({'message_type': {'$regex': '(comment|reply):.*'}})
            elif message_topic == MessageTopic.COMMENT:
                query.update({'message_type': {'$regex': 'comment:.*'}})
            elif message_topic == MessageTopic.REPLY:
                query.update({'message_type': {'$regex': 'reply:.*'}})
            elif message_topic == MessageTopic.LIKE:
                query.update({'message_type': {'$regex': 'like:.*'}})
            elif message_topic == MessageTopic._FRIENDS_DYNAMIC:
                query.update({
                    'message_type': {
                        '$in': [
                            MessageTopic.STATUS_NEW,
                            MessageTopic.TOPIC_NEW,
                            MessageTopic.SHARE_NEW
                        ]
                    }
                })
            else:
                query.update({'message_type': message_topic})

        return query

    def get_message_number(recipient_id, message_topic=None, read=None):
        '''得到相关消息的数量'''

        query = MessageDocument.get_query(recipient_id, message_topic)
        if read is not None:
            assert isinstance(read, bool)
            query.update({'read': read})

        count = MessageDocument.get_collection(
            pymongo=True).find(query).count()

        return count

    def has_unreceived(recipient_id):
        '''是否有未读的消息'''

        message = MessageDocument.get_collection(pymongo=True).find_one({
            'recipient': DBRef(
                UserDocument.meta['collection'],
                ObjectId(recipient_id)
            ),
            'received': False,
            'read': False
        })

        return True if message else False

    def get_unread_message_numbers(recipient_id):
        '''得到未读的消息个数'''

        unread_message_numbers = {
            MessageTopic._FRIENDS_DYNAMIC: MessageDocument.get_message_number(
                recipient_id, MessageTopic._FRIENDS_DYNAMIC, read=False
            ),

            MessageTopic._COMMENT_AND_REPLY: MessageDocument.get_message_number(
                recipient_id, MessageTopic._COMMENT_AND_REPLY, read=False
            ),

            MessageTopic.LIKE: MessageDocument.get_message_number(
                recipient_id, MessageTopic.LIKE, read=False
            ),

            MessageTopic.CHAT_MESSAGE_NEW: ChatMessageDocument.get_message_number(
                recipient_id, read=False
            ),

            MessageTopic.LEAVE_MESSAGE_NEW: MessageDocument.get_message_number(
                recipient_id, MessageTopic.LEAVE_MESSAGE_NEW, read=False
            ),

            MessageTopic.FRIEND_REQUEST_NEW: MessageDocument.get_message_number(
                recipient_id, MessageTopic.FRIEND_REQUEST_NEW, read=False
            )
        }

        return unread_message_numbers
