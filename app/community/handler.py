# -*- coding: utf-8 -*-

from StringIO import StringIO
from datetime import datetime, timedelta

import Image
from tornado import gen
from tornado.web import authenticated, asynchronous, HTTPError
from bson.objectid import ObjectId
from bson.dbref import DBRef
from bson.binary import Binary

from lib.message import WriterManager
from young.handler import BaseHandler
from app.community.setting import COMMUNITY_SETTINGS
from app.message.document import MessageDocument, MessageTopic
from app.home.document import StatusDocument
from app.home.setting import HOME_SETTINGS
from app.base.setting import WEALTH_SETTINGS
from app.user.document import (
    UserDocument, UserSettingDocument,
    UserActivityDocument, WealthRecordDocument, FriendDocument
)
from app.community.document import (
    NodeDocument, NodeAvatarDocument, TopicDocument,
    TopicLikeDocument, TopicCommentDocument, TopicStatisticsDocument
)
from app.community.form import (
    NodeSuggestionForm, TopicNewForm,
    TopicCommentNewForm, TopicCommentMoreForm, TopicLikeForm,
    NodeAvatarSetForm, NodeDescriptionEditTemplateForm,
    NodeDescriptionEditForm, TopicEditForm
)

__all__ = ['CommunityHandler', 'NodeSuggestionHandler',
           'TopicNewHandler', 'TopicHandler', 'TopicCommentNewHandler',
           'TopicCommentMoreHandler', 'TopicLikeHandler', 'NodeHandler',
           'NodeAvatarEditTemplateHandler', 'NodeAvatarSetHandler',
           'NodeDescriptionEditTemplateHandler', 'NodeDescriptionEditHandler',
           'TopicEditHandler', 'TopicDeleteHandler',
           'TopicCommentDeleteHandler']


class CommunityBaseHandler(BaseHandler):
    @gen.coroutine
    def get_sidebar_arguments(self):
        '''得到两侧栏的render变量'''

        user_id = self.current_user['_id']

        status_number = yield StatusDocument.get_status_number(user_id)
        topic_number = yield TopicDocument.get_topic_number_by_someone(
            user_id, visitor_id=user_id
        )

        user_setting = yield UserSettingDocument.find_one({
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })
        login_reward_fetched_today = yield UserActivityDocument.login_reward_fetched(
            user_id
        )
        continuous_login_days = yield UserDocument.get_continuous_login_days(
            user_id
        )

        kwargs = {
            'status_number': status_number,
            'topic_number': topic_number,
            'MessageTopic': MessageTopic,
            'user_setting': user_setting,
            'login_reward_fetched_today': login_reward_fetched_today,
            'continuous_login_days': continuous_login_days,
            'HOME_SETTINGS': HOME_SETTINGS
        }

        raise gen.Return(kwargs)


class CommunityHandler(CommunityBaseHandler):
    @gen.coroutine
    def get(self):
        sort = self.get_argument('sort', "time")
        if sort not in ['time', 'popularity']:
            sort = 'time'

        node = self.get_argument('node', None)
        try:
            page = max(int(self.get_argument("page", 1)), 1)
        except:
            page = 1

        query = {
            'user_id': self.current_user and self.current_user['_id'],
            'sort': sort,
            'skip': (page - 1) * COMMUNITY_SETTINGS["topic_number_per_page"],
            'limit': COMMUNITY_SETTINGS['topic_number_per_page']
        }
        if node:
            node = yield NodeDocument.get_node(node)
            if not node:
                raise HTTPError(404)

            query.update({'node_id': node['_id']})

        topic_list = yield TopicDocument.get_topic_list(**query)
        hot_topic_list = yield TopicDocument.get_hot_topic_list(
            period=timedelta(days=1),
            limit=COMMUNITY_SETTINGS['hot_topic_number']
        )
        hot_node_list = yield NodeDocument.get_hot_node_list(
            size=COMMUNITY_SETTINGS['hot_node_number']
        )
        top_header_node_list = yield NodeDocument.get_top_header_node_list()

        total_page, pages = self.paginate(
            (yield TopicDocument.get_topic_number(node and node['_id'])),
            COMMUNITY_SETTINGS['topic_number_per_page'],
            page
        )

        kwargs = {}
        if self.current_user:
            kwargs = yield self.get_sidebar_arguments()

        kwargs.update({
            'sort': sort,
            'current_node': node,
            'topic_list': topic_list,
            'hot_topic_list': hot_topic_list,
            'top_header_node_list': top_header_node_list,
            'hot_node_list': hot_node_list,
            'page': page,
            'total_page': total_page,
            'pages': pages
        })

        self.render('community/template/community.html', **kwargs)


class TopicHandler(CommunityBaseHandler):
    '''得到某一话题'''

    @gen.coroutine
    def get(self, topic_id):
        topic = yield TopicDocument.get_topic(
            topic_id, self.current_user and self.current_user['_id']
        )
        if not topic:
            raise HTTPError(404)

        if self.current_user and topic['author']['_id'] != self.current_user['_id']:
            yield TopicDocument.update(
                {'_id': topic['_id']}, {'$inc': {'read_times': 1}}
            )

        comment_list = yield TopicCommentDocument.get_comment_list(
            topic['_id'],
            limit=COMMUNITY_SETTINGS['topic_comment_number_per_page']
        )
        recommend_topic_list = yield TopicDocument.get_recommend_topic_list(
            topic_id
        )

        like_list = yield TopicLikeDocument.get_like_list(topic_id)

        kwargs = {
            'topic': topic,
            'comment_list': comment_list,
            'like_list': like_list,
            'recommend_topic_list': recommend_topic_list,
            'COMMUNITY_SETTINGS': COMMUNITY_SETTINGS
        }

        self.render('community/template/topic-one.html', **kwargs)


class TopicNewHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        node_id = self.get_argument("node_id", None)

        node = None
        if node_id:
            node = yield NodeDocument.get_node(node_id)
            if not node:
                node = None

        self.render(
            "community/template/topic-new.html",
            action="new",
            node_one=node
        )

    @authenticated
    @gen.coroutine
    def post(self):
        form = TopicNewForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        title = form.title.data
        content = form.content.data
        nodes = form.nodes.data.split(',')
        anonymous = form.anonymous.data

        nodes = list(set(nodes))

        if len(nodes) > 3:
            response_data = {'error': '节点请不要超过3个！'}

        can_afford = yield UserDocument.can_afford(
            self.current_user['_id'], WEALTH_SETTINGS['topic_new']
        )
        if not can_afford:
            response_data = {'error': '金币不足！'}

        new_nodes = []
        for node in nodes:
            existed = yield NodeDocument.find_one({'name': node})
            if existed:
                node_id = existed['_id']
            else:
                node_id = yield NodeDocument.insert({'name': node})

            new_nodes.append(
                DBRef(NodeDocument.meta['collection'], ObjectId(node_id))
            )

        now = datetime.now()
        document = {
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'title': title,
            'anonymous': anonymous,
            'nodes': new_nodes,
        }

        existed = yield TopicDocument.find_one(document)
        if existed and (now - existed['publish_time'] < timedelta(minutes=1)):
            response_data.update({'error': '你已经发布了一个相同的帖子！'})
        else:
            document.update({'publish_time': now, 'last_update_time': now})

        if not response_data:
            if content:
                document.update({'content': content})

                images = yield self.get_images(content)
                if images:
                    document.update({'images': images})

            topic_id = yield TopicDocument.insert_one(document)

            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'activity_type': UserActivityDocument.TOPIC_NEW,
                'time': now,
                'data': DBRef(
                    TopicDocument.meta['collection'], ObjectId(topic_id)
                )
            }
            activity_id = yield UserActivityDocument.insert(document)

            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'in_out_type': WealthRecordDocument.OUT,
                'activity': DBRef(
                    UserActivityDocument.meta['collection'],
                    ObjectId(activity_id)
                ),
                'quantity': WEALTH_SETTINGS['topic_new'],
                'time': now
            }
            yield WealthRecordDocument.insert(document)
            yield UserDocument.update_wealth(
                self.current_user['_id'], -WEALTH_SETTINGS['topic_new']
            )

            if not anonymous:
                friends = yield FriendDocument.get_reached_friends(
                    self.current_user['_id']
                )

                message_list = []
                for friend in friends:
                    document = {
                        'sender': DBRef(
                            UserDocument.meta['collection'],
                            ObjectId(self.current_user['_id'])
                        ),
                        'recipient': DBRef(
                            UserDocument.meta['collection'],
                            ObjectId(friend['_id'])
                        ),
                        'message_type': MessageTopic.TOPIC_NEW,
                        'time': now,
                        'read': False,
                        'data': DBRef(
                            TopicDocument.meta['collection'],
                            ObjectId(topic_id)
                        )
                    }
                    message_id = yield MessageDocument.insert(document)
                    message_list.append(str(message_id))

                if message_list:
                    try:
                        WriterManager.mpub(MessageTopic.TOPIC_NEW, message_list)
                    except:
                        pass

        self.write_json(response_data)


class TopicEditHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        topic_id = self.get_argument('topic_id', None)
        if not topic_id:
            raise HTTPError(404)

        topic = yield TopicDocument.get_topic(
            topic_id, self.current_user['_id']
        )
        if not topic or topic['author']['_id'] != self.current_user['_id']:
            raise HTTPError(404)

        self.render(
            'community/template/topic-new.html',
            action="edit",
            topic=topic
        )

    @authenticated
    @gen.coroutine
    def post(self):
        form = TopicEditForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        topic_id = form.topic_id.data
        title = form.title.data
        content = form.content.data
        nodes = form.nodes.data.split(',')
        anonymous = form.anonymous.data

        topic = yield TopicDocument.get_topic(
            topic_id, self.current_user['_id']
        )
        if (not topic or len(nodes) > 3 or
                topic['author']['_id'] != self.current_user['_id']):
            raise HTTPError(404)

        nodes = list(set(nodes))

        node_ids = []
        for node in nodes:
            existed = yield NodeDocument.find_one({'name': node})
            if existed:
                node_id = existed['_id']
            else:
                node_id = yield NodeDocument.insert({'name': node})

            node_ids.append(
                DBRef(NodeDocument.meta['collection'], ObjectId(node_id))
            )

        document = {
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'title': title,
            'anonymous': anonymous,
            'nodes': node_ids,
            'content': content
        }

        images = yield self.get_images(content)
        document.update({'images': images})

        topic_id = yield TopicDocument.update(
            {'_id': ObjectId(topic_id)},
            {'$set': document}
        )

        self.write_json(response_data)


class TopicCommentNewHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = TopicCommentNewForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        content = form.content.data
        topic_id = form.topic_id.data
        anonymous = form.anonymous.data
        replyeder_id = form.replyeder_id.data

        replyeder = None
        if replyeder_id:
            replyeder = yield UserDocument.find_one({
                '_id': ObjectId(replyeder_id)
            })
            if not replyeder:
                raise HTTPError(404)

            if anonymous or self.current_user['_id'] == replyeder['_id']:
                raise HTTPError(404)

        topic = yield TopicDocument.find_one({'_id': ObjectId(topic_id)})
        if not topic:
            raise HTTPError(404)

        now = datetime.now()
        document = {
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'topic': DBRef(
                TopicDocument.meta['collection'],
                ObjectId(topic['_id'])
            ),
            'content': content,
            'anonymous': anonymous
        }

        existed = yield TopicCommentDocument.find_one(document)
        if existed and (now - existed['comment_time'] < timedelta(minutes=1)):
            response_data.update({'error': '请不要重复评论！'})
        else:
            document.update({'comment_time': now})

        if not response_data:
            if replyeder:
                document.update({
                    'replyeder': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(replyeder_id)
                    )
                })

            comment_id = yield TopicCommentDocument.insert_one(document)

            activity = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'activity_type': UserActivityDocument.COMMENT,
                'time': now,
                'data': DBRef(
                    TopicCommentDocument.meta['collection'],
                    ObjectId(comment_id)
                )
            }
            yield UserActivityDocument.insert(activity)

            if replyeder:
                recipient_id = replyeder_id
                message_type = 'reply:topic'
                message_topic = MessageTopic.REPLY
            else:
                recipient_id = topic['author'].id
                message_type = 'comment:topic'
                message_topic = MessageTopic.COMMENT

            if (str(self.current_user['_id']) != str(recipient_id) and
                    not anonymous and
                    not (message_topic == MessageTopic.COMMENT and
                         topic['anonymous'])):
                message = {
                    'sender': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'recipient': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(recipient_id)
                    ),
                    'message_type': message_type,
                    'time': now,
                    'read': False,
                    'data': DBRef(
                        TopicCommentDocument.meta['collection'],
                        ObjectId(comment_id)
                    )
                }
                message_id = yield MessageDocument.insert(message)
                WriterManager.pub(message_topic, message_id)

            comment_times = yield TopicCommentDocument.get_comment_times(
                topic_id
            )

            document.update({
                '_id': ObjectId(comment_id),
                'author': self.current_user,
                'floor': comment_times
            })

            if replyeder:
                document.update({'replyeder': replyeder})

            item = self.render_string(
                'community/template/topic-comment-list-item.html',
                comment=document
            )
            response_data.update({'item': item})

        self.write_json(response_data)


class TopicCommentMoreHandler(CommunityBaseHandler):
    '''加载更多话题评论'''

    @gen.coroutine
    def post(self):
        form = TopicCommentMoreForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        page = form.page.data
        topic_id = form.topic_id.data

        skip = COMMUNITY_SETTINGS['topic_comment_number_per_page'] * page
        limit = COMMUNITY_SETTINGS['topic_comment_number_per_page']

        comment_list = yield TopicCommentDocument.get_comment_list(
            topic_id, skip, limit
        )

        html = ''.join(
            self.render_string(
                'community/template/topic-comment-list-item.html',
                comment=comment
            ) for comment in comment_list
        )

        self.write_json({'html': html, 'page': page + 1})


class TopicLikeHandler(CommunityBaseHandler):
    '''点赞'''

    @authenticated
    @gen.coroutine
    def post(self):
        response_data = {}

        form = TopicLikeForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        topic_id = form.topic_id.data

        topic = yield TopicDocument.find_one({'_id': ObjectId(topic_id)})
        if not topic:
            raise HTTPError(404)

        can_afford = yield UserDocument.can_afford(
            self.current_user['_id'], WEALTH_SETTINGS['like']
        )

        if not can_afford and str(
                self.current_user['_id']) != str(topic['author'].id):
            response_data.update({'error': '金币不足！'})

        topic_dbref = DBRef(
            TopicDocument.meta['collection'],
            ObjectId(topic_id)
        )
        liker_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(self.current_user['_id'])
        )

        document = {'topic': topic_dbref, 'liker': liker_dbref}

        liked = yield TopicLikeDocument.is_liked(
            topic_id, self.current_user['_id']
        )

        if not liked and not response_data:
            now = datetime.now()
            document.update({'like_time': now})
            like_id = yield TopicLikeDocument.insert_one(document)

            if str(self.current_user['_id']) != str(topic['author'].id):
                document = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'activity_type': UserActivityDocument.LIKE,
                    'time': now,
                    'data': DBRef(
                        TopicLikeDocument.meta['collection'],
                        ObjectId(like_id)
                    )
                }
                activity_id = yield UserActivityDocument.insert(document)

                # 赞者
                document = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'in_out_type': WealthRecordDocument.OUT,
                    'activity': DBRef(
                        UserActivityDocument.meta['collection'],
                        ObjectId(activity_id)
                    ),
                    'quantity': WEALTH_SETTINGS['like'],
                    'time': now
                }
                yield WealthRecordDocument.insert(document)
                yield UserDocument.update_wealth(
                    self.current_user['_id'], -WEALTH_SETTINGS['like']
                )

                # 被赞者
                document = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(topic['author'].id)
                    ),
                    'in_out_type': WealthRecordDocument.IN,
                    'activity': DBRef(
                        UserActivityDocument.meta['collection'],
                        ObjectId(activity_id)
                    ),
                    'quantity': WEALTH_SETTINGS['like'],
                    'time': now
                }
                yield WealthRecordDocument.insert(document)
                yield UserDocument.update_wealth(
                    topic['author'].id, WEALTH_SETTINGS['like']
                )

                document = {
                    'sender': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'recipient': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(topic['author'].id)
                    ),
                    'message_type': 'like:topic',
                    'time': now,
                    'read': False,
                    'data': DBRef(
                        TopicLikeDocument.meta['collection'],
                        ObjectId(like_id)
                    )
                }

                message_id = yield MessageDocument.insert(document)
                WriterManager.pub(MessageTopic.LIKE, message_id)

        like_times = yield TopicLikeDocument.get_like_times(topic_id)
        response_data.update({'like_times': like_times})

        self.write_json(response_data)


class NodeHandler(CommunityBaseHandler):
    '''得到某一个节点'''

    @gen.coroutine
    def get(self, node_id):
        current_node = yield NodeDocument.get_node(node_id)
        if not current_node:
            raise HTTPError(404)

        sort = self.get_argument('sort', "time")
        if sort not in ['time', 'popularity']:
            sort = 'time'

        try:
            page = max(int(self.get_argument("page", 1)), 1)
        except:
            page = 1

        node_avatar_url = yield NodeAvatarDocument.get_node_avatar_url(
            node_id
        )
        topic_list = yield TopicDocument.get_topic_list(
            node_id=node_id,
            user_id=self.current_user and self.current_user['_id'],
            sort=sort,
            skip=(page - 1) * COMMUNITY_SETTINGS["topic_number_per_page"],
            limit=COMMUNITY_SETTINGS['topic_number_per_page']
        )
        active_author_list = yield TopicStatisticsDocument.get_active_author_list(
            node_id=node_id,
            period=timedelta(days=100),
            limit=10
        )
        total_page, pages = self.paginate(
            (yield TopicDocument.get_topic_number(current_node["_id"])),
            COMMUNITY_SETTINGS['topic_number_per_page'],
            page
        )

        kwargs = {
            'current_node': current_node,
            'node_avatar_url': node_avatar_url,
            'sort': sort,
            'topic_list': topic_list,
            'active_author_list': active_author_list,
            'page': page,
            'total_page': total_page,
            'pages': pages
        }

        self.render('community/template/node-one.html', **kwargs)


class NodeSuggestionHandler(CommunityBaseHandler):
    @authenticated
    @asynchronous
    def get(self):
        nodes = []

        form = NodeSuggestionForm(self.request.arguments)
        if form.validate():
            res = self.es.search(
                index="young",
                doc_type=NodeDocument.meta["collection"],
                body={
                    "query": {
                        "match": {
                            "name": form.q.data
                        }
                    }
                }
            )
            nodes = [r["_source"]['name'] for r in res["hits"]["hits"]]

        self.write_json(nodes)


class NodeAvatarEditTemplateHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        self.render('community/template/node-avatar-edit-template.html')


class NodeAvatarSetHandler(CommunityBaseHandler):
    '''设置头像'''

    @authenticated
    @gen.coroutine
    def post(self):
        from app.base.document import ImageDocument

        form = NodeAvatarSetForm(self.request.arguments)
        if not form.validate() or 'avatar' not in self.request.files:
            raise HTTPError(404)

        node_id = form.node_id.data
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        target_width = form.target_width.data

        node = yield NodeDocument.find_one({'_id': ObjectId(node_id)})
        if not node:
            raise HTTPError(404)

        upload_file = self.request.files['avatar'][0]

        now = datetime.now()
        document = {
            'name': upload_file['filename'],
            'body': Binary(upload_file['body']),
            'content_type': upload_file['content_type'].split('/')[1].upper(),
            'uploader': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'upload_time': now
        }

        image = Image.open(StringIO(upload_file['body']))

        if image.size[0] < target_width:
            target_width = image.size[0]

        scale = image.size[0] * 1.0 / target_width

        x = int(x * scale)
        y = int(y * scale)
        w = int(w * scale)
        h = int(h * scale)

        box = (x, y, x + w, y + h)
        image = image.crop(box)

        output = StringIO()
        image = image.resize((64, 64), Image.ANTIALIAS).save(
            output, document['content_type'], quality=100
        )
        document.update({'thumbnail': Binary(output.getvalue())})
        output.close()

        yield NodeAvatarDocument.remove_one({
            'node': DBRef(
                NodeDocument.meta['collection'],
                ObjectId(node_id)
            )
        })

        image_id = yield ImageDocument.insert(document)

        document = {
            'node': DBRef(
                NodeDocument.meta['collection'],
                ObjectId(node_id)
            ),
            'image': DBRef(
                ImageDocument.meta['collection'],
                ObjectId(image_id)
            ),
            'uploader': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'upload_time': now
        }
        yield NodeAvatarDocument.insert(document)

        self.finish()


class NodeDescriptionEditTemplateHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = NodeDescriptionEditTemplateForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        node_id = form.node_id.data

        node = yield NodeDocument.find_one({'_id': ObjectId(node_id)})
        if not node:
            raise HTTPError(404)

        self.render(
            'community/template/node-description-edit-template.html',
            node=node
        )


class NodeDescriptionEditHandler(CommunityBaseHandler):
    '''修改节点描述'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = NodeDescriptionEditForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        node_id = form.node_id.data
        description = form.description.data

        node = yield NodeDocument.find_one({'_id': ObjectId(node_id)})
        if not node:
            raise HTTPError(404)

        yield NodeDocument.update(
            {'_id': ObjectId(node_id)},
            {'$set': {
                'description': description,
                'last_modified_by': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'last_modified_time': datetime.now()
            }}
        )

        node = yield NodeDocument.get_node(node_id)
        html = self.render_string(
            'community/template/node-description.html',
            current_node=node
        )

        self.write_json({'html': html})


class TopicDeleteHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, topic_id):
        yield TopicDocument.delete_one(topic_id)

        self.redirect('/community')


class TopicCommentDeleteHandler(CommunityBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, comment_id):
        yield TopicCommentDocument.delete_one(comment_id)
        self.redirect('/community')
