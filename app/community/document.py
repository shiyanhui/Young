# -*- coding: utf-8 -*-

import re
import os
import random
from datetime import datetime

import pymongo
from tornado import gen
from bson.objectid import ObjectId
from bson.dbref import DBRef
from monguo import (
    Document, StringField, IntegerField, ReferenceField, ListField,
    BooleanField, DateTimeField
)

from app.user.document import UserDocument
from app.base.document import ImageDocument
from app.message.document import MessageDocument

__all__ = ['NodeDocument', 'NodeAvatarDocument', 'TopicDocument',
           'TopicLikeDocument', 'TopicCommentDocument',
           'TopicStatisticsDocument']


class NodeDocument(Document):
    '''
    :Variables:
      - `name`: 节点名称
      - `topic_number`: 节点下有多少话题, 添加该属性是为了高效的根据话题多少对节点进行排名
      - `father`: 父节点
      - `category`: 节点类型, 比如内建
      - `sort`: 对于某些特殊节点的排序方式
      - `description`: 节点描述
    '''

    BUILTIN = 'builtin'

    name = StringField(required=True, max_length=20, unique=True)
    topic_number = IntegerField(required=True, default=0)
    father = ReferenceField('NodeDocument')

    category = StringField(max_length=30)
    sort = IntegerField()
    description = StringField(max_length=300)
    last_modified_by = ReferenceField(UserDocument)
    last_modified_time = DateTimeField()

    meta = {
        'collection': 'community_node'
    }

    @gen.coroutine
    def get_node(node_id):
        node = yield NodeDocument.find_one({'_id': ObjectId(node_id)})
        if node:
            node = yield NodeDocument.translate_dbref_in_document(node)
            url = yield NodeAvatarDocument.get_node_avatar_url(node['_id'])
            if url:
                node['avatar'] = url

        raise gen.Return(node)

    @gen.coroutine
    def get_node_list_by_category(category, skip=0, limit=None):
        cursor = NodeDocument.find({'category': category}).sort(
            [('sort', pymongo.ASCENDING), ('topic_number', pymongo.DESCENDING)]
        ).skip(skip)

        if isinstance(limit, int) and limit >0:
            cursor = cursor.limit(limit)

        node_list = yield NodeDocument.to_list(cursor)
        raise gen.Return(node_list)

    @gen.coroutine
    def get_hot_node_list(size=None):
        cursor = NodeDocument.find({'category': {'$exists': False}}).sort(
            [('topic_number', pymongo.DESCENDING)]
        )

        if size is not None:
            cursor = cursor.limit(size)

        node_list = yield NodeDocument.to_list(cursor)
        raise gen.Return(node_list)

    @gen.coroutine
    def get_top_header_node_list():
        '''得到社区模块上边部分的节点'''

        node_list = yield NodeDocument.get_node_list_by_category(
            NodeDocument.BUILTIN
        )

        raise gen.Return(node_list)


class NodeAvatarDocument(Document):
    '''节点头像, 注意image里边包含有64x64略缩图.

    :Variables:
      - `node`: 节点
      - `image`: 图片
      - `uploader`: 上传者
      - `upload_time`: 上传时间
    '''
    node = ReferenceField(NodeDocument, required=True)
    image = ReferenceField(ImageDocument, required=True)
    uploader = ReferenceField(UserDocument, required=True)
    upload_time = DateTimeField(required=True)

    meta = {
        'collection': 'community_node_avatar'
    }

    @gen.coroutine
    def get_node_avatar_url(node_id):
        '''得到node头像的url'''

        node = yield NodeAvatarDocument.find_one({
            'node': DBRef(NodeDocument.meta['collection'], ObjectId(node_id))
        })

        url = None
        if node:
            url = yield ImageDocument.generate_image_url(
                node['image'].id, thumbnail=True
            )

        raise gen.Return(url)

    @gen.coroutine
    def remove_one(query):
        node_avatar = yield NodeAvatarDocument.find_one(query)
        if node_avatar:
            yield ImageDocument.remove({
                '_id': ObjectId(node_avatar['image'].id)
            })

        yield NodeAvatarDocument.remove(query)
        raise gen.Return()


class TopicDocument(Document):
    '''
    :Variables:
      - `author`: 话题者
      - `publish_time`: 话题时间
      - `last_update_time`: 最后更新时间, 添加此项是为了更好的排名, 当有新的评论时更新此项
      - `title`: 标题
      - `anonymous`: 是否匿名
      - `nodes`: 所属节点
      - `read_times`: 阅读次数
      - `like_times`: 点赞次数
      - `comment_times`: 评论次数
      - `top`: 是否被置顶
      - `perfect`: 是否被加精
      - `content`: 话题的内容
      - `images`: 话题内容里边的图片url, 每当话题内容改变时, 应该改变images
    '''

    author = ReferenceField(UserDocument, required=True)
    publish_time = DateTimeField(required=True)
    last_update_time = DateTimeField(required=True)
    title = StringField(required=True, max_length=100)
    anonymous = BooleanField(required=True, default=False)
    nodes = ListField(ReferenceField(NodeDocument), required=True)
    read_times = IntegerField(required=True, default=0)
    like_times = IntegerField(required=True, default=0)
    comment_times = IntegerField(required=True, default=0)
    top = BooleanField(required=True, default=False)
    perfect = BooleanField(required=True, default=False)

    content = StringField(max_length=10 ** 5)
    images = ListField(StringField())

    meta = {
        'collection': 'community_topic'
    }

    @gen.coroutine
    def _extend_images(topic):
        regex = re.compile('^/image/([a-f0-9]{24})/?$')

        images = []
        for image in topic['images']:
            url = thumbnail = image
            if regex.match(image):
                thumbnail = os.path.join(image, 'thumbnail')

            images.append({
                'url': url,
                'thumbnail': thumbnail
            })

        return images

    @gen.coroutine
    def get_topic(topic_id, user_id):
        '''
        :Parameters:
          - `topic_id`: 话题id
          - `user_id`: 判断该user是否赞了该话题
        '''

        topic = yield TopicDocument.find_one({'_id': ObjectId(topic_id)})
        if topic:
            topic['author'] = yield UserDocument.translate_dbref(
                topic['author']
            )

            liked = yield TopicLikeDocument.is_liked(topic_id, user_id)
            last_comment = yield TopicCommentDocument.get_last_comment(
                topic['_id']
            )

            topic.update({
                'liked': liked,
                'last_comment': last_comment
            })

            if 'images' in topic and topic['images']:
                topic['images'] = yield TopicDocument._extend_images(topic)

            for i, node in enumerate(topic['nodes']):
                topic['nodes'][i] = yield NodeDocument.translate_dbref(node)

        raise gen.Return(topic)

    @gen.coroutine
    def get_top_topic_list(user_id=None, skip=0, limit=None):
        '''得到置顶的帖子'''

        query = {'top': True}

        cursor = TopicDocument.find(query).sort(
            [('publish_time', pymongo.DESCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        topic_list = yield TopicDocument.to_list(cursor)
        for topic in topic_list:
            topic['author'] = yield UserDocument.translate_dbref(
                topic['author']
            )
            topic['last_comment'] = yield TopicCommentDocument.get_last_comment(
                topic['_id']
            )

            if 'images' in topic and topic['images']:
                topic['images'] = yield TopicDocument._extend_images(topic)

            if user_id is not None:
                topic['liked'] = yield TopicLikeDocument.is_liked(
                    topic['_id'], user_id
                )

            for i, node in enumerate(topic['nodes']):
                topic['nodes'][i] = yield NodeDocument.translate_dbref(node)

        raise gen.Return(topic_list)

    @gen.coroutine
    def get_topic_list(node_id=None, user_id=None, sort=None,
                       skip=0, limit=None):
        '''
        :Parameters:
          - `node_id`: 如果node_id不为None, 那么得到该节点下的话题
          - `sort`: 排序方式, 只可能为time或者popularity
          - `skip`: 默认0
          - `limit`: 默认None

        NOTE: NEED CACHE !!
        '''

        def score(topic):
            '''
            公式为: score = like_times + comment_times/2 + read_times/5

            即: 1 * like_times = 2 * comment_times = 5 * read_times
            '''
            return (topic['like_times'] + topic['comment_times'] / 2.0 +
                    topic['read_times'] / 5.0)

        top_topic_list = yield TopicDocument.get_top_topic_list(user_id)
        if node_id is not None:
            query = {
                'nodes': DBRef(
                    NodeDocument.meta['collection'], ObjectId(node_id)
                )
            }
        else:
            query = {
                '_id': {'$nin': [ObjectId(t['_id']) for t in top_topic_list]}
            }

        cursor = TopicDocument.find(query)
        if sort == 'time' or sort is None:
            cursor = cursor.sort(
                [('last_update_time', pymongo.DESCENDING)]
            ).skip(skip)

            if limit is not None:
                cursor = cursor.limit(limit)

            topic_list = yield TopicDocument.to_list(cursor)
        else:
            topic_list = yield TopicDocument.to_list(cursor)
            topic_list.sort(
                cmp=lambda x, y: -1 if score(x) < score(y) else 1,
                reverse=True
            )

            if limit is not None:
                topic_list = topic_list[skip: skip + limit]
            else:
                topic_list = topic_list[skip:]

        for topic in topic_list:
            topic['author'] = yield UserDocument.translate_dbref(
                topic['author']
            )
            topic['last_comment'] = yield TopicCommentDocument.get_last_comment(
                topic['_id']
            )

            if 'images' in topic and topic['images']:
                topic['images'] = yield TopicDocument._extend_images(topic)

            if user_id is not None:
                topic['liked'] = yield TopicLikeDocument.is_liked(
                    topic['_id'], user_id
                )

            for i, node in enumerate(topic['nodes']):
                topic['nodes'][i] = yield NodeDocument.translate_dbref(node)

        if not node_id and skip == 0 and top_topic_list:
            topic_list = top_topic_list + topic_list

        raise gen.Return(topic_list)

    @gen.coroutine
    def get_topic_number(node_id=None):
        '''统计某节点下共有多少话题'''

        if node_id:
            count = yield TopicDocument.find({
                'nodes': DBRef(
                    NodeDocument.meta['collection'],
                    ObjectId(node_id)
                )
            }).count()
        else:
            count = yield TopicDocument.count()

        raise gen.Return(count)

    @gen.coroutine
    def get_topic_number_by_someone(user_id, visitor_id=None):
        '''得到某人发布的状态总的个数'''

        query = {
            'author': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        }
        # if visitor_id is not None:
        #     if ObjectId(user_id) != ObjectId(visitor_id):
        #         query.update({'anonymous': False})

        query.update({'anonymous': False})
        topic_number = yield TopicDocument.find(query).count()

        raise gen.Return(topic_number)

    @gen.coroutine
    def get_hot_topic_list(period=None, skip=0, limit=None):
        '''在一段时间内的热门话题, 跟赞/评论/阅读的次数有关.

        :Parameters:
          - `period`: 从现在往前算起, 多长时间之内的新闻
          - `skip`: 默认0
          - `limit`: 最终得到的热门话题的个数

        NOTE: NEED CACHE!
        '''

        def score(topic):
            '''
            公式为: score = like_times + comment_times/2 + read_times/5

            即: 1 * like_times = 2 * comment_times = 5 * read_times
            '''
            return (topic['like_times'] + topic['comment_times'] / 2.0 +
                    topic['read_times'] / 5.0)

        query = {}
        if period is not None:
            query.update({'last_update_time': {'$gt': datetime.now() - period}})

        cursor = TopicDocument.find(query)
        topic_list = yield TopicDocument.to_list(cursor)
        topic_list.sort(
            cmp=lambda x, y: -1 if score(x) < score(y) else 1, reverse=True
        )

        if limit is not None:
            topic_list = topic_list[skip: skip + limit]
        else:
            topic_list = topic_list[skip:]

        raise gen.Return(topic_list)

    @gen.coroutine
    def get_recommend_topic_list(topic_id, size=10):
        '''根据某一话题推荐话题'''

        topic_list = []

        topic = yield TopicDocument.find_one({'_id': ObjectId(topic_id)})
        if topic:
            query = {
                '$and': [
                    {'_id': {'$ne': ObjectId(topic_id)}},
                    {'$or': [{'nodes': node} for node in topic['nodes']]}
                ]
            }
            count = yield TopicDocument.find(query).count()
            if count > size:
                skip = random.randint(0, count - size)
                cursor = TopicDocument.find(query).skip(skip).limit(size)
            else:
                cursor = TopicDocument.find(query)

            topic_list = yield TopicDocument.to_list(cursor)
            if not topic_list or len(topic_list) < size:
                query = {
                    '$and': [
                        {'_id': {'$ne': ObjectId(topic_id)}}
                    ]
                }
                count = yield TopicDocument.find(query).count()
                if count > size:
                    skip = random.randint(0, count - size)
                    cursor = TopicDocument.find(query).skip(skip).limit(size)
                else:
                    cursor = TopicDocument.find(query)

                topic_list = yield TopicDocument.to_list(cursor)

            for topic in topic_list:
                topic['author'] = yield UserDocument.translate_dbref(
                    topic['author']
                )

        raise gen.Return(topic_list)

    @gen.coroutine
    def get_topic_list_by_someone(author_id, skip=0, limit=None):
        '''得到某人的话题'''

        cursor = TopicDocument.find({
            'author': DBRef(
                UserDocument.meta['collection'], ObjectId(author_id)
            )
        }).sort([('publish_time', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        topic_list = yield TopicDocument.to_list(cursor)
        for topic in topic_list:
            topic['author'] = yield UserDocument.translate_dbref(
                topic['author']
            )
            topic['last_comment'] = yield TopicCommentDocument.get_last_comment(
                topic['_id']
            )

            for i, node in enumerate(topic['nodes']):
                topic['nodes'][i] = yield NodeDocument.translate_dbref(node)

        raise gen.Return(topic_list)

    @gen.coroutine
    def insert_one(document):
        topic_id = yield TopicDocument.insert(document)

        for node in document['nodes']:
            topic_number = yield TopicDocument.get_topic_number(node.id)
            yield NodeDocument.update(
                {'_id': ObjectId(node.id)},
                {'$set': {'topic_number': topic_number}}
            )

        new_document = {
            'author': document['author'],
            'publish_time': document['publish_time'],
            'nodes': document['nodes'],
            'anonymous': document['anonymous'],
            'data_type': 'topic',
            'data': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }
        yield TopicStatisticsDocument.insert(new_document)

        raise gen.Return(topic_id)

    @gen.coroutine
    def delete_one(topic_id):
        topic = DBRef(
            TopicDocument.meta['collection'], ObjectId(topic_id)
        )

        yield TopicDocument.remove({'_id': ObjectId(topic_id)})
        yield TopicStatisticsDocument.remove({'data': topic})
        yield TopicLikeDocument.delete(topic_id)
        yield TopicCommentDocument.delete(topic_id)
        yield MessageDocument.remove({'data': topic})

        raise gen.Return()


class TopicLikeDocument(Document):
    '''
    :Variables:
      - `topic`: 话题
      - `liker`: 点赞者
      - `like_time`: 点赞时间
    '''

    topic = ReferenceField(TopicDocument, required=True)
    liker = ReferenceField(UserDocument, required=True)
    like_time = DateTimeField(required=True)

    meta = {
        'collection': 'community_topic_like'
    }

    @gen.coroutine
    def get_like_list(topic_id, skip=0, limit=None):
        cursor = TopicLikeDocument.find({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }).sort([('like_time', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        like_list = yield TopicLikeDocument.to_list(cursor)
        for like in like_list:
            like['liker'] = yield UserDocument.translate_dbref(like['liker'])

        raise gen.Return(like_list)

    @gen.coroutine
    def get_like_times(topic_id):
        like_times = yield TopicLikeDocument.find({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }).count()

        raise gen.Return(like_times)

    @gen.coroutine
    def insert_one(document):
        like_id = yield TopicLikeDocument.insert(document)
        like_times = yield TopicLikeDocument.get_like_times(
            document['topic'].id
        )
        yield TopicDocument.update(
            {'_id': ObjectId(document['topic'].id)},
            {'$set': {'like_times': like_times}})

        raise gen.Return(like_id)

    @gen.coroutine
    def remove_one(query):
        like = yield TopicLikeDocument.find_one(query)
        if like:
            yield TopicLikeDocument.remove(query)
            like_times = yield TopicLikeDocument.get_like_times(
                like['topic'].id
            )

            yield TopicDocument.update(
                {'_id': ObjectId(like['topic'].id)},
                {'$set': {'like_times': like_times}})

            yield MessageDocument.remove({
                'data': DBRef(TopicLikeDocument.meta['collection'],
                              ObjectId(like['_id']))
            })

        raise gen.Return()

    @gen.coroutine
    def delete(topic_id):
        '''将与某一topic有关的topic都删除掉'''

        like_list = yield TopicLikeDocument.get_like_list(topic_id)
        for like in like_list:
            yield TopicLikeDocument.remove_one({'_id': ObjectId(like['_id'])})

        raise gen.Return()

    @gen.coroutine
    def is_liked(topic_id, user_id):
        topic_like = yield TopicLikeDocument.find_one({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id)),
            'liker': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })

        raise gen.Return(True if topic_like else False)


class TopicCommentDocument(Document):
    '''
    :Variables:
      - `topic`: 被评论的话题
      - `author`: 评论者
      - `comment_time`: 评论时间
      - `content`: 评论内容
      - `anonymous`: 是否匿名
      - `replyeder`: 被回复的人
    '''

    topic = ReferenceField(TopicDocument, required=True)
    author = ReferenceField(UserDocument, required=True)
    comment_time = DateTimeField(required=True)
    content = StringField(required=True, max_length=10 ** 5)
    anonymous = BooleanField(required=True, default=False)
    replyeder = ReferenceField(UserDocument)

    meta = {
        'collection': 'community_topic_comment'
    }

    @gen.coroutine
    def get_comment_list(topic_id, skip=0, limit=None):
        cursor = TopicCommentDocument.find({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }).sort([('comment_time', pymongo.ASCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        comment_list = yield TopicCommentDocument.to_list(cursor)
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
    def get_comment_times(topic_id):
        comment_times = yield TopicCommentDocument.find({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }).count()

        raise gen.Return(comment_times)

    @gen.coroutine
    def insert_one(document):
        comment_id = yield TopicCommentDocument.insert(document)
        topic_id = document['topic'].id

        comment_times = yield TopicCommentDocument.get_comment_times(topic_id)
        yield TopicDocument.update(
            {'_id': ObjectId(topic_id)},
            {'$set': {'comment_times': comment_times,
                      'last_update_time': datetime.now()}}
        )

        topic = yield TopicDocument.find_one({'_id': ObjectId(topic_id)})
        if topic:
            new_document = {
                'author': document['author'],
                'publish_time': document['comment_time'],
                'nodes': topic['nodes'],
                'anonymous': document['anonymous'],
                'data_type': 'topic_comment',
                'data': DBRef(TopicCommentDocument.meta['collection'],
                              ObjectId(comment_id))
            }
            yield TopicStatisticsDocument.insert(new_document)

        raise gen.Return(comment_id)

    @gen.coroutine
    def get_last_comment(topic_id):
        '''得到某一话题的最后一个回复'''

        cursor = TopicCommentDocument.find({
            'topic': DBRef(TopicDocument.meta['collection'], ObjectId(topic_id))
        }).sort([('comment_time', pymongo.DESCENDING)]).limit(1)

        comment_list = yield TopicCommentDocument.to_list(cursor)

        last_comment = None
        if comment_list:
            last_comment = comment_list[0]
            last_comment['author'] = yield UserDocument.translate_dbref(
                last_comment['author']
            )

        raise gen.Return(last_comment)

    @gen.coroutine
    def delete_one(comment_id):
        comment = yield TopicCommentDocument.find_one({
            '_id': ObjectId(comment_id)
        })
        if comment:
            yield TopicCommentDocument.remove({'_id': ObjectId(comment_id)})

            comment_times = yield TopicCommentDocument.get_comment_times(
                comment['topic'].id
            )

            yield TopicDocument.update(
                {'_id': ObjectId(comment['topic'].id)},
                {'$set': {'comment_times': comment_times}}
            )

            yield MessageDocument.remove({
                'data': DBRef(TopicCommentDocument.meta['collection'],
                              ObjectId(comment_id))
            })

        raise gen.Return()

    @gen.coroutine
    def delete(topic_id):
        '''将与某一个话题有关的评论都删除'''

        comment_list = yield TopicCommentDocument.get_comment_list(topic_id)
        for comment in comment_list:
            yield TopicCommentDocument.delete_one(comment['_id'])

        raise gen.Return()


class TopicStatisticsDocument(Document):
    '''
    话题统计, 添加该集合的目的是为了更好的统计活跃用户

    :Variables:
      - `author`: 用户
      - `publish_time`: 发表时间, 可以根据发表时间来确定一段时间内的活跃用户,而不是所有时间段
                        的活跃用户
      - `nodes`: 话题或者话题评论所属的节点
      - `anonymous`: 是否匿名, 如果匿名的话, 则不算
      - `data_type`: 所保存的数据类型
      - `data`: 数据
    '''

    author = ReferenceField(UserDocument, required=True)
    publish_time = DateTimeField(required=True)
    nodes = ListField(ReferenceField(NodeDocument), required=True)
    anonymous = BooleanField(required=True)
    data_type = StringField(required=True, candidate=['topic', 'topic_comment'])
    data = ReferenceField(required=True)

    meta = {
        'collection': 'community_topic_statistics'
    }

    @gen.coroutine
    def get_active_author_list(node_id=None, period=None, skip=0, limit=None):
        '''得到某一节点下的活跃用户排名

        :Parameters:
          - `node_id`: 如果不为None, 则表示某一节点下的活跃用户
          - `period`: 如果不为None, 则为timedelta类型, 表示从现在往前算多长时间内的活跃用户
          - `skip`: 默认0
          - `limit`: 默认None
        '''

        query = {
            'anonymous': False,
        }
        if node_id is not None:
            query.update({
                'nodes': DBRef(NodeDocument.meta['collection'],
                               ObjectId(node_id))
            })

        if period is not None:
            begin = datetime.now() - period
            query.update({'publish_time': {'$gt': begin}})

        aggregate_pipeline = [
            {'$match': query},
            {'$group': {'_id': {'author': '$author'}, 'times': {'$sum': 1}}},
            {'$sort': {'times': -1}},
            {'$skip': skip},
            {'$limit': limit}
        ]

        cursor = TopicStatisticsDocument.aggregate(aggregate_pipeline)

        author_list = []
        while (yield cursor.fetch_next):
            item = cursor.next_object()
            author_list.append({
                'author': item['_id']['author'],
                'times': item['times']
            })

        author_list = yield UserDocument.translate_dbref_in_document_list(
            author_list
        )

        raise gen.Return(author_list)
