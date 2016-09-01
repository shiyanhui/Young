# -*- coding: utf-8 -*-

import time
from datetime import datetime

import simplejson
from tornado import gen
from tornado.web import authenticated, asynchronous, HTTPError
from bson.dbref import DBRef
from bson.objectid import ObjectId

from young.handler import BaseHandler
from lib.xmpp.client import XMPPClient, XMPPClientManager
from lib.xmpp.browser import BrowserClientManager
from app.user.document import UserDocument
from app.chat.document import ChatMessageDocument
from app.chat.form import MessageNewForm, MessageUpdateForm, MessageHistoryForm


class ChatWithHandler(BaseHandler):
    @authenticated
    @asynchronous
    def post(self):
        self.render('chat/template/chat.html')


class MessageNewHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        '''浏览器端发来消息'''

        form = MessageNewForm(self.request.arguments)
        if not form.validate() or form.chat_with.data == str(
                self.current_user['_id']):
            raise HTTPError(404)

        body = form.body.data
        chat_with = form.chat_with.data

        # 是否严格的设置不能同陌生人条聊天?
        # user_setting = yield UserSettingDocument.get_user_setting(chat_with)
        # is_friend = yield FriendDocument.is_friend(self.current_user['_id'], chat_with)

        # if not is_friend and not user_setting['allow_stranger_chat_with_me']:
        #     raise HTTPError(404)

        mto = XMPPClient.make_jid(chat_with)

        sender = DBRef(
            UserDocument.meta['collection'], ObjectId(self.current_user['_id']))
        recipient = DBRef(UserDocument.meta['collection'], ObjectId(chat_with))
        between = [sender, recipient]

        message = {
            'body': body,
            'between': between,
            'sender': sender,
            'recipient': recipient,
            'send_time': datetime.now(),
        }
        msg_id = yield ChatMessageDocument.insert(message)

        client = XMPPClientManager.get_xmppclient(
            self.current_user['_id'], self.current_user['password'])

        client.send_message(
            mto=mto, mbody=body, msubject=str(msg_id), mtype='chat')

        self.render('chat/template/message-mine.html', message=message)


class MessageUpdateHandler(BaseHandler):
    @authenticated
    @asynchronous
    def post(self):
        form = MessageUpdateForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        self.chat_with_id = form.chat_with.data
        self.current_user_id = str(self.current_user['_id'])

        if self.current_user_id == self.chat_with_id:
            raise HTTPError(404)

        BrowserClientManager.add(
            self.current_user_id, self.chat_with_id, self.new_message)

    def new_message(self, msg):
        '''新消息: Ejabberd服务器 => XMPPClient => Broswer => Here(callback)'''

        if self.request.connection.stream.closed():
            return

        message = ChatMessageDocument.get_collection(pymongo=True).find_one(
            {'_id': ObjectId(str(msg['subject']))}
        )
        BrowserClientManager.remove(self.current_user_id, self.chat_with_id)

        self.render('chat/template/message-others.html', message=message)

    def on_connection_close(self):
        BrowserClientManager.remove(self.current_user_id, self.chat_with_id)


class MessageHistoryHandler(BaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = MessageHistoryForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        chat_with = form.chat_with.data
        since = datetime.fromtimestamp(form.since.data / 1000)

        id_a = self.current_user['_id']
        id_b = chat_with

        response_data = {'has': 0}

        history_messages = yield ChatMessageDocument.get_history_messages(
            id_a, id_b, since
        )

        if history_messages:
            since = time.mktime(
                history_messages[0]['send_time'].timetuple()
            ) * 1000
            html = self.render_string(
                'chat/template/message-chat.html',
                history_messages=history_messages
            )
            response_data.update({'has': 1, 'since': since, 'html': html})

        self.finish(simplejson.dumps(response_data))
