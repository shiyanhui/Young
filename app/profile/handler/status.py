# -*- coding: utf-8 -*-

import simplejson as json
from bson.objectid import ObjectId
from tornado import gen
from tornado.web import authenticated, HTTPError

from app.home.document import StatusDocument
from app.user.document import UserDocument, LeagueMemberDocument
from app.profile.setting import PROFILE_SETTINGS
from app.profile.handler.profile import ProfileBaseHandler
from app.profile.form import StatusMoreForm, LeagueBulletinSaveForm

__all__ = ['StatusHandler', 'StatusMoreHandler', 'FriendRecommendHandler',
           'LeagueBulletinSaveHandler']


class StatusHandler(ProfileBaseHandler):
    '''个人主页'''

    @authenticated
    @gen.coroutine
    def get(self, user_id=None):
        if user_id is None:
            user_id = self.current_user['_id']

        kwargs = yield self.get_header_arguments(user_id)
        if not kwargs['can_seen']:
            self.render('profile/template/profile-visitor.html', **kwargs)
        else:
            status_list = yield StatusDocument.get_status_list(
                user_id,
                self.current_user['_id'],
                limit=PROFILE_SETTINGS['status_number_per_page']
            )

            recommend_friend_list = yield UserDocument.get_random_user_list(
                self.current_user['_id']
            )

            if kwargs['user']['user_type'] == 'league':
                member_list = yield LeagueMemberDocument.get_member(user_id)
                kwargs.update({'member_list': member_list})

            kwargs.update({
                'status_list': status_list,
                'recommend_friend_list': recommend_friend_list,
                'PROFILE_SETTINGS': PROFILE_SETTINGS
            })

            self.render('profile/template/status/status.html', **kwargs)


class StatusMoreHandler(ProfileBaseHandler):
    '''加载更多状态'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = StatusMoreForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        page = form.page.data

        skip = PROFILE_SETTINGS['status_number_per_page'] * page
        limit = PROFILE_SETTINGS['status_number_per_page']
        status_list = yield StatusDocument.get_status_list(
            self.current_user['_id'],
            self.current_user['_id'],
            skip=skip, limit=limit
        )

        html = ''.join(
            self.render_string(
                'profile/template/status/status-list-item.html',
                status=status
            ) for status in status_list
        )

        self.finish(json.dumps({'html': html, 'page': page + 1}))


class FriendRecommendHandler(ProfileBaseHandler):
    '''换一批推荐'''

    @authenticated
    @gen.coroutine
    def post(self):
        recommend_friend_list = yield UserDocument.get_random_user_list(
            self.current_user['_id']
        )

        html = self.render_string(
            'profile/template/status/friend-recommend.html',
            recommend_friend_list=recommend_friend_list
        )
        self.finish(json.dumps({'html': html}))


class LeagueBulletinSaveHandler(ProfileBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = LeagueBulletinSaveForm(self.request.arguments)
        if not form.validate() or self.current_user['user_type'] != 'league':
            raise HTTPError(404)

        league_bulletin = form.league_bulletin.data

        yield UserDocument.update(
            {'_id': ObjectId(self.current_user['_id'])},
            {'$set': {'league_bulletin': league_bulletin}}
        )

        self.finish()
