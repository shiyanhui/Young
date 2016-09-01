# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
from sleekxmpp import ClientXMPP

from lib.xmpp.browser import BrowserClientManager
from app.chat.document import ChatMessageDocument

__all__ = ['XMPPClient', 'XMPPClientManager']


class XMPPClient(ClientXMPP):
    def __init__(self, jid, password):
        ClientXMPP.__init__(self, jid, password)

        self.add_event_handler('session_start', self.session_start)
        self.add_event_handler('message', self.message)

        self._jid = jid
        self._password = password

    def session_start(self, event):
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        '''收到Ejabberd服务器发来的信息, 判断后发到browser端'''

        if msg['type'] == 'chat':
            # 只有上线后才能收到信息
            ChatMessageDocument.get_collection(True).update(
                {'_id': ObjectId(str(msg['subject']))},
                {'$set': {'received': True}})

            BrowserClientManager.new_message(msg)

    def start(self):
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0004')  # Data Forms
        self.register_plugin('xep_0060')  # PubSub
        self.register_plugin('xep_0199')  # XMPP Ping

        if self.connect():
            self.process(block=False)

    @classmethod
    def make_jid(cls, _id, host='localhost'):
        return "%s@%s" % (_id, host)

    @classmethod
    def jid2objectid(cls, jid):
        objectid = None
        try:
            objectid = str(jid).split('@')[0]
        except:
            pass

        return objectid


class XMPPClientManager(object):
    _clients = {}

    @classmethod
    def has(cls, jid):
        return str(jid) in cls._clients

    @classmethod
    def add(cls, jid, client):
        c = cls.get(jid)
        if c is not None:
            c.disconnect()

        cls._clients[str(jid)] = client

    @classmethod
    def remove(cls, jid):
        try:
            client = cls._clients.pop(str(jid))
            client.disconnect()
        except:
            pass

    @classmethod
    def get(cls, jid):
        return cls._clients.get(str(jid), None)

    @classmethod
    def get_xmppclient(cls, user_id, password):
        jid = XMPPClient.make_jid(user_id)
        client = XMPPClientManager.get(jid)

        if client is None:
            client = XMPPClient(jid, password)
            XMPPClientManager.add(jid, client)
            client.start()

        return client

    @classmethod
    def logout(cls, user_id):
        jid = XMPPClient.make_jid(user_id)
        cls.remove(jid)
