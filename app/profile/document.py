# -*- coding: utf-8 -*-

import pymongo
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from monguo import (
    Document, ReferenceField, DateTimeField, StringField, BooleanField
)

from app.user.document import UserDocument


__all__ = ['LeaveMessageDocument']


class LeaveMessageDocument(Document):
    '''留言

    :Variables:
      - `user`: 被留言者
      - `author`: 留言者
      - `leave_time`: 留言时间
      - `private`: 是不是私密的
      - `content`: 留言内容
      - `replyeder`: 被回复者
    '''
    user = ReferenceField(UserDocument, required=True)
    author = ReferenceField(UserDocument, required=True)
    leave_time = DateTimeField(required=True)
    private = BooleanField(required=True, default=False)
    content = StringField(required=True, max_length=5000)
    replyeder = ReferenceField(UserDocument)

    meta = {
        'collection': 'profile_leave_message'
    }

    @gen.coroutine
    def get_leave_message_number(user_id, visitor_id):
        '''得到留给某人的留言的总个数'''

        query = {
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id)),
            '$or': [
                {'private': False},
                {'private': True, 'author': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(visitor_id)
                )},
                {'private': True, 'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(visitor_id)
                )}
            ]
        }

        count = yield LeaveMessageDocument.find(query).count()
        raise gen.Return(count)

    @gen.coroutine
    def get_leave_message_list(user_id, visitor_id, skip=0, limit=None):
        '''得到某人得到的留言'''

        query = {
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id)),
            '$or': [
                {'private': False},
                {'private': True, 'author': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(visitor_id)
                )},
                {'private': True, 'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(visitor_id)
                )}
            ]
        }

        cursor = LeaveMessageDocument.find(query).sort(
            [('leave_time', pymongo.ASCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        translate = LeaveMessageDocument.translate_dbref_in_document_list
        leave_message_list = yield LeaveMessageDocument.to_list(cursor)
        leave_message_list = yield translate(leave_message_list)

        # message_sum = yield LeaveMessageDocument.get_leave_message_number(
        #     user_id, visitor_id)
        # for i, leave_message in enumerate(leave_message_list):
        #     leave_message['floor'] = message_sum - i - skip

        for i, leave_message in enumerate(leave_message_list):
            leave_message['floor'] = skip + 1 + i

        raise gen.Return(leave_message_list)
