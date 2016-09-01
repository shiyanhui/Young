# -*- coding: utf-8 -*-

from app.home.handler import (
    HomeHandler, StatusMoreHandler, FriendRecommendHandler, StatusNewHandler,
    StatusCommentsHandler, StatusCommentNewHandler, StatusLikeHandler,
    FriendsHandler, MessageHandler, MessageMoreHandler, FriendActionHandler,
    StatusPhotoStaticFileHandler
)

urlpattern = (
    (r'/home/?', HomeHandler),
    (r'/home/status/more/?', StatusMoreHandler),
    (r'/home/friend/recommend/?', FriendRecommendHandler),
    (r'/home/status/new/?', StatusNewHandler),
    (r'/home/status/comments/?', StatusCommentsHandler),
    (r'/home/status/comment/new/?', StatusCommentNewHandler),
    (r'/home/status/like/?', StatusLikeHandler),
    (r'/home/friends/?', FriendsHandler),
    (r'/home/message/?', MessageHandler),
    (r'/home/message/more?', MessageMoreHandler),
    (r'/friend/(shield|block|delete)/?', FriendActionHandler),
    (r'/status/photo/([a-f0-9]{24})/?(thumbnail)?/?', StatusPhotoStaticFileHandler),
)
