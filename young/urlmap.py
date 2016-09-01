# -*- coding: utf-8 -*-

import app.base.urlmap
import app.chat.urlmap
import app.community.urlmap
import app.home.urlmap
import app.message.urlmap
import app.profile.urlmap
import app.search.urlmap
import app.setting.urlmap
import app.share.urlmap
import app.user.urlmap

from young.handler import BaseHandler

urlpattern = ()

urlpattern += app.base.urlmap.urlpattern
urlpattern += app.chat.urlmap.urlpattern
urlpattern += app.community.urlmap.urlpattern
urlpattern += app.home.urlmap.urlpattern
urlpattern += app.message.urlmap.urlpattern
urlpattern += app.profile.urlmap.urlpattern
urlpattern += app.search.urlmap.urlpattern
urlpattern += app.setting.urlmap.urlpattern
urlpattern += app.share.urlmap.urlpattern
urlpattern += app.user.urlmap.urlpattern

urlpattern += (
    (r'.*', BaseHandler),
)
