# -*- coding: utf-8 -*-

from datetime import datetime

import simplejson as json
from bson.dbref import DBRef
from bson.objectid import ObjectId
from tornado import gen
from tornado.web import authenticated, HTTPError

from lib.message import WriterManager
from young.handler import BaseHandler
from app.home.document import StatusDocument
from app.user.document import (
    UserDocument, FriendDocument, UserSettingDocument
)
from app.message.document import MessageDocument, MessageTopic
from app.community.document import TopicDocument
from app.profile.setting import PROFILE_SETTINGS
from app.profile.document import LeaveMessageDocument
from app.profile.form import (
    LeaveMessageNewForm, LeaveMessageMoreForm, FriendRequestForm
)

__all__ = ['LeaveMessageNewHandler', 'LeaveMessageMoreHandler',
           'FriendRequestNewHandler', 'FriendRequestAgreeHandler',
           'FriendRequestRefuseHandler']


class ProfileBaseHandler(BaseHandler):
    @gen.coroutine
    def get_header_arguments(self, user_id=None):
        user_id = user_id or self.current_user["_id"]

        user = yield UserDocument.find_one({
            '_id': ObjectId(user_id)
        })
        if not user:
            raise HTTPError(404)

        status_number = yield StatusDocument.get_status_number(user_id)
        topic_number = yield TopicDocument.get_topic_number_by_someone(
            user_id, visitor_id=self.current_user['_id']
        )

        user = yield UserDocument.translate_dbref_in_document(user)

        can_seen = yield UserDocument.can_seen(
            user_id, self.current_user['_id']
        )
        is_friend = yield FriendDocument.is_friend(
            user_id, self.current_user['_id']
        )
        user_setting = yield UserSettingDocument.get_user_setting(
            user_id
        )
        profile_cover = yield UserSettingDocument.get_profile_cover(
            user_id
        )

        kwargs = {
            'user': user,
            'can_seen': can_seen,
            'is_friend': is_friend,
            'user_setting': user_setting,
            'status_number': status_number,
            'topic_number': topic_number,
            'profile_cover': profile_cover,
            'PROFILE_SETTINGS': PROFILE_SETTINGS
        }

        if not can_seen:
            messages_func = LeaveMessageDocument.get_leave_message_list
            leave_message_list = yield messages_func(
                user_id, self.current_user['_id'],
                limit=PROFILE_SETTINGS['leave_message_number_per_page']
            )

            kwargs.update({
                'leave_message_list': leave_message_list
            })

        raise gen.Return(kwargs)


class LeaveMessageNewHandler(ProfileBaseHandler):
    '''在visitor界面添加新留言'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = LeaveMessageNewForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        user_id = form.user_id.data
        private = form.private.data
        content = form.content.data
        replyeder_id = form.replyeder_id.data

        user_setting = yield UserSettingDocument.get_user_setting(user_id)
        if not user_setting['enable_leaving_message']:
            raise HTTPError(404)

        replyeder = None
        if replyeder_id:
            replyeder = yield UserDocument.find_one({
                '_id': ObjectId(replyeder_id)
            })
            if (not replyeder or
                    ObjectId(user_id) != ObjectId(self.current_user['_id'])):
                raise HTTPError(404)

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise HTTPError(404)

        now = datetime.now()
        document = {
            'user': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            'author': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'private': private,
            'content': content,
            'leave_time': now
        }

        if replyeder:
            document.update({
                'replyeder': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(replyeder_id)
                )
            })

        leave_message_id = yield LeaveMessageDocument.insert(document)

        if replyeder:
            recipient_id = replyeder_id
            message_type = 'reply:leavemessage'
            message_topic = MessageTopic.REPLY
        else:
            recipient_id = user_id
            message_type = MessageTopic.LEAVE_MESSAGE_NEW
            message_topic = MessageTopic.LEAVE_MESSAGE_NEW

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
                'data': DBRef(
                    LeaveMessageDocument.meta['collection'],
                    ObjectId(leave_message_id)
                )
            }
            message_id = yield MessageDocument.insert(message)
            WriterManager.pub(message_topic, message_id)

        number_func = LeaveMessageDocument.get_leave_message_number
        leave_message_number = yield number_func(
            user_id, self.current_user['_id']
        )

        document.update({
            '_id': ObjectId(leave_message_id),
            'floor': leave_message_number
        })

        if replyeder:
            document.update({
                'replyeder': replyeder
            })

        leave_message = yield LeaveMessageDocument.translate_dbref_in_document(
            document
        )

        html = self.render_string(
            'profile/template/leavemessage/leavemessage-list-item.html',
            leave_message=leave_message,
            user=user
        )

        self.finish(json.dumps({'html': html}))


class LeaveMessageMoreHandler(ProfileBaseHandler):
    '''陌生人访问界面加载更多留言'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = LeaveMessageMoreForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        page = form.page.data
        user_id = form.user_id.data

        skip = PROFILE_SETTINGS['leave_message_number_per_page'] * page
        limit = PROFILE_SETTINGS['leave_message_number_per_page']

        leave_message_list = yield LeaveMessageDocument.get_leave_message_list(
            user_id, self.current_user['_id'], skip=skip, limit=limit
        )

        html = ''.join(
            self.render_string(
                'profile/template/leavemessage/leavemessage-list-item.html',
                leave_message=leave_message
            )
            for leave_message in leave_message_list
        )

        self.finish(json.dumps({'html': html, 'page': page + 1}))


class FriendRequestNewHandler(ProfileBaseHandler):
    '''请求添加新朋友'''

    @authenticated
    @gen.coroutine
    def post(self):
        response_data = {}
        form = FriendRequestForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        user_id = form.user_id.data

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user or user['_id'] == self.current_user['_id']:
            raise HTTPError(404)

        is_friend = yield FriendDocument.is_friend(
            user_id, self.current_user['_id']
        )
        if is_friend:
            raise HTTPError(404)

        document = {
            'sender': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'recipient': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            'message_type': MessageTopic.FRIEND_REQUEST_NEW,
        }

        message = yield MessageDocument.find_one(document)
        if message:
            response_data = {'error': '你已经发送了好友请求!'}
        else:
            user_setting = yield UserSettingDocument.get_user_setting(user_id)
            if not user_setting['require_verify_when_add_friend']:
                yield FriendDocument.add_friend(
                    user_id,
                    self.current_user['_id']
                )
                response_data.update({'ok': 1})

            document.update({'time': datetime.now()})
            message_id = yield MessageDocument.insert(document)

            WriterManager.pub(MessageTopic.FRIEND_REQUEST_NEW, message_id)

        self.finish(json.dumps(response_data))


class FriendRequestAgreeHandler(ProfileBaseHandler):
    '''同意添加其为好友'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = FriendRequestForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        user_id = form.user_id.data

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user or user['_id'] == self.current_user['_id']:
            raise HTTPError(404)

        is_friend = yield FriendDocument.is_friend(
            user_id, self.current_user['_id']
        )
        if not is_friend:
            yield FriendDocument.add_friend(
                user_id, self.current_user['_id']
            )

        yield MessageDocument.remove({
            'sender': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            'recipient': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'message_type': MessageTopic.FRIEND_REQUEST_NEW
        })

        self.finish()


class FriendRequestRefuseHandler(ProfileBaseHandler):
    '''拒绝添加其为好友'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = FriendRequestForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        user_id = form.user_id.data

        yield MessageDocument.remove({
            'sender': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            'recipient': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'message_type': MessageTopic.FRIEND_REQUEST_NEW})

        self.finish()
