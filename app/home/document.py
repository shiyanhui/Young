# -*- coding: utf-8 -*-

import re

import pymongo
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from monguo import (
    Document, ReferenceField, DateTimeField, StringField,
    IntegerField, BinaryField
)

from app.user.document import UserDocument, FriendDocument, UserSettingDocument


__all__ = ['StatusDocument', 'StatusLikeDocument', 'StatusCommentDocument',
           'StatusPhotoDocument']


class StatusDocument(Document):
    '''
    :Variables:
      - `author`: 发布者
      - `publish_time`: 发布时间
      - `content`: 内容
      - `like_times`: 点赞次数
      - `comment_times`: 评论次数
    '''

    author = ReferenceField(UserDocument, required=True)
    publish_time = DateTimeField(required=True)
    content = StringField(required=True, max_length=1000)
    like_times = IntegerField(required=True, default=0)
    comment_times = IntegerField(required=True, default=0)

    meta = {
        'collection': 'home_status'
    }

    REGEX_AT = re.compile('@([^@\d\(\)]+)\(([0-9a-f]{24})\)')

    @gen.coroutine
    def translate_at(content):
        '''将status cotent中的@转换成链接'''

        result = StatusDocument.REGEX_AT.findall(content)

        for item in result:
            origin = '@%s(%s)' % (item[0], item[1])
            link = '<a href="/profile/%s" data-userid="%s">@%s</a>' % (
                item[1], item[1], item[0]
            )
            content = content.replace(origin, link)

        raise gen.Return(content)

    @gen.coroutine
    def get_status(status_id, user_id=None):
        '''得到一个status, 是status_list的item'''

        status = yield StatusDocument.find_one({'_id': ObjectId(status_id)})
        if status:
            status = yield StatusDocument.translate_dbref_in_document(status)
            photo = yield StatusPhotoDocument.find_one({
                'status': DBRef(
                    StatusDocument.meta['collection'],
                    ObjectId(status['_id'])
                )
            })

            if photo:
                url = yield StatusPhotoDocument.generate_url(photo['_id'])
                thumbnail = yield StatusPhotoDocument.generate_url(
                    photo['_id'], thumbnail=True
                )

                status['photo'] = {
                    'url': url,
                    'thumbnail': thumbnail
                }

            if user_id is not None:
                status['liked'] = yield StatusLikeDocument.is_liked(
                    status['_id'], user_id
                )
                status['like_list'] = yield StatusLikeDocument.get_like_list(
                    status['_id'], user_id
                )

        raise gen.Return(status)

    @gen.coroutine
    def _extend_status_list(status_list, user_id):
        for status in status_list:
            like_times_f = StatusLikeDocument.get_like_times_can_seen
            status['like_times'] = yield like_times_f(
                status['_id'], user_id
            )

            comment_times_f = StatusCommentDocument.get_comment_times_can_seen
            status['comment_times'] = yield comment_times_f(
                status['_id'], user_id
            )

            photo = yield StatusPhotoDocument.find_one({
                'status': DBRef(
                    StatusDocument.meta['collection'],
                    ObjectId(status['_id'])
                )
            })

            if photo:
                url = yield StatusPhotoDocument.generate_url(photo['_id'])
                thumbnail = yield StatusPhotoDocument.generate_url(
                    photo['_id'], thumbnail=True
                )
                status['photo'] = {
                    'url': url,
                    'thumbnail': thumbnail
                }

            status['liked'] = yield StatusLikeDocument.is_liked(
                status['_id'], user_id
            )
            status['like_list'] = yield StatusLikeDocument.get_like_list(
                status['_id'], user_id
            )

        raise gen.Return(status_list)

    @gen.coroutine
    def get_status_list(user_id, visitor_id, skip=0, limit=None):
        '''按时间从近致远的顺序获取user_id发布的状态

        :Parameters:
          - `user_id`: 用户id
          - `visitor_id`: 当前访问者id
          - `skip`: 默认0
          - `limit`: 默认None
        '''

        cursor = StatusDocument.find({
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            )
        }).sort([('publish_time', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        status_list = yield StatusDocument.to_list(cursor)
        status_list = yield StatusDocument.translate_dbref_in_document_list(
            status_list
        )
        status_list = yield StatusDocument._extend_status_list(
            status_list, visitor_id
        )

        raise gen.Return(status_list)

    @gen.coroutine
    def get_friends_status_list(user_id, skip=0, limit=None):
        '''得到user_id的朋友的状态, 包括自己.

        :Parameters:
          - `user_id`: 用户id
          - `skip`: 默认0
          - `limit`: 默认None
        '''

        friend_list = yield FriendDocument.get_friend_list(user_id)
        shielded_friend_list = yield FriendDocument.get_shielded_friends(
            user_id
        )
        blocked_friend_list = yield FriendDocument.get_blocked_friends(
            user_id
        )

        all_friend_dbref_list = [
            DBRef(UserDocument.meta['collection'], ObjectId(friend['_id']))
            for friend in friend_list
        ]

        shielded_friend_dbref_list = [
            DBRef(UserDocument.meta['collection'], ObjectId(friend['_id']))
            for friend in shielded_friend_list
        ]

        blocked_friend_dbref_list = [
            DBRef(UserDocument.meta['collection'], ObjectId(friend['_id']))
            for friend in blocked_friend_list
        ]

        friend_dbref_list = [
            DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        ]

        for friend in all_friend_dbref_list:
            if (friend not in shielded_friend_dbref_list and
                    friend not in blocked_friend_dbref_list):
                friend_dbref_list.append(friend)

        cursor = StatusDocument.find({
            'author': {'$in': friend_dbref_list}
        }).sort([('publish_time', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        status_list = yield StatusDocument.to_list(cursor)
        status_list = yield StatusDocument.translate_dbref_in_document_list(
            status_list
        )
        status_list = yield StatusDocument._extend_status_list(
            status_list, user_id
        )

        raise gen.Return(status_list)

    @gen.coroutine
    def get_status_number(user_id):
        '''得到某一个人的已发表的微博的数量'''

        status_number = yield StatusDocument.find({
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            )
        }).count()

        raise gen.Return(status_number)

    @gen.coroutine
    def can_see(status, user_id):
        '''判断某人能否看到某状态.

        :Parameters:
          - `status`: 状态, 是id或者document
          - `user_id`: 相关用户
        '''

        can = False

        if isinstance(status, (str, ObjectId)):
            status = yield StatusDocument.find_one({'_id': ObjectId(status)})

        if status:
            if isinstance(status['author'], DBRef):
                author = status['author'].id
            elif isinstance(status['author'], dict):
                author = status['author']['_id']
            else:
                raise gen.Return(can)

            is_friend = yield FriendDocument.is_friend(user_id, author)
            user_setting = yield UserSettingDocument.get_user_setting(author)

            if (str(author) == str(user_id) or is_friend or
                    user_setting['allow_stranger_visiting_profile']):
                can = True

        raise gen.Return(can)


class StatusLikeDocument(Document):
    '''赞

    :Variables:
      - `status`: 相关状态
      - `liker`: 点赞者
      - `like_time`: 点赞时间
    '''
    status = ReferenceField(StatusDocument, required=True)
    liker = ReferenceField(UserDocument, required=True)
    like_time = DateTimeField(required=True)

    meta = {
        'collection': 'home_status_like'
    }

    @gen.coroutine
    def _get_status_liker_cursor(status, user_id):
        friend_ids = yield FriendDocument.get_same_friends(
            status['author']['_id'], user_id
        )

        friend_ids += [
            DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            DBRef(
                UserDocument.meta['collection'],
                ObjectId(status['author']['_id'])
            )
        ]

        cursor = StatusLikeDocument.find({
            'status': DBRef(
                StatusDocument.meta['collection'],
                ObjectId(status['_id'])
            ),
            'liker': {'$in': friend_ids}
        })

        raise gen.Return(cursor)

    @gen.coroutine
    def get_like_list(status_id, user_id, skip=0, limit=None):
        '''得到赞列表, 只能包括我和该状态发布者共同好友

        :Parameters:
          - `status_id`: 状态id
          - `user_id`: 查看该状态的人
          - `skip`: 0
          - `limit`: None
        '''

        like_list = []

        status = yield StatusDocument.find_one({
            '_id': ObjectId(status_id)
        })
        if status:
            status = yield StatusDocument.translate_dbref_in_document(status)

            if status['author']['_id'] == ObjectId(user_id):
                cursor = StatusLikeDocument.find({
                    'status': DBRef(
                        StatusDocument.meta['collection'],
                        ObjectId(status['_id'])
                    )
                })
            else:
                can_see = yield StatusDocument.can_see(status, user_id)
                if not can_see:
                    raise gen.Return(like_list)

                cursor = yield StatusLikeDocument._get_status_liker_cursor(
                    status, user_id
                )

            cursor = cursor.sort([('like_time', pymongo.ASCENDING)]).skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)

            translate = StatusLikeDocument.translate_dbref_in_document_list
            like_list = yield StatusLikeDocument.to_list(cursor)
            like_list = yield translate(like_list)

        raise gen.Return(like_list)

    @gen.coroutine
    def is_liked(status_id, user_id):
        status = DBRef(StatusDocument.meta['collection'], ObjectId(status_id))
        liker = DBRef(UserDocument.meta['collection'], ObjectId(user_id))

        like = yield StatusLikeDocument.find_one({
            'status': status, 'liker': liker
        })
        raise gen.Return(True if like else False)

    @gen.coroutine
    def get_like_times(status_id):
        '''得到点赞次数, 所有人的'''

        like_times = yield StatusLikeDocument.find({
            'status': DBRef(
                StatusDocument.meta['collection'],
                ObjectId(status_id)
            )
        }).count()

        raise gen.Return(like_times)

    @gen.coroutine
    def get_like_times_can_seen(status_id, user_id):
        '''得到某一个人能够看到的赞的次数'''

        status = yield StatusDocument.get_status(status_id)
        if not status:
            raise gen.Return(0)

        if ObjectId(status['author']['_id']) == ObjectId(user_id):
            cnt = yield StatusLikeDocument.get_like_times(status_id)
            raise gen.Return(cnt)

        can_see = yield StatusDocument.can_see(status, user_id)
        if not can_see:
            raise gen.Return(0)

        cursor = yield StatusLikeDocument._get_status_liker_cursor(
            status, user_id
        )
        cnt = yield cursor.count()

        raise gen.Return(cnt)

    @gen.coroutine
    def insert_one(document):
        like_id = yield StatusLikeDocument.insert(document)
        like_times = yield StatusLikeDocument.get_like_times(
            document['status'].id
        )

        yield StatusDocument.update(
            {'_id': ObjectId(document['status'].id)},
            {'$set': {'like_times': like_times}}
        )

        raise gen.Return(like_id)

    @gen.coroutine
    def remove_one(query):
        like = yield StatusLikeDocument.find_one(query)
        if like:
            yield StatusLikeDocument.remove(query)

            like_times = yield StatusLikeDocument.get_like_times(
                like['status'].id
            )
            yield StatusDocument.update(
                {'_id': ObjectId(like['status'].id)},
                {'$set': {'like_times': like_times}}
            )

        raise gen.Return()


class StatusCommentDocument(Document):
    '''状态的评论.

    :Variables:
      - `status`: 相关的状态
      - `commenter`: 评论者
      - `comment_time`: 评论时间
      - `content`: 评论内容
      - `replyeder`: 被回复者, 如果有此属性, 说明该评论是回复某人的
    '''

    status = ReferenceField(StatusDocument, required=True)
    author = ReferenceField(UserDocument, required=True)
    comment_time = DateTimeField(required=True)
    content = StringField(required=True, max_length=200)
    replyeder = ReferenceField(UserDocument)

    meta = {
        'collection': 'home_status_comment'
    }

    @gen.coroutine
    def get_comment(comment_id):
        '''得到某一条评论, 是comment_list的一个item'''

        comment = yield StatusCommentDocument.find_one({
            '_id': ObjectId(comment_id)
        })
        if comment:
            comment = yield StatusCommentDocument.translate_dbref_in_document(
                comment
            )

        raise gen.Return(comment)

    @gen.coroutine
    def get_comment_list(status_id, user_id, skip=0, limit=None):
        '''得到某一状态的评论, 只能看到共同好友和自己的评论.

        :Parameters:
          - `status_id`: 相关的状态
          - `user_id`: 查看评论者
          - `skip`: 默认0
          - `limit`: 默认None
        '''

        comment_list = []

        status = yield StatusDocument.find_one({'_id': ObjectId(status_id)})
        if status:
            status = yield StatusDocument.translate_dbref_in_document(status)
            if status['author']['_id'] == ObjectId(user_id):
                cursor = StatusCommentDocument.find({
                    'status': DBRef(
                        StatusDocument.meta['collection'],
                        ObjectId(status['_id'])
                    )
                })
            else:
                can_see = yield StatusDocument.can_see(status, user_id)
                if not can_see:
                    raise gen.Return(comment_list)

                friend_ids = yield FriendDocument.get_same_friend_ids(
                    status['author']['_id'], user_id
                )

                friend_ids += [
                    DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(user_id)
                    ),
                    DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(status['author']['_id'])
                    )
                ]

                cursor = StatusCommentDocument.find({
                    'status': DBRef(
                        StatusDocument.meta['collection'],
                        ObjectId(status['_id'])
                    ),
                    'author': {'$in': friend_ids},
                    '$or': [
                        {'replyeder': {'$exists': False}},
                        {'replyeder': {'$exists': True, '$in': friend_ids}}
                    ]
                })

            cursor = cursor.sort(
                [('comment_time', pymongo.ASCENDING)]
            ).skip(skip)

            if limit is not None:
                cursor = cursor.limit(limit)

            translate = StatusCommentDocument.translate_dbref_in_document_list
            comment_list = yield StatusCommentDocument.to_list(cursor)
            comment_list = yield translate(comment_list)

        raise gen.Return(comment_list)

    @gen.coroutine
    def get_comment_times(status_id):
        '''得到某一个评论的评论次数, 所有人的评论'''

        comment_times = yield StatusCommentDocument.find({
            'status': DBRef(
                StatusDocument.meta['collection'],
                ObjectId(status_id)
            )
        }).count()

        raise gen.Return(comment_times)

    @gen.coroutine
    def get_comment_times_can_seen(status_id, user_id):
        '''得到某一个人能够看到的评论次数'''

        status = yield StatusDocument.get_status(status_id)
        if not status:
            raise gen.Return(0)

        if ObjectId(status['author']['_id']) == ObjectId(user_id):
            cnt = yield StatusCommentDocument.get_comment_times(status_id)
            raise gen.Return(cnt)

        can_see = yield StatusDocument.can_see(status, user_id)
        if not can_see:
            raise gen.Return(0)

        friend_ids = yield FriendDocument.get_same_friend_ids(
            status['author']['_id'], user_id
        )

        friend_ids += [
            DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            DBRef(
                UserDocument.meta['collection'],
                ObjectId(status['author']['_id'])
            )
        ]

        cnt = yield StatusCommentDocument.find({
            'status': DBRef(
                StatusDocument.meta['collection'],
                ObjectId(status['_id'])
            ),
            'author': {'$in': friend_ids},
            '$or': [
                {'replyeder': {'$exists': False}},
                {'replyeder': {'$exists': True, '$in': friend_ids}}
            ]
        }).count()

        raise gen.Return(cnt)

    @gen.coroutine
    def insert_one(document):
        comment_id = yield StatusCommentDocument.insert(document)
        comment_times = yield StatusCommentDocument.get_comment_times(
            document['status'].id
        )

        yield StatusDocument.update(
            {'_id': ObjectId(document['status'].id)},
            {'$set': {'comment_times': comment_times}}
        )

        raise gen.Return(comment_id)


class StatusPhotoDocument(Document):
    '''状态图片

    :Variables:
      - `status`: 相关的状态
      - `name`: 照片名称
      - `body`: 相片内容
      - `thumbnail`: 相片略缩图
      - `content_type`: 照片格式
      - `upload_time`: 上传时间
    '''

    status = ReferenceField(StatusDocument, required=True)
    name = StringField(required=True, max_length=50)
    body = BinaryField(required=True)
    thumbnail = BinaryField(required=True)
    content_type = StringField(required=True)
    upload_time = DateTimeField(required=True)

    meta = {
        'collection': 'home_status_photo'
    }

    @gen.coroutine
    def generate_url(photo_id, thumbnail=False):
        '''生成照片的url'''

        url = '/status/photo/%s' % photo_id
        if thumbnail:
            url += '/thumbnail'

        raise gen.Return(url)
