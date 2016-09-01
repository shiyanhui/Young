# -*- coding: utf-8 -*-

from app.profile.handler import (
    StatusHandler, StatusMoreHandler, FriendRecommendHandler,
    FriendRequestNewHandler, FriendRequestAgreeHandler,
    FriendRequestRefuseHandler, TopicHandler, LeaveMessageHandler,
    LeaveMessageNewHandler, LeaveMessageMoreHandler,
    LeagueBulletinSaveHandler
)

urlpattern = (
    (r'/profile/?([a-f0-9]{24})?', StatusHandler),
    (r'/profile/status/?([a-f0-9]{24})?/?', StatusHandler),
    (r'/profile/status/more/?', StatusMoreHandler),
    (r'/profile/friend/recommend/?', FriendRecommendHandler),
    (r'/profile/friend/request/new?', FriendRequestNewHandler),
    (r'/profile/friend/request/agree/?', FriendRequestAgreeHandler),
    (r'/profile/friend/request/refuse/?', FriendRequestRefuseHandler),
    (r'/profile/topic/?([a-f0-9]{24})?/?', TopicHandler),
    (r'/profile/leavemessage/?([a-f0-9]{24})?/?', LeaveMessageHandler),
    (r'/profile/leavemessage/new/?', LeaveMessageNewHandler),
    (r'/profile/leavemessage/more/?', LeaveMessageMoreHandler),
    (r'/profile/league/bulletin/save/?', LeagueBulletinSaveHandler)
)
