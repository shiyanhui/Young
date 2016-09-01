# -*- coding: utf-8 -*-

from app.chat.handler import (
    ChatWithHandler, MessageNewHandler, MessageUpdateHandler,
    MessageHistoryHandler
)

urlpattern = (
    (r'/chat/with/?', ChatWithHandler),
    (r'/chat/message/new/?', MessageNewHandler),
    (r'/chat/message/update/?', MessageUpdateHandler),
    (r'/chat/message/history/?', MessageHistoryHandler),
)
