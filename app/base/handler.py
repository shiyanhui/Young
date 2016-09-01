# -*- coding: utf-8 -*-

from datetime import datetime

import simplejson
from bson.dbref import DBRef
from bson.objectid import ObjectId
from tornado import gen
from tornado.web import authenticated, HTTPError

from young.handler import BaseHandler
from app.user.document import UserDocument
from app.base.document import ImageDocument

__all__ = ['ImageUploadHandler', 'ImageStaticFileHandler']


class ImageUploadHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        if 'files[]' not in self.request.files:
            raise HTTPError(404)

        uploaded_file = self.request.files['files[]'][0]
        uploader = DBRef(
            UserDocument.meta['collection'], ObjectId(self.current_user['_id'])
        )
        upload_time = datetime.now()

        image_id = yield ImageDocument.insert_one(
            uploaded_file, uploader=uploader, upload_time=upload_time
        )

        response_data = {
            'files': [{
                'name': "",
                'size': 10,
                'url': '/image/%s' % image_id,
                'thumbnail_url': '/image/%s' % image_id,
                'delete_url': '/image/%s' % image_id,
                'delete_type': 'POST'
            }]
        }
        response_data = simplejson.dumps(response_data)
        self.finish(response_data)


class ImageStaticFileHandler(BaseHandler):
    @gen.coroutine
    def get(self, image_id, thumbnail=None):
        image = yield ImageDocument.find_one({'_id': ObjectId(image_id)})
        self.set_header(
            'Content-Type', ('image/%s' % image['content_type']).lower())

        content = image['body']
        if thumbnail and 'thumbnail' in image:
            content = image['thumbnail']

        self.finish(str(content))
