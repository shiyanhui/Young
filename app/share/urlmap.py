# -*- coding: utf-8 -*-

from app.share.handler import (
    ShareHandler, ShareNewTemplateHandler, ShareNewHandler,
    ShareNewCancelHandler, ShareCategoryHandler, ShareOneHandler,
    ShareDownloadHandler, ShareCommentNewHandler, ShareLikeHandler
)

urlpattern = (
    (r'/share/?', ShareHandler),
    (r'/share/new/template/?', ShareNewTemplateHandler),
    (r'/share/new/?', ShareNewHandler),
    (r'/share/new/cancel/?', ShareNewCancelHandler),
    (r'/share/category/?', ShareCategoryHandler),
    (r'/share/([a-f0-9]{24})/?', ShareOneHandler),
    (r'/share/download/([a-f0-9]{24})/?', ShareDownloadHandler),
    (r'/share/comment/new/?', ShareCommentNewHandler),
    (r'/share/like/?', ShareLikeHandler),
)
