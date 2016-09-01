# -*- coding: utf-8 -*-

from app.base.handler import ImageUploadHandler, ImageStaticFileHandler

urlpattern = (
    (r'/image/upload/?', ImageUploadHandler),
    (r'/image/([a-f0-9]{24})/?(thumbnail)?/?', ImageStaticFileHandler)
)
