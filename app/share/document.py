# -*- coding: utf-8 -*-

import random
from datetime import datetime, timedelta

import pymongo
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from monguo import (
    Document, StringField, IntegerField, BooleanField,
    DateTimeField, ReferenceField, FloatField, GridFileField
)

from app.user.document import UserDocument
from app.message.document import MessageDocument

__all__ = ['ShareCategoryDocument', 'ShareDocument',
           'ShareLikeDocument', 'ShareCommentDocument', 'ShareDownloadDocument']


class ShareCategoryDocument(Document):
    '''分享类别

    :Variables:
      - `name`: 名称
      - `sort`: 按从小到大排序
    '''

    name = StringField(required=True, max_length=10)
    sort = IntegerField(required=True)

    meta = {
        'collection': 'share_category'
    }

    @gen.coroutine
    def get_share_category_list():
        cursor = ShareCategoryDocument.find().sort(
            [('sort', pymongo.ASCENDING)]
        )
        category_list = yield ShareCategoryDocument.to_list(cursor)

        raise gen.Return(category_list)


class ShareDocument(Document):
    '''分享

    :Variables:
      - `title`: 分享标题
      - `category`: 类别
      - `filename`: 文件标题
      - `content_type`: 文件类型, 根据文件头判断出文件类型, 而不是文件名称,
                        存储的是MIME, 在后续处理里边更新该属性
      - `passed`: 审核是否通过
      - `description`: 描述
      - `uploader`: 上传者
      - `upload_time`: 上传时间
      - `cost`: 下载需要多少金币
      - `like_times`: 点赞次数
      - `comment_times`: 评论次数
      - `download_times`: 下载次数
      - `score`: 评分

      - `origin_file`: 在后续处理里边更新该属性
      - `mime`: 文件真正的格式，保存的是content_type，如果不存在那就说明没
                判断出来
    '''
    title = StringField(required=True, max_length=1000)
    category = StringField(required=True)
    filename = StringField(required=True, max_length=500)
    content_type = StringField(required=True, max_length=100)
    passed = BooleanField(required=True, default=True)
    description = StringField(required=True, max_length=10 ** 5)
    uploader = ReferenceField(UserDocument, required=True)
    upload_time = DateTimeField(required=True)
    cost = IntegerField(required=True, min_value=0)
    like_times = IntegerField(required=True, default=0)
    comment_times = IntegerField(required=True, default=0)
    download_times = IntegerField(required=True, default=0)
    score = FloatField(required=True, default=-1)

    origin_file = GridFileField()
    mime = StringField()

    meta = {
        'collection': 'share'
    }

    @gen.coroutine
    def get_share(share_id, user_id=None):
        share = yield ShareDocument.find_one({'_id': ObjectId(share_id)})
        if share:
            share = yield ShareDocument.translate_dbref_in_document(share)
            share['like_list'] = yield ShareLikeDocument.get_like_list(
                share['_id'], limit=10
            )

            fs = ShareDocument.get_gridfs()
            gridout = yield fs.get(ObjectId(share['origin_file']))
            share['size'] = gridout.length

            if user_id is not None:
                share['liked'] = yield ShareLikeDocument.is_liked(
                    share_id, user_id
                )

        raise gen.Return(share)

    @gen.coroutine
    def get_share_list(category=None, sort='time', skip=0, limit=None):
        def score(share):
            '''
            公式为: score = like_times + comment_times/2 + read_times/5

            即: 1 * download_times = 2 * like_times = 5 * comment_times
            '''
            return (share['download_times'] + share['like_times'] / 2.0 +
                    share['comment_times'] / 5.0)

        assert sort in ['time', 'popularity', 'score']

        query = {"passed": True}
        if category is not None:
            query.update({'category': category})

        cursor = ShareDocument.find(query)

        if sort != 'popularity':
            _sort = 'upload_time' if sort == 'time' else 'score'
            cursor = cursor.sort([(_sort, pymongo.DESCENDING)]).skip(skip)

            if limit is not None:
                cursor = cursor.limit(limit)

            share_list = yield ShareDocument.to_list(cursor)
        else:
            share_list = yield ShareDocument.to_list(cursor)
            share_list.sort(
                cmp=lambda x, y: -1 if score(x) < score(y) else 1,
                reverse=True
            )

            if limit is not None:
                share_list = share_list[skip: skip + limit]
            else:
                share_list = share_list[skip:]

        share_list = yield ShareDocument.translate_dbref_in_document_list(
            share_list
        )

        for share in share_list:
            share['like_list'] = yield ShareLikeDocument.get_like_list(
                share['_id'], limit=10
            )

        raise gen.Return(share_list)

    @gen.coroutine
    def get_recommend_share_list(share_id, size=10):
        '''根据某一话题推荐话题'''

        share_list = []

        share = yield ShareDocument.find_one({'_id': ObjectId(share_id)})
        if share:
            query = {
                '_id': {'$ne': ObjectId(share_id)},
                'category': share['category'],
                "passed": True
            }
            count = yield ShareDocument.find(query).count()
            if count > size:
                skip = random.randint(0, count - size)
                cursor = ShareDocument.find(query).skip(skip).limit(size)
            else:
                cursor = ShareDocument.find(query)

            share_list = yield ShareDocument.to_list(cursor)

        raise gen.Return(share_list)

    @gen.coroutine
    def get_share_number(category=None):
        '''得到某一类下分享总数'''

        query = {'passed': True}
        if category is not None:
            query.update({'category': category})

        count = yield ShareDocument.find(query).count()
        raise gen.Return(count)

    @gen.coroutine
    def get_uploader_number(category=None):
        '''得到某一类下上传者总数'''

        query = {'passed': True}
        if category is not None:
            query.update({'category': category})

        cursor = ShareDocument.aggregate([
            {'$match': query},
            {'$group': {'_id': '$uploader'}}
        ])

        num = 0
        while (yield cursor.fetch_next):
            cursor.next_object()
            num += 1

        raise gen.Return(num)

    @gen.coroutine
    def get_uploader_list(skip=0, limit=None):
        '''按照上传者上传数量大->小得到上传者'''

        piplines = [
            {'$match': {'passed': True}},
            {'$group': {'_id': '$uploader', 'upload_times': {'$sum': 1}}},
            {'$sort': {'upload_times': -1}},
            {'$skip': skip}
        ]
        if limit is not None:
            piplines.append({'$limit': limit})

        cursor = ShareDocument.aggregate(piplines)

        r = []
        while (yield cursor.fetch_next):
            r.append(cursor.next_object())

        translate = ShareDocument.translate_dbref_in_document_list

        uploader_list = yield translate(r)
        for uploader in uploader_list:
            uploader['uploader'] = uploader['_id']

        raise gen.Return(uploader_list)


class ShareLikeDocument(Document):
    '''
    :Variables:
      - `share`: 分享
      - `liker`: 点赞者
      - `like_time`: 点赞时间
    '''

    share = ReferenceField(ShareDocument, required=True)
    liker = ReferenceField(UserDocument, required=True)
    like_time = DateTimeField(required=True)

    meta = {
        'collection': 'share_like'
    }

    @gen.coroutine
    def get_like_list(share_id, skip=0, limit=None):
        cursor = ShareLikeDocument.find({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }).sort([('like_time', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        like_list = yield ShareLikeDocument.to_list(cursor)
        for like in like_list:
            like['liker'] = yield UserDocument.translate_dbref(like['liker'])

        raise gen.Return(like_list)

    @gen.coroutine
    def get_like_times(share_id):
        like_times = yield ShareLikeDocument.find({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }).count()

        raise gen.Return(like_times)

    @gen.coroutine
    def insert_one(document):
        like_id = yield ShareLikeDocument.insert(document)

        like_times = yield ShareLikeDocument.get_like_times(
            document['share'].id
        )
        yield ShareDocument.update(
            {'_id': ObjectId(document['share'].id)},
            {'$set': {'like_times': like_times}}
        )

        raise gen.Return(like_id)

    @gen.coroutine
    def remove_one(query):
        like = yield ShareLikeDocument.find_one(query)
        if like:
            yield ShareLikeDocument.remove(query)

            like_times = yield ShareLikeDocument.get_like_times(
                like['share'].id
            )
            yield ShareDocument.update(
                {'_id': ObjectId(like['share'].id)},
                {'$set': {'like_times': like_times}}
            )

            yield MessageDocument.remove({
                'data': DBRef(
                    ShareLikeDocument.meta['collection'],
                    ObjectId(like['_id'])
                )
            })

        raise gen.Return()

    @gen.coroutine
    def is_liked(share_id, user_id):
        share_like = yield ShareLikeDocument.find_one({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            ),
            'liker': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            )
        })

        raise gen.Return(True if share_like else False)


class ShareCommentDocument(Document):
    '''
    :Variables:
      - `share`: 被评论的分享
      - `author`: 评论者
      - `comment_time`: 评论时间
      - `content`: 评论内容
      - `anonymous`: 是否匿名
      - `replyeder`: 被回复的人
    '''

    share = ReferenceField(ShareDocument, required=True)
    author = ReferenceField(UserDocument, required=True)
    comment_time = DateTimeField(required=True)
    content = StringField(required=True, max_length=10 ** 5)
    anonymous = BooleanField(required=True, default=False)
    replyeder = ReferenceField(UserDocument)

    meta = {
        'collection': 'share_comment'
    }

    @gen.coroutine
    def get_comment_list(share_id, skip=0, limit=None):
        cursor = ShareCommentDocument.find({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }).sort([('comment_time', pymongo.ASCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        comment_list = yield ShareCommentDocument.to_list(cursor)

        for i, comment in enumerate(comment_list):
            comment['floor'] = skip + 1 + i
            comment['author'] = yield UserDocument.translate_dbref(
                comment['author']
            )
            if 'replyeder' in comment:
                comment['replyeder'] = yield UserDocument.translate_dbref(
                    comment['replyeder']
                )

        raise gen.Return(comment_list)

    @gen.coroutine
    def get_comment_times(share_id):
        comment_times = yield ShareCommentDocument.find({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }).count()

        raise gen.Return(comment_times)

    @gen.coroutine
    def insert_one(document):
        comment_id = yield ShareCommentDocument.insert(document)

        comment_times = yield ShareCommentDocument.get_comment_times(
            document['share'].id
        )
        yield ShareDocument.update(
            {'_id': ObjectId(document['share'].id)},
            {'$set': {'comment_times': comment_times}}
        )

        raise gen.Return(comment_id)

    @gen.coroutine
    def delete_one(comment_id):
        comment = yield ShareCommentDocument.find_one({
            '_id': ObjectId(comment_id)
        })
        if comment:
            yield ShareCommentDocument.remove({
                '_id': ObjectId(comment_id)
            })

            comment_times = yield ShareCommentDocument.get_comment_times(
                comment['share'].id
            )
            yield ShareDocument.update(
                {'_id': ObjectId(comment['share'].id)},
                {'$set': {'comment_times': comment_times}}
            )

            yield MessageDocument.remove({
                'data': DBRef(
                    ShareCommentDocument.meta['collection'],
                    ObjectId(comment_id)
                )
            })

        raise gen.Return()


class ShareDownloadDocument(Document):
    '''下载

    :Variables:
      - `share`: 分享
      - `downloader`: 下载者
      - `download_time`: 下载时间
    '''
    share = ReferenceField(ShareDocument, required=True)
    downloader = ReferenceField(UserDocument, required=True)
    download_time = DateTimeField(required=True)

    meta = {
        'collection': 'share_download'
    }

    @gen.coroutine
    def get_download_times(share_id):
        download_times = yield ShareDownloadDocument.find({
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }).count()

        raise gen.Return(download_times)

    @gen.coroutine
    def get_hot_download_list(period=timedelta(days=7), size=6):
        '''得到最近下载的比较多的资源的列表'''

        cursor = ShareDownloadDocument.aggregate([
            {'$match': {'download_time': {'$gt': datetime.now() - period}}},
            {'$group': {'_id': '$share', 'download_times': {'$sum': 1}}},
            {'$sort': {'download_times': -1}},
            {'$limit': size}
        ])

        r = []
        while (yield cursor.fetch_next):
            r.append(cursor.next_object())
        r = yield ShareDownloadDocument.translate_dbref_in_document_list(r)

        hot_download_list = [item['_id'] for item in r]

        translate = ShareDocument.translate_dbref_in_document_list
        hot_download_list = yield translate(hot_download_list)

        if not hot_download_list:
            hot_download_list = yield ShareDocument.get_share_list(
                sort='popularity', limit=6
            )

        raise gen.Return(hot_download_list)
