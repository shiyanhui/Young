# -*- coding: utf-8 -*-

from app.message.handler import MessageUpdaterHandler

urlpattern = (
    (r'/message/update/?', MessageUpdaterHandler),
)
