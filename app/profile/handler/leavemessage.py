# -*- coding: utf-8 -*-

from tornado import gen
from tornado.web import authenticated
from bson.objectid import ObjectId

from app.profile.handler.profile import ProfileBaseHandler
from app.profile.setting import PROFILE_SETTINGS
from app.profile.document import LeaveMessageDocument
from app.message.document import MessageDocument, MessageTopic

__all__ = ['LeaveMessageHandler']


class LeaveMessageHandler(ProfileBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, user_id=None):
        user_id = user_id or self.current_user["_id"]

        kwargs = yield self.get_header_arguments(user_id)
        if not kwargs['can_seen']:
            self.render('profile/template/profile-visitor.html', **kwargs)
        else:
            messages_func = LeaveMessageDocument.get_leave_message_list
            leave_message_list = yield messages_func(
                user_id, self.current_user['_id'],
                limit=PROFILE_SETTINGS['leave_message_number_per_page']
            )

            kwargs.update({
                'leave_message_list': leave_message_list
            })

            if ObjectId(user_id) == ObjectId(self.current_user['_id']):
                yield MessageDocument.set_read(
                    user_id, MessageTopic.LEAVE_MESSAGE_NEW
                )

            self.render(
                'profile/template/leavemessage/leavemessage.html',
                **kwargs
            )
