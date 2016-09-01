# -*- coding: utf-8 -*-

import re
from StringIO import StringIO
from datetime import datetime

import Image
import simplejson as json
from tornado import gen
from tornado.web import authenticated, HTTPError
from bson.objectid import ObjectId
from bson.dbref import DBRef
from bson.binary import Binary

from lib.xmpp import Ejabberd
from young.handler import BaseHandler
from app.base.document import ImageDocument
from app.user.document import (
    UserDocument, AvatarDocument, UserSettingDocument,
    OfficialProfileCoverDocument)
from app.setting.form import (
    AvatarSetForm, ProfileSetForm, PasswordSetForm, ProfileCoverSetForm,
    PrivateSetForm, NotificationSetForm, ThemeSetForm)

__all__ = ['SettingHandler', 'AvatarSetHandler', 'ProfileCoverSetHander',
           'PasswordSetHandler', 'ProfileSetHandler', 'PrivateSetHandler',
           'ProfileCoverCustomHandler', 'NotificationSetHandler',
           'ThemeSetHandler']


class SettingHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, option):
        if option == 'avatar':
            avatar = yield AvatarDocument.find_one({
                'owner': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })

            self.render(
                'setting/template/setting-avatar.html',
                avatar=avatar,
                preview=self.get_avatar(self.current_user['_id'])
            )

        elif option == 'profile':
            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })

            self.render(
                'setting/template/setting-profile.html',
                user_setting=user_setting
            )

        elif option == 'password':
            self.render('setting/template/setting-password.html')

        elif option == 'profile/cover':
            cover_list_f = OfficialProfileCoverDocument.get_profile_cover_list
            profile_cover_list = yield cover_list_f()

            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })

            self.render(
                'setting/template/setting-profile-cover.html',
                profile_cover_list=profile_cover_list,
                user_setting=user_setting
            )

        elif option == 'private':
            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })

            self.render(
                'setting/template/setting-private.html',
                user_setting=user_setting
            )
        elif option == 'notification':
            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })
            self.render(
                'setting/template/setting-notification.html',
                user_setting=user_setting
            )
        elif option == 'theme':
            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                )
            })

            self.render(
                'setting/template/setting-theme.html',
                user_setting=user_setting
            )
        else:
            raise HTTPError(404)


class AvatarSetHandler(BaseHandler):
    '''设置头像'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = AvatarSetForm(self.request.arguments)
        if not form.validate() or 'avatar' not in self.request.files:
            raise HTTPError(404)

        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        target_width = form.target_width.data

        crop_area = {
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'target_width': target_width
        }

        upload_file = self.request.files['avatar'][0]

        document = {
            'name': upload_file['filename'],
            'upload_time': datetime.now(),
            'content': Binary(upload_file['body']),
            'content_type': upload_file['content_type'],
            'owner': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'crop_area': crop_area
        }

        try:
            image = Image.open(StringIO(upload_file['body']))
        except:
            raise HTTPError(404)

        scale = image.size[0] * 1.0 / target_width

        x = int(x * scale)
        y = int(y * scale)
        w = int(w * scale)
        h = int(h * scale)

        box = (x, y, x + w, y + h)
        image = image.crop(box)

        output50x50 = StringIO()
        output180x180 = StringIO()

        image50x50 = image.resize((50, 50), Image.ANTIALIAS)
        image180x180 = image.resize((180, 180), Image.ANTIALIAS)

        image50x50.save(
            output50x50,
            document['content_type'].split('/')[1].upper(),
            quality=100
        )
        image180x180.save(
            output180x180,
            document['content_type'].split('/')[1].upper(),
            quality=100
        )

        document['thumbnail50x50'] = Binary(output50x50.getvalue())
        document['thumbnail180x180'] = Binary(output180x180.getvalue())

        output50x50.close()
        output180x180.close()

        user_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(self.current_user['_id'])
        )

        yield AvatarDocument.remove({'owner': user_dbref}, multi=True)
        yield AvatarDocument.insert(document)
        yield UserDocument.update(
            {'_id': ObjectId(self.current_user['_id'])},
            {'$set': {'avatar_updated': True}}
        )

        self.finish()


class ProfileCoverSetHander(BaseHandler):
    '''设置个人封面'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = ProfileCoverSetForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        profile_cover_id = form.profile_cover_id.data
        profile_cover = yield OfficialProfileCoverDocument.find_one({
            '_id': ObjectId(profile_cover_id)
        })

        if not profile_cover:
            raise HTTPError(404)

        cover = DBRef(
            OfficialProfileCoverDocument.meta['collection'],
            ObjectId(profile_cover['_id'])
        )
        yield UserSettingDocument.set_profile_cover(
            self.current_user['_id'], cover
        )

        raise gen.Return()


class PasswordSetHandler(BaseHandler):
    '''设置密码'''

    @authenticated
    @gen.coroutine
    def post(self):
        response_data = {}

        form = PasswordSetForm(self.request.arguments)
        if form.validate():
            current_password = form.current_password.data
            new_password = form.new_password.data
            repeat_password = form.repeat_password.data

            encrypt_password = yield UserDocument.encrypt_password(
                current_password
            )

            if self.current_user['password'] != encrypt_password:
                response_data.update({'error': '密码错误!'})
            elif new_password != repeat_password:
                response_data.update({'error': '新密码与重复密码不一致!'})
            else:
                new_password = yield UserDocument.encrypt_password(
                    new_password
                )

                yield UserDocument.update(
                    {'_id': ObjectId(self.current_user['_id'])},
                    {'$set': {'password': new_password}}
                )

                try:
                    Ejabberd.unregister(self.current_user['_id'])
                    Ejabberd.register(self.current_user['_id'], new_password)
                except:
                    pass
        else:
            for field in form.errors:
                response_data.update({'error': form.errors[field][0]})
                break

        self.finish(json.dumps(response_data))


class ProfileSetHandler(BaseHandler):
    '''设置个人信息'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = ProfileSetForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        sex = form.sex.data
        birthday = form.birthday.data
        relationship_status = form.relationship_status.data
        province = form.province.data
        city = form.city.data
        phone = form.phone.data
        qq = form.qq.data
        signature = form.signature.data

        document = {}

        if birthday:
            year, month, day = map(int, birthday.split('-'))
            birthday = datetime(year, month, day)
            document.update({'birthday': birthday})

        if sex:
            document.update({'sex': sex})

        if relationship_status not in ['', 'single', 'in_love']:
            raise HTTPError(404)

        document.update({'relationship_status': relationship_status})

        if province and city:
            home = '%s-%s' % (province, city)
            if len(home) < 100:
                document.update({'home': home})
            else:
                raise HTTPError(404)

        regex = re.compile('^\d{11}$')
        document.update({'phone': phone})
        if phone and not regex.match(phone):
            response_data.update({'error': '手机号码错误!'})

        regex = re.compile('^\d{1,20}$')
        document.update({'qq': qq})
        if qq and not regex.match(qq):
            response_data.update({'error': 'qq号码错误!'})

        document.update({'signature': signature})
        if signature and len(signature) > 100:
            response_data.update({'error': '自我介绍不能超过100字!'})

        if not response_data:
            yield UserDocument.update(
                {'_id': ObjectId(self.current_user['_id'])},
                {'$set': document}
            )

        self.finish(json.dumps(response_data))


class PrivateSetHandler(BaseHandler):
    '''设置隐私'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = PrivateSetForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        require_verify_when_add_friend = form.require_verify_when_add_friend.data
        allow_stranger_visiting_profile = form.allow_stranger_visiting_profile.data
        allow_stranger_chat_with_me = form.allow_stranger_chat_with_me.data
        enable_leaving_message = form.enable_leaving_message.data

        yield UserSettingDocument.update(
            {'user': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            )},
            {'$set': {
                'require_verify_when_add_friend': require_verify_when_add_friend,
                'allow_stranger_visiting_profile': allow_stranger_visiting_profile,
                'allow_stranger_chat_with_me': allow_stranger_chat_with_me,
                'enable_leaving_message': enable_leaving_message
            }}
        )

        self.finish()


class NotificationSetHandler(BaseHandler):
    '''设置隐私'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = NotificationSetForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        email_notify_when_offline = form.email_notify_when_offline.data

        yield UserSettingDocument.update(
            {'user': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            )},
            {'$set': {'email_notify_when_offline': email_notify_when_offline}}
        )

        self.finish()


class ProfileCoverCustomHandler(BaseHandler):
    '''上传自定义个人封面'''

    @authenticated
    @gen.coroutine
    def post(self):
        if 'cover' not in self.request.files:
            raise HTTPError(404)

        upload_file = self.request.files['cover'][0]

        try:
            Image.open(StringIO(upload_file['body']))
        except:
            raise HTTPError(404)

        uploader = DBRef(
            UserDocument.meta['collection'],
            ObjectId(self.current_user['_id'])
        )
        image_id = yield ImageDocument.insert_one(
            upload_file,
            thumbnail_width=960,
            uploader=uploader,
            upload_time=datetime.now()
        )

        cover = DBRef(ImageDocument.meta['collection'], ObjectId(image_id))
        yield UserSettingDocument.set_profile_cover(
            self.current_user['_id'], cover
        )

        self.finish()


class ThemeSetHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = ThemeSetForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        theme = form.theme.data

        yield UserSettingDocument.update(
            {'user': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            )},
            {'$set': {'theme': theme}}
        )

        self.finish()
