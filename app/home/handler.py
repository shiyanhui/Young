# -*- coding: utf-8 -*-

import re
import os
from datetime import datetime
from StringIO import StringIO

import Image
import simplejson as json
from tornado.web import authenticated, HTTPError
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from bson.binary import Binary

from lib.message import WriterManager
from setting import HOME_SETTINGS
from young.handler import BaseHandler
from app.user.document import (
    UserDocument, UserSettingDocument, FriendDocument)
from app.chat.document import ChatMessageDocument
from app.message.document import MessageDocument, MessageTopic
from app.community.document import TopicDocument
from app.home.form import (
    StatusMoreForm, StatusNewForm, StatusCommentsForm,
    StatusCommentNewForm, FriendActionForm,
    StatusLikeForm, MessageForm, MessageMoreForm)
from app.home.document import (
    StatusDocument, StatusLikeDocument, StatusCommentDocument,
    StatusPhotoDocument)

__all__ = ['HomeHandler', 'FriendRecommendHandler', 'StatusNewHandler',
           'StatusMoreHandler', 'StatusCommentsHandler',
           'StatusCommentNewHandler', 'FriendsHandler', 'FriendActionHandler',
           'StatusLikeHandler', 'MessageHandler', 'MessageMoreHandler',
           'StatusPhotoStaticFileHandler']


class HomeBaseHandler(BaseHandler):
    @gen.coroutine
    def get_sidebar_arguments(self):
        '''得到两侧栏的render变量'''

        user_id = self.current_user['_id']
        status_number = yield StatusDocument.get_status_number(user_id)
        topic_number = yield TopicDocument.get_topic_number_by_someone(user_id)

        user_setting = yield UserSettingDocument.find_one({
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })

        random_user_list = yield UserDocument.get_random_user_list(
            self.current_user['_id']
        )

        kwargs = {
            'status_number': status_number,
            'topic_number': topic_number,
            'MessageTopic': MessageTopic,
            'user_setting': user_setting,
            'random_user_list': random_user_list,
            'HOME_SETTINGS': HOME_SETTINGS
        }

        raise gen.Return(kwargs)


class HomeHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        kwargs = yield self.get_sidebar_arguments()

        user_id = self.current_user['_id']
        status_list = yield StatusDocument.get_friends_status_list(
            user_id, limit=HOME_SETTINGS['status_number_per_page']
        )

        kwargs.update({
            'status_list': status_list,
            'HOME_SETTINGS': HOME_SETTINGS
        })

        self.render('home/template/status/status.html', **kwargs)


class FriendRecommendHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''换一批推荐'''

        random_user_list = yield UserDocument.get_random_user_list(
            self.current_user['_id']
        )
        html = self.render_string(
            'home/template/friend-recommend.html',
            random_user_list=random_user_list
        )

        self.finish(json.dumps({'html': html}))


class StatusNewHandler(HomeBaseHandler):
    '''发布新状态'''

    REGEX_AT = re.compile('@[^@\d\(\)]+\([0-9a-f]{24}\)')

    def number(self, content):
        '''状态字数'''

        result = len(content)

        search = self.REGEX_AT.findall(content)
        if search:
            result -= len(search) * 26

        return result

    @authenticated
    @gen.coroutine
    def post(self):
        response_data = {}

        form = StatusNewForm(self.request.arguments)
        if form.validate():
            content = form.content.data

            n = len(content)
            if n > HOME_SETTINGS['status_max_length']:
                response_data.update({
                    'error': (
                        '状态内容不能超过%s字' %
                        HOME_SETTINGS['status_max_length']
                    )
                })
            elif n <= 0 and not (
                    self.request.files and 'picture' in self.request.files):
                response_data.update({'error': '请输入文字内容或者照片'})
            else:
                picture = None
                if self.request.files and 'picture' in self.request.files:
                    picture = self.request.files['picture'][0]
                    image_types = [
                        'image/jpg', 'image/png', 'image/jpeg', 'image/gif'
                    ]
                    if picture['content_type'].lower() not in image_types:
                        response_data.update({
                            'error': '请上传jpg/png/gif格式的图片'
                        })

                if 'error' not in response_data:
                    now = datetime.now()

                    document = {
                        'author': DBRef(
                            UserDocument.meta['collection'],
                            self.current_user['_id']
                        ),
                        'publish_time': now,
                        'content': content
                    }
                    status_id = yield StatusDocument.insert(document)
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
                            'message_type': MessageTopic.STATUS_NEW,
                            'time': now,
                            'read': False,
                            'data': DBRef(
                                StatusDocument.meta['collection'],
                                ObjectId(status_id)
                            )
                        }
                        message_id = yield MessageDocument.insert(document)
                        message_list.append(str(message_id))

                    if message_list:
                        WriterManager.mpub(
                            MessageTopic.STATUS_NEW, message_list
                        )

                    if picture is not None:
                        try:
                            image = Image.open(StringIO(picture['body']))
                        except:
                            raise HTTPError(404)

                        try:
                            content_type = picture[
                                'content_type'
                            ].split('/')[-1].upper()
                        except:
                            content_type = 'JPEG'

                        document = {
                            'status': DBRef(
                                StatusDocument.meta['collection'],
                                ObjectId(status_id)
                            ),
                            'name': picture['filename'],
                            'content_type': content_type,
                            'upload_time': datetime.now()
                        }

                        width = 1024
                        if image.size[0] > width:
                            height = width * 1.0 * image.size[1] / image.size[0]
                            image = image.resize(
                                map(int, (width, height)), Image.ANTIALIAS
                            )

                        output = StringIO()
                        image.save(output, content_type, quality=100)
                        document.update({'body': Binary(output.getvalue())})
                        output.close()

                        thumbnail_width = 200
                        thumbnail_height = (
                            thumbnail_width * 1.0 * image.size[1] / image.size[0]
                        )

                        output = StringIO()
                        image = image.resize(
                            map(int, (thumbnail_width, thumbnail_height)),
                            Image.ANTIALIAS
                        )
                        image.save(output, content_type, quality=100)
                        document.update({
                            'thumbnail': Binary(output.getvalue())
                        })
                        output.close()

                        yield StatusPhotoDocument.insert(document)

                    status = yield StatusDocument.get_status(
                        status_id, self.current_user['_id']
                    )
                    html = self.render_string(
                        'home/template/status/status-list-item.html',
                        status=status
                    )
                    response_data.update({'html': html})
        else:
            for field in form.errors:
                response_data.update({'error': form.errors[field][0]})
                break

        self.finish(json.dumps(response_data))


class StatusMoreHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''加载更多状态'''

        form = StatusMoreForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        page = form.page.data

        skip = HOME_SETTINGS['status_number_per_page'] * page
        limit = HOME_SETTINGS['status_number_per_page']

        status_list = yield StatusDocument.get_friends_status_list(
            self.current_user['_id'], skip=skip, limit=limit
        )

        html = ''.join(
            self.render_string(
                'home/template/status/status-list-item.html',
                status=status
            ) for status in status_list
        )
        response_data = json.dumps({'html': html, 'page': page + 1})

        self.finish(response_data)


class StatusCommentsHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = StatusCommentsForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        status_id = form.status_id.data

        status = yield StatusDocument.find_one({
            '_id': ObjectId(status_id)
        })
        if not status:
            raise HTTPError(404)

        status_comment_list = yield StatusCommentDocument.get_comment_list(
            status_id, self.current_user['_id']
        )

        html = self.render_string(
            'home/template/status/status-comment-list.html',
            status=status,
            status_comment_list=status_comment_list
        )

        self.finish(json.dumps({'html': html}))


class StatusCommentNewHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''评论状态'''

        response_data ={}

        form = StatusCommentNewForm(self.request.arguments)
        if form.validate():
            status_id = form.status_id.data
            content = form.content.data
            replyeder_id = form.replyeder_id.data

            status = yield StatusDocument.find_one({
                '_id': ObjectId(status_id)
            })
            if not status:
                raise HTTPError(404)

            can_see = yield StatusDocument.can_see(
                status, self.current_user['_id']
            )
            if not can_see:
                raise HTTPError(404)

            replyeder = None
            if replyeder_id:
                replyeder = yield UserDocument.find_one({
                    '_id': ObjectId(replyeder_id)
                })
                if not replyeder:
                    raise HTTPError(404)

                is_friend = yield FriendDocument.is_friend(
                    self.current_user['_id'], replyeder_id
                )
                if not is_friend:
                    raise HTTPError(404)

            now = datetime.now()
            document = {
                'status': DBRef(
                    StatusDocument.meta['collection'],
                    ObjectId(status['_id'])
                ),
                'author': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'comment_time': now,
                'content': content
            }

            if replyeder:
                document.update({
                    'replyeder': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(replyeder_id)
                    )
                })

            comment_id = yield StatusCommentDocument.insert_one(document)

            if replyeder:
                recipient_id = replyeder_id
                message_type = 'reply:status'
                message_topic = MessageTopic.REPLY
            else:
                recipient_id = status['author'].id
                message_type = 'comment:status'
                message_topic = MessageTopic.COMMENT

            if ObjectId(self.current_user['_id']) != ObjectId(recipient_id):
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
                        StatusCommentDocument.meta['collection'],
                        ObjectId(comment_id)
                    )
                }
                message_id = yield MessageDocument.insert(message)
                WriterManager.pub(message_topic, message_id)

            comment = yield StatusCommentDocument.get_comment(comment_id)
            html = self.render_string(
                'home/template/status/status-comment-list-item.html',
                status=status,
                status_comment=comment
            )
            response_data.update({'html': html})
        else:
            for field in form.errors:
                response_data.update({'error': form.errors[field][0]})
                break

        self.finish(json.dumps(response_data))


class StatusLikeHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''点赞'''

        form = StatusLikeForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        status_id = form.status_id.data

        status = yield StatusDocument.find_one({'_id': ObjectId(status_id)})
        if not status:
            raise HTTPError(404)

        status_dbref = DBRef(
            StatusDocument.meta['collection'],
            ObjectId(status_id)
        )
        liker_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(self.current_user['_id'])
        )

        document = {
            'status': status_dbref,
            'liker': liker_dbref
        }

        liked = yield StatusLikeDocument.is_liked(
            status_id, self.current_user['_id']
        )
        if not liked:
            now = datetime.now()
            document.update({'like_time': now})
            like_id = yield StatusLikeDocument.insert_one(document)

            if str(self.current_user['_id']) != str(status['author'].id):
                document = {
                    'sender': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'recipient': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(status['author'].id)
                    ),
                    'message_type': 'like:status',
                    'time': now,
                    'read': False,
                    'data': DBRef(
                        StatusLikeDocument.meta['collection'],
                        ObjectId(like_id)
                    )
                }
                message_id = yield MessageDocument.insert(document)
                WriterManager.pub(MessageTopic.LIKE, message_id)

        like_times = yield StatusLikeDocument.get_like_times(status_id)
        like_list = yield StatusLikeDocument.get_like_list(
            status['_id'], self.current_user['_id']
        )

        likers = '、'.join([like['liker']['name'] for like in like_list])
        response_data = json.dumps({
            'like_times': like_times,
            'likers': likers
        })

        self.finish(response_data)


class FriendsHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        '''朋友首页'''

        kwargs = yield self.get_sidebar_arguments()

        friend_list = yield FriendDocument.get_friend_list(
            self.current_user['_id']
        )
        kwargs.update({
            'friend_list': friend_list
        })
        self.render('home/template/friend/friend.html', **kwargs)


class FriendActionHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self, action):
        '''屏蔽/拉黑/删除某一个朋友'''

        form = FriendActionForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        friend_id = form.friend_id.data

        is_friend = yield FriendDocument.is_friend(
            self.current_user['_id'], friend_id
        )

        if not is_friend:
            response_data.update({'error': '你们不是朋友'})
        else:
            owner = DBRef(
                UserDocument.meta['collection'],
                self.current_user['_id']
            )
            friend = DBRef(
                UserDocument.meta['collection'],
                ObjectId(friend_id)
            )

            friend_document = yield FriendDocument.find_one({
                'owner': owner, 'friend': friend
            })

            if action == 'shield':
                shielded = True
                if friend_document['shielded']:
                    shielded = False

                yield FriendDocument.update(
                    {'_id': friend_document['_id']},
                    {'$set': {'shielded': shielded}}
                )

                response_data.update({'shielded': shielded})

            elif action == 'block':
                blocked = True
                if friend_document['blocked']:
                    blocked = False

                yield FriendDocument.update(
                    {'_id': friend_document['_id']},
                    {'$set': {'blocked': blocked}}
                )

                response_data.update({'blocked': blocked})

            elif action == 'delete':
                yield FriendDocument.remove({
                    '$or': [
                        {'owner': owner, 'friend': friend},
                        {'owner': friend, 'friend': owner}
                    ]
                })
            else:
                raise HTTPError(404)

        self.finish(json.dumps(response_data))


class MessageHandler(HomeBaseHandler):
    '''首页历史消息'''

    @authenticated
    @gen.coroutine
    def get(self):
        form = MessageForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        category = form.category.data

        kwargs = yield self.get_sidebar_arguments()

        if category == MessageTopic.CHAT_MESSAGE_NEW:
            message_list = yield ChatMessageDocument.get_chat_message_list(
                self.current_user['_id'],
                limit=HOME_SETTINGS['message_number_per_page']
            )
        else:
            message_list = yield MessageDocument.get_message_list(
                self.current_user['_id'],
                message_topic=category,
                limit=HOME_SETTINGS['message_number_per_page']
            )

            yield MessageDocument.set_read(self.current_user['_id'], category)

        kwargs.update({
            'message_list': message_list,
            'category': category
        })

        self.render('home/template/message/message.html', **kwargs)


class MessageMoreHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''加载更多消息'''

        form = MessageMoreForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        page = form.page.data
        category = form.category.data

        skip = HOME_SETTINGS['message_number_per_page'] * page
        limit = HOME_SETTINGS['message_number_per_page']

        if category == MessageTopic.CHAT_MESSAGE_NEW:
            message_list = yield ChatMessageDocument.get_chat_message_list(
                self.current_user['_id'],
                skip=skip,
                limit=limit
            )
        else:
            message_list = yield MessageDocument.get_message_list(
                self.current_user['_id'],
                message_topic=category,
                skip=skip,
                limit=limit
            )

        if category == MessageTopic._FRIENDS_DYNAMIC:
            path = 'message-friends-dynamic-list-item.html'
        elif category == MessageTopic._COMMENT_AND_REPLY:
            path = 'message-comment-and-reply-list-item.html'
        elif category == MessageTopic.AT:
            path = 'message-at-list-item.html'
        elif category == MessageTopic.CHAT_MESSAGE_NEW:
            path = 'message-chat-message-list-item.html'
        elif category == MessageTopic.FRIEND_REQUEST_NEW:
            path = 'message-friend-request-list-item.html'
        elif category == MessageTopic.LIKE:
            path = 'message-like-list-item.html'

        path = os.path.join("home/template/message", path)

        html = ''.join(
            self.render_string(
                path, message=message, MessageTopic=MessageTopic
            ) for message in message_list
        )

        response_data = json.dumps({'html': html, 'page': page + 1})
        self.finish(response_data)


class StatusPhotoStaticFileHandler(HomeBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, photo_id, thumbnail=None):
        photo = yield StatusPhotoDocument.find_one({
            '_id': ObjectId(photo_id)
        })
        if not photo:
            self.finish()
        else:
            content = photo['thumbnail'] if thumbnail else photo['body']
            self.set_header(
                'Content-Type',
                ('image/%s' % photo['content_type']).lower()
            )
            self.finish(str(content))
