# -*- coding: utf-8 -*-

import re
from datetime import datetime

import motor
import gridfs
import simplejson as json
from bson.objectid import ObjectId
from bson.dbref import DBRef
from bs4 import BeautifulSoup
from monguo import Connection, Document
from tornado import gen
from tornado.web import RequestHandler

import app.user.document


class UtilMixin(object):
    @classmethod
    def translate_time(cls, time):
        """把时间换成易读的格式"""

        SECOND = 1
        MINUTE = SECOND * 60
        HOUR = MINUTE * 60
        DAY = HOUR * 24

        total_seconds = int((datetime.now() - time).total_seconds())

        if total_seconds < MINUTE:
            result = '%d 秒前' % max(total_seconds, 1)
        elif total_seconds < HOUR:
            result = '%d 分钟前' % (total_seconds / MINUTE)
        elif total_seconds < DAY:
            hour = total_seconds / HOUR
            minute = (total_seconds - hour * HOUR) / MINUTE
            result = '%d 小时 %d 分钟前' % (hour, minute)
        else:
            result = '%d 天前' % (total_seconds / DAY)
        return result

    @classmethod
    def get_avatar(cls, user_id, thumbnail=None):
        '''得到头像略缩图'''

        url = '/avatar/%s/' % str(user_id)
        if thumbnail is not None:
            url += thumbnail
        return url

    @classmethod
    def get_text(cls, html):
        '''将html去掉标签'''

        text = BeautifulSoup(
            html, "html.parser").get_text().replace(' ', '').replace('\n', '')
        return text

    @gen.coroutine
    def get_images(self, html):
        '''从html里边得到所有的图片'''

        url_list = []

        images = BeautifulSoup(html, "html.parser").find_all('img')
        if images:
            url_list = [image['src'] for image in images]

        raise gen.Return(url_list)

    @classmethod
    def translate_dbref(cls, dbref):
        db = Document.get_database(pymongo=True)
        return db[dbref.collection].find_one({'_id': ObjectId(dbref.id)})

    @classmethod
    def translate_dbref_in_document(cls, document, depth=1):
        for item in document:
            if not isinstance(document[item], DBRef):
                continue

            document[item] = cls.translate_dbref(document[item])

            if depth > 1:
                document[item] = cls.translate_dbref_in_document(
                    document[item], depth - 1
                )

        return document

    @classmethod
    def translate_dbref_in_document_list(cls, document_list, depth=1):
        return [
            cls.translate_dbref_in_document(document, depth)
            for document in document_list
        ]

    @classmethod
    def get_font_number(cls, string):
        '''得到string中值得个数，每个英文单词算是一个字，且每个英文单词长度
        不超过50
        '''

        result = re.findall('\w+', string)
        for item in result:
            if len(item) > 50:
                return len(string)

        string = re.sub('\w+', '', string)
        return len(string) + len(result)

    @classmethod
    def get_gridfs(cls, async=True):
        if async:
            db = Connection.get_database()
            fs = motor.MotorGridFS(db)
        else:
            db = Connection.get_database(pymongo=True)
            fs = gridfs.GridFS(db)

        return fs

    @classmethod
    def translate_byte(cls, size):
        UNIT = 1024

        BYTE = 1
        KB = UNIT * BYTE
        MB = UNIT * KB
        GB = UNIT * MB
        TB = UNIT * GB
        PB = UNIT * TB

        result = size

        size *= 1.0
        unit_dict = {BYTE: 'Bytes', KB: 'K', MB: 'M', GB: 'G', TB: 'T', PB: 'P'}

        unit_list = sorted(unit_dict.items(), cmp=lambda x, y: x[0] - y[0])
        for unit, symbol in unit_list:
            if size > unit:
                result = '%.1f' % (size / unit)
            else:
                if result[-2:] == '.0':
                    result = result[: -2]

                result += unit_dict[unit / UNIT]
                break

        return result

    @classmethod
    def paginate(cls, size, page_size, page):
        div, mod = divmod(size, page_size)
        total_page = div + bool(mod)

        block = (page - 1) / 10
        pages = range(block * 10 + 1, min(total_page, (block + 1) * 10) + 1)

        return total_page, pages


class BaseHandler(RequestHandler, UtilMixin):
    def initialize(self):
        '''重写父类的initialize函数'''

        self.es = self.settings["es"]
        self.session_manager = self.settings["session_manager"]

        # generate xsrf_token
        self.xsrf_token

    def get_current_user(self):
        session_id = self.get_secure_cookie('session_id')
        if not session_id:
            return

        session = self.session_manager.load_session(session_id)
        if not session:
            return

        user_agent = self.request.headers.get("User-Agent", None)
        ip = self.request.headers.get("X-Real-IP", None)

        # 验证user_agent和ip, 防止session劫持
        if (user_agent == session["user_agent"] and
                ip == session["ip"] and not session.expired()):

            user = app.user.document.UserDocument.get_user_sync(
                session.get('user_id'))

            if user:
                self.session = session
                return user

        session.clear()
        self.clear_cookie('session_id')

    def write_json(self, data):
        self.write(json.dumps(data))
        self.flush(include_footers=True)

    def get_theme(self):
        if not self.current_user:
            return "default"

        user_setting = app.user.document.UserSettingDocument.get_user_setting_sync(
            self.current_user['_id'])

        try:
            theme = user_setting['theme']
        except:
            theme = 'default'

        return theme
