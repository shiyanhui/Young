# -*- coding: utf-8 -*-

import random

from tornado import gen
from tornado.web import authenticated
from app.community.document import TopicDocument
from app.profile.handler.profile import ProfileBaseHandler

__all__ = ['TopicHandler']


class TopicHandler(ProfileBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, user_id=None):
        if user_id is None:
            user_id = self.current_user['_id']

        kwargs = yield self.get_header_arguments(user_id)
        if not kwargs['can_seen']:
            self.render('profile/template/profile-visitor.html', **kwargs)
        else:
            recommend_topic_list = []

            topic_list = yield TopicDocument.get_topic_list_by_someone(user_id)
            if topic_list:
                index = random.randint(0, len(topic_list) - 1)

                topic_list_func = TopicDocument.get_recommend_topic_list
                recommend_topic_list = yield topic_list_func(
                    topic_list[index]['_id']
                )

            kwargs.update({
                'topic_list': topic_list,
                'recommend_topic_list': recommend_topic_list
            })
            self.render('profile/template/topic/topic.html', **kwargs)
