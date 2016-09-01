# -*- coding: utf-8 -*-

from StringIO import StringIO

import Image
from bson.binary import Binary
from bson.dbref import DBRef
from tornado import gen
from tornado.web import HTTPError
from monguo import (
    Document, StringField, BinaryField, ReferenceField,
    DateTimeField, ListField, IntegerField
)

from app.user.document import UserDocument

__all__ = ['ImageDocument', 'TemporaryFileDocument']


class ImageDocument(Document):
    '''图片

    :Variables:
      - `name`: 图片名称
      - `body`: 图片内容
      - `content_type`: 图片类型, 存储的内容是PNG, JPEG等
      - `thumbnail`: 略缩图
      - `uploader`: 上传者, 有可能是抓取的图片, 所以上传者不一定存在.
      - `upload_time`: 上传时间
      - `description`: 图片描述
      - `tag`: 标签
    '''

    name = StringField(required=True, max_length=200)
    body = BinaryField(required=True)
    content_type = StringField(required=True)
    thumbnail = BinaryField(required=True)
    uploader = ReferenceField(UserDocument)
    upload_time = DateTimeField()
    description = StringField(max_length=500)
    tags = ListField(StringField(max_length=50))

    meta = {
        'collection': 'image'
    }

    @gen.coroutine
    def generate_image_url(image_id, thumbnail=False):
        url = '/image/%s' % image_id
        if thumbnail:
            url += '/thumbnail'

        raise gen.Return(url)

    @gen.coroutine
    def insert_one(uploaded_file, thumbnail_width=200, target_width=None,
                   crop_area=None, uploader=None, upload_time=None,
                   description=None, tags=None):
        '''
        插入一个图片

        :Parameters:
          - `uploaded_file`: 上传的文件
          - `thumbnail_width`: 略缩图宽度, 默认200px
          - `target_width`: Jcrop插件剪裁时, 图像所具有的宽度
          - `crop_area`: 要剪裁的区域, 其格式为(x, y, w, h), x/y/w/h是Jcrop插件传过来的数据,
                         x代表左上角x坐标, y代表左上角y坐标, w代表宽度, h代表高度
          - `uploader`: 上传者, 不是ObjectId, 是DBRef
          - `upload_time`: 上传时间
          - `description`: 描述
          - `tags`: 标签, 列表类型
        '''

        try:
            image = Image.open(StringIO(uploaded_file['body']))
        except:
            raise HTTPError(404)

        content_type = uploaded_file['content_type'].split('/')[1].upper()

        document = {
            'name': uploaded_file['filename'],
            'content_type': content_type,
        }
        if uploader:
            assert isinstance(uploader, DBRef)
            document["uploader"] = uploader

        if upload_time:
            document["upload_time"] = upload_time

        if description:
            document["description"] = description

        if tags:
            document["tags"] = tags

        if target_width is not None and crop_area is not None:
            scale = image.size[0] * 1.0 / target_width
            x, y, w, h = map(lambda x: int(x * scale), crop_area)

            box = (x, y, x + w, y + h)
            image = image.crop(box)

        _width = 1024
        if image.size[0] > _width:
            height = _width * 1.0 * image.size[1] / image.size[0]
            image = image.resize(map(int, (_width, height)), Image.ANTIALIAS)

        output = StringIO()
        image.save(output, content_type, quality=100)
        document["body"] = Binary(output.getvalue())
        output.close()

        thumbnail_height = thumbnail_width * 1.0 * image.size[1] / image.size[0]

        output = StringIO()
        image.resize(
            map(int, (thumbnail_width, thumbnail_height)), Image.ANTIALIAS
        ).save(output, content_type, quality=100)
        document["thumbnail"] = Binary(output.getvalue())
        output.close()

        image_id = yield ImageDocument.insert(document)

        raise gen.Return(image_id)


class TemporaryFileDocument(Document):
    '''临时文件

    :Variables:
      - `body`: 文件内容，不超过16M
      - `chunk_index`: 片索引
      - `filename`: 文件名称
      - `uploader`: 上传者
      - `upload_time`: 上传时间
      - `upload_token`: 上传id
    '''

    body = BinaryField(required=True)
    chunk_index = IntegerField(required=True)
    filename = StringField(required=True, max_length=500)
    uploader = ReferenceField(UserDocument, required=True)
    upload_time = DateTimeField(required=True)
    upload_token = StringField(required=True, max_length=100)

    meta = {
        'collection': 'tmporary_file'
    }
