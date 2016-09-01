# -*- coding: utf-8 -*-

from app.setting.handler import (
    SettingHandler, AvatarSetHandler, PasswordSetHandler, ProfileCoverSetHander,
    ProfileCoverCustomHandler, ProfileSetHandler, NotificationSetHandler,
    ThemeSetHandler, PrivateSetHandler
)

urlpattern = (
    (r'/setting/(profile|avatar|profile/cover|password|course|private|notification|theme)/?', SettingHandler),
    (r'/setting/avatar/set/?', AvatarSetHandler),
    (r'/setting/password/set/?', PasswordSetHandler),
    (r'/setting/profile/cover/set/?', ProfileCoverSetHander),
    (r'/setting/profile/cover/custom/?', ProfileCoverCustomHandler),
    (r'/setting/profile/set/?', ProfileSetHandler),
    (r'/setting/private/set/?', PrivateSetHandler),
    (r'/setting/notification/set/?', NotificationSetHandler),
    (r'/setting/theme/set/?', ThemeSetHandler),
)
