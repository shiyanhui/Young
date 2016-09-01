# -*- coding: utf-8 -*-

import os
import sys
from StringIO import StringIO

import Image
from monguo import Connection
from tornado import gen
from tornado.ioloop import IOLoop
from bson.binary import Binary
from bson.dbref import DBRef
from bson.objectid import ObjectId

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT_PATH)

from app.community.document import NodeDocument
from app.base.document import ImageDocument
from app.user.document import OfficialProfileCoverDocument


@gen.coroutine
def init_community_nodes():
    node_list = [
        u'问与答', u'分享', u'技术', u'小道消息', u'酷工作', u'求职',
        u'面经', u'交易', u'活动', u'考研', u'出国', u'原创小说', u'设计']

    for i, node in enumerate(node_list):
        document = {
            'name': node,
            'sort': i,
            'category': NodeDocument.BUILTIN
        }

        existed = yield NodeDocument.find_one({"name": node})
        if not existed:
            yield NodeDocument.insert(document)

    raise gen.Return()


@gen.coroutine
def add_share_category():
    collection = Connection.get_database(pymongo=True).share_category

    category_list = [
        u'音乐', u'视频', u'图片', u'小说', u'论文', u'文档', u'软件', u'其他']

    for i, category in enumerate(category_list):
        document = {
            'name': category,
            'sort': i
        }

        existed = collection.find_one({"name": category})
        if not existed:
            collection.insert(document)

    raise gen.Return()


@gen.coroutine
def add_one_profile_cover(img_path, name):
    '''事先填充个人封面图片数据库'''

    document = {}
    document['name'] = name
    document['content_type'] = 'JPEG'

    existed = yield ImageDocument.find_one(document)
    if existed:
        return

    path = os.path.join(img_path, name)
    image = Image.open(path)

    scale = image.size[0] * 1.0 / 960
    width = int(image.size[0])
    height = int(300 * scale)
    box = (0, 0, width, height)

    image = image.crop(box)
    image = image.resize((969, 300), Image.ANTIALIAS)

    output = StringIO()
    image.save(output, document['content_type'], quality=100)
    document['body'] = Binary(output.getvalue())
    output.close()

    image = Image.open(path)
    image = image.resize((260, 160), Image.ANTIALIAS)

    output = StringIO()
    image.save(output, document['content_type'], quality=100)
    document['thumbnail'] = Binary(output.getvalue())
    output.close()

    image_id = yield ImageDocument.insert(document)
    document = {
        'image': DBRef(ImageDocument.meta['collection'], ObjectId(image_id))
    }

    yield OfficialProfileCoverDocument.insert(document)

    raise gen.Return()


@gen.coroutine
def add_profile_covers():
    '''往数据库中添加个人封面'''

    img_path = os.path.join(ROOT_PATH, 'static/img/profile-cover')

    for i in xrange(1, 25):
        yield add_one_profile_cover(img_path, "%s.jpg" % i)

    raise gen.Return()


if __name__ == '__main__':
    Connection.connect('Young')

    IOLoop.instance().run_sync(init_community_nodes)
    IOLoop.instance().run_sync(add_share_category)
    IOLoop.instance().run_sync(add_profile_covers)
