# -*- coding: utf-8 -*-

import os
import time
import random
import hashlib
import email.utils
from datetime import datetime, timedelta

import simplejson as json
from tornado import gen
from tornado.web import authenticated, HTTPError
from bson.objectid import ObjectId
from bson.dbref import DBRef
from bson.binary import Binary

from lib.xmpp import Ejabberd, XMPPClient, XMPPClientManager
from lib.message import WriterManager
from young.handler import BaseHandler
from young.setting import APPLICATION_SETTINGS
from app.message.document import MessageTopic
from app.user.setting import USER_SETTINGS
from app.user.form import (
    LoginForm, RegisterForm, AccountActiveForm,
    PasswordResetSendmailForm, PasswordResetGetForm,
    PasswordResetPostForm, AccountActiveSendmailForm
)
from app.user.document import (
    AvatarDocument, UserDocument, OfficialProfileCoverDocument,
    UserSettingDocument, CodeDocument, WealthRecordDocument,
    UserActivityDocument
)

__all__ = ['LoginHandler', 'LogoutHandler', 'AvatarStaticFileHandler',
           'ProfileCoverStaticFileHandler', 'RegisterTemplateHandler',
           'RegisterHandler', 'AccountActiveHandler',
           'PasswordResetSendmailHandler', 'PasswordResetHandler',
           'AccountActiveSendmailHandler', 'FetchLoginRewardHandler']


class LoginHandler(BaseHandler):
    '''登陆'''

    @gen.coroutine
    def get(self):
        if self.current_user:
            self.redirect("/community")
        else:
            self.render('user/template/login.html')

    @gen.coroutine
    def post(self):
        response_data = {
            "next": self.get_argument("next", "/")
        }

        form = LoginForm(self.request.arguments)
        if form.validate():
            email = form.email.data
            password = form.password.data

            encrypt_password = yield UserDocument.encrypt_password(password)

            user = yield UserDocument.find_one({
                'email': email,
                'password': encrypt_password
            })

            if user:
                if not user['activated']:
                    response_data.update({
                        'error': '该账号尚未被激活! 请登录该邮箱以激活该账号! '
                                 '或者 <a href="#resend-activation-email-modal" '
                                 'class="red-color" id="resend-activation-email-link">'
                                 '重新发送激活邮件</a>'
                    })
                elif user['forbidden_login']:
                    response_data.update({
                        'error': '你的账号已于%s被冻结, 冻结时间为一周. 冻结原因: %s. 请你一周后再登录!' % (
                            user['forbidden_login_info'][-1]['time'].strftime('%m 月 %d 日 %H:%M'),
                            user['forbidden_login_info'][-1]['reason']
                        )
                    })
                else:
                    if not Ejabberd.registered(user['_id']):
                        Ejabberd.register(user['_id'], user['password'])

                    session = self.session_manager.new_session()
                    session.set('user_id', user['_id'])
                    session.set(
                        "ip", self.request.headers.get("X-Real-IP", None)
                    )
                    session.set(
                        'user_agent',
                        self.request.headers.get("User-Agent", None)
                    )

                    # 添加httponly，防止javascript获得session_id
                    self.set_secure_cookie(
                        'session_id', session.id, httponly=True
                    )
            else:
                response_data.update({'error': '邮箱或者密码错误!'})
        else:
            for field in form.errors:
                response_data.update({'error': form.errors[field][0]})
                break

        self.finish(json.dumps(response_data))


class LogoutHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        user_id = self.session.get('user_id')
        jid = XMPPClient.make_jid(user_id)
        XMPPClientManager.remove(jid)

        self.session.clear()
        self.clear_all_cookies()

        self.redirect('/')


class RegisterTemplateHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        self.render('user/template/register.html')


class RegisterHandler(BaseHandler):
    @gen.coroutine
    def post(self):
        response_data = {}

        form = RegisterForm(self.request.arguments)
        if form.validate():
            name = form.name.data
            email = form.email.data
            password = form.password.data

            if (yield UserDocument.find_one({'name': name})):
                response_data["error"] = "用户名已被占用"

            if (yield UserDocument.find_one({"email": email})):
                response_data["error"] = "邮箱已被注册"

            if not response_data:
                password = yield UserDocument.encrypt_password(password)

                document = {
                    'email': email,
                    'name': name,
                    'password': password,
                    'user_type': "person",
                    'register_date': datetime.now()
                }

                try:
                    user_id = yield UserDocument.insert(document)
                except:
                    raise HTTPError(500)

                # 头像初始化
                avatar = open(os.path.join(
                    APPLICATION_SETTINGS['static_path'], 'img/default.jpg')
                )
                content = avatar.read()
                avatar.close()

                document = {
                    'name': 'default.jpg',
                    'upload_time': datetime.now(),
                    'content_type': 'jpeg',
                    'owner': DBRef(
                        UserDocument.meta['collection'], ObjectId(user_id)
                    ),
                    'content': Binary(content),
                    'thumbnail50x50': Binary(content),
                    'thumbnail180x180': Binary(content)
                }
                yield AvatarDocument.insert(document)

                # 用户设置初始化
                _ = yield OfficialProfileCoverDocument.get_profile_cover_list()
                profile_cover = random.sample(_, 1)[0]

                document = {
                    'user': DBRef(
                        UserDocument.meta['collection'], ObjectId(user_id)
                    ),
                    'profile_cover': DBRef(
                        OfficialProfileCoverDocument.meta['collection'],
                        ObjectId(profile_cover['_id'])
                    )
                }
                yield UserSettingDocument.insert(document)

                # Ejabberd注册
                try:
                    Ejabberd.register(user_id, password)
                except:
                    pass

                # 给用户发送验证邮件
                document = {
                    'uid': user_id,
                    'code': CodeDocument.generate_code(),
                    'expired_time': datetime.now() + timedelta(
                        days=USER_SETTINGS['code_expired_after']
                    )
                }
                code_id = yield CodeDocument.insert(document)
                WriterManager.pub(MessageTopic.SEND_ACTIVATION_EMAIL, code_id)

                response_data.update({
                    'success': '注册成功! 系统已经向你的注册邮箱发送了一封激活'
                               '邮件, 请验证后登录!'
                })

        else:
            for field in form.errors:
                response_data.update({'error': form.errors[field][0]})
                break

        self.finish(json.dumps(response_data))


class AvatarStaticFileHandler(BaseHandler):
    def _send_avatar(self, avatar, thumbnail):
        hasher = hashlib.sha1()
        content = str(
            avatar['content'] if thumbnail is None else avatar[thumbnail]
        )
        hasher.update(content)

        self.set_header('Etag', '"%s"' % hasher.hexdigest())
        self.finish(content)

    @gen.coroutine
    def get(self, user_id, thumbnail=None):
        avatar = yield AvatarDocument.find_one({
            'owner': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })

        modified = avatar['upload_time']

        self.set_header('Last-Modified', modified)
        self.set_header('Content-Type', avatar['content_type'])
        self.set_header('Cache-Control', 'public')

        ims_value = self.request.headers.get('If-Modified-Since')
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.fromtimestamp(time.mktime(date_tuple))

            if if_since >= modified.replace(microsecond=0):
                self.set_status(304)
                self.finish()
            else:
                self._send_avatar(avatar, thumbnail)
        else:
            self._send_avatar(avatar, thumbnail)


class ProfileCoverStaticFileHandler(BaseHandler):
    @gen.coroutine
    def get(self, cover_type, id_, content_type=None):
        if cover_type == 'user':
            user_setting = yield UserSettingDocument.find_one({
                'user': DBRef(UserDocument.meta['collection'], ObjectId(id_))
            })

            profile_cover = yield OfficialProfileCoverDocument.find_one({
                '_id': ObjectId(user_setting['profile_cover'].id)
            })
        else:
            profile_cover = yield OfficialProfileCoverDocument.find_one({
                '_id': ObjectId(id_)
            })

        content = str(profile_cover['content'])
        if content_type is not None:
            content = str(
                profile_cover['profile_content']
                if content_type == 'profile-content' else
                profile_cover['setting_content']
            )

        self.finish(content)


class AccountActiveSendmailHandler(BaseHandler):
    '''重新发送激活邮件'''

    @gen.coroutine
    def post(self):
        form = AccountActiveSendmailForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}
        email = form.email.data

        user = yield UserDocument.find_one({'email': email})
        if not user:
            raise HTTPError(404)

        if user['activated']:
            response_data.update({'error': '该账号已经激活!'})
        else:
            document = {
                'uid': user["_id"],
                'code': CodeDocument.generate_code(),
                'expired_time': datetime.now() + timedelta(
                    days=USER_SETTINGS['code_expired_after']
                )
            }

            yield CodeDocument.remove({"uid": user["_id"]}, multi=True)

            code_id = yield CodeDocument.insert(document)
            WriterManager.pub(MessageTopic.SEND_ACTIVATION_EMAIL, code_id)

        self.finish(json.dumps(response_data))


class AccountActiveHandler(BaseHandler):
    '''从激活邮件里过来, 激活账号'''

    @gen.coroutine
    def get(self):
        form = AccountActiveForm(self.request.arguments)
        if not form:
            raise HTTPError(404)

        response_data = {}

        uid = form.uid.data
        code = form.code.data

        user = yield UserDocument.find_one({'_id': ObjectId(uid)})
        if not user:
            raise HTTPError(404)

        code = yield CodeDocument.find_one({'uid': user["_id"], 'code': code})
        if not code:
            raise HTTPError(404)

        if user['activated']:
            response_data.update({'error': '该账号已经激活!'})
        elif code['expired_time'] < datetime.now():
            response_data.update({
                'error': '激活码已失效! 请返回到登录界面重新发送激活码!'
            })
        else:
            yield UserDocument.update(
                {'_id': user['_id']},
                {'$set': {'activated': True}}
            )
            response_data.update({'error': '激活成功!'})

        yield CodeDocument.remove({'_id': code['_id']})

        self.render('user/template/feedback.html', response_data=response_data)


class PasswordResetSendmailHandler(BaseHandler):
    '''往邮箱里边发送重设密码邮件'''

    @gen.coroutine
    def post(self):
        form = PasswordResetSendmailForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}
        email = form.email.data

        user = yield UserDocument.find_one({'email': email})
        if not user:
            raise HTTPError(404)

        if not user['activated']:
            response_data.update({'error': '该账号尚未激活, 请先激活账号!'})
        else:
            document = {
                'uid': user["_id"],
                'code': CodeDocument.generate_code(),
                'expired_time': datetime.now() + timedelta(
                    days=USER_SETTINGS['code_expired_after']
                )
            }

            yield CodeDocument.remove({"uid": user["_id"]}, multi=True)

            code_id = yield CodeDocument.insert(document)
            WriterManager.pub(MessageTopic.SEND_RESET_PASSWORD_EMAIL, code_id)

        self.finish(json.dumps(response_data))


class PasswordResetHandler(BaseHandler):
    '''从验证邮件里过来, 重设密码'''

    @gen.coroutine
    def get(self):
        # 刷新失效
        session_id = self.get_secure_cookie('sid')
        if session_id:
            session = self.session_manager.load_session(session_id)

            yield CodeDocument.remove({
                'uid': ObjectId(session["uid"]),
                'code': session["code"]
            })

            session.clear()
            self.clear_cookie("sid")

        form = PasswordResetGetForm(self.request.arguments)
        if not form:
            raise HTTPError(404)

        response_data = {}

        uid = form.uid.data
        code = form.code.data

        user = yield UserDocument.find_one({'_id': ObjectId(uid)})
        if not user:
            raise HTTPError(404)

        code = yield CodeDocument.find_one({
            'uid': user["_id"],
            'code': code
        })
        if not code or datetime.now() > code['expired_time']:
            response_data.update({
                'error': '验证码已失效! 请返回到登录界面重新发送验证邮件!'
            })

        if response_data:
            self.clear_cookie('sid')
            self.render(
                'user/template/feedback.html',
                response_data=response_data
            )
        else:
            session = self.session_manager.new_session()
            session["uid"] = uid
            session["code"] = code["code"]

            self.set_secure_cookie('sid', session.id, httponly=True)
            self.render('user/template/password-reset.html')

    @gen.coroutine
    def post(self):
        form = PasswordResetPostForm(self.request.arguments)
        if not form:
            raise HTTPError(404)

        password = form.password.data

        session_id = self.get_secure_cookie('sid')
        if not session_id:
            raise HTTPError(404)

        self.session = self.session_manager.load_session(session_id)

        uid = self.session.get('uid')
        code = self.session.get('code')

        if not uid or not code:
            raise HTTPError(404)

        code = yield CodeDocument.find_one({
            'uid': ObjectId(uid),
            'code': code
        })
        if not code:
            raise HTTPError(404)

        user = yield UserDocument.find_one({'_id': ObjectId(uid)})
        if not user:
            raise HTTPError(404)

        password = yield UserDocument.encrypt_password(password)
        yield UserDocument.update(
            {'_id': user["_id"]},
            {'$set': {'password': password}}
        )
        yield CodeDocument.remove({'_id': ObjectId(code['_id'])})

        try:
            Ejabberd.unregister(user['_id'])
            Ejabberd.register(user['_id'], password)
        except:
            pass

        self.session.clear()
        self.clear_cookie('sid')

        self.finish()


class FetchLoginRewardHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        response_data = {}

        login_reward_fetched = yield UserActivityDocument.login_reward_fetched(
            self.current_user['_id']
        )

        if login_reward_fetched:
            response_data.update({'error': '你已经领取了今日的登录奖励！'})
        else:
            now = datetime.now()

            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'activity_type': UserActivityDocument.FETCH_LOGIN_REWARD,
                'time': now
            }
            activity_id = yield UserActivityDocument.insert(document)

            continuous_login_days = yield UserDocument.get_continuous_login_days(
                self.current_user['_id']
            )
            quantity = (1 + continuous_login_days / 7) * 5

            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'activity': DBRef(
                    UserActivityDocument.meta['collection'],
                    ObjectId(activity_id)
                ),
                'in_out_type': WealthRecordDocument.IN,
                'quantity': quantity,
                'time': now
            }
            yield WealthRecordDocument.insert(document)

            yield UserDocument.update_wealth(
                self.current_user['_id'], quantity
            )
            yield UserDocument.update(
                {'_id': ObjectId(self.current_user['_id'])},
                {'$inc': {'continuous_login_days': 1}}
            )

            continuous_login_days = yield UserDocument.get_continuous_login_days(
                self.current_user['_id']
            )

            response_data.update({
                'wealth': self.current_user['wealth'] + quantity,
                'continuous_login_days': continuous_login_days
            })

        self.finish(json.dumps(response_data))
