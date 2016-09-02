# -*- coding: utf-8 -*-

import time

from bson.objectid import ObjectId
from tornado.web import authenticated, asynchronous, HTTPError
from tornado.escape import xhtml_escape

from lib.message import BrowserCallbackManager
from lib.xmpp import XMPPClientManager
from young.handler import BaseHandler
from app.chat.document import ChatMessageDocument
from app.user.document import UserDocument
from app.message.document import MessageDocument, MessageTopic
from app.message.form import MessageUpdaterForm


__all__ = ['MessageUpdaterHandler']


class MessageUpdaterHandler(BaseHandler):
    '''与浏览器端建立长连接, 以更新消息'''

    @authenticated
    @asynchronous
    def post(self):
        form = MessageUpdaterForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        n = form.n.data

        XMPPClientManager.get_xmppclient(
            self.current_user['_id'], self.current_user['password']
        )

        has_unreceived = MessageDocument.has_unreceived(
            self.current_user['_id']
        )
        has_unread_chat_message = ChatMessageDocument.has_unread_chat_message(
            self.current_user['_id']
        )

        if n == 1 or has_unreceived:
            unread_message_numbers = MessageDocument.get_unread_message_numbers(
                self.current_user['_id']
            )
            MessageDocument.set_received(self.current_user['_id'])

            kwargs = {
                'unread_message_numbers': unread_message_numbers,
                'MessageTopic': MessageTopic
            }

            html = self.render_string(
                'message/template/message-header.html',
                **kwargs
            )

            self.write_json({
                'topic': 'unread_message_numbers', 'html': html
            })
            self.finish()

        elif has_unread_chat_message:
            messages = ChatMessageDocument.get_unread_messages(
                self.current_user['_id']
            )
            response_data = self._new_chat_message_handler(messages)

            ChatMessageDocument.set_read(self.current_user['_id'])

            self.write_json(response_data)
            self.finish()
        else:
            BrowserCallbackManager.add(
                self.current_user['_id'], self.new_message
            )

    def _new_chat_message_handler(self, messages):
        '''处理未读的聊天信息, 返回前端易于处理的json格式. 返回的格式为:
        {
            'topic': MessageTopic.CHAT_MESSAGE_NEW,
            'each_people':
            [
                {
                    'sender': {'id': xxx, 'name': xxx},
                    'messages':
                    [
                        {
                            'body': xxx,
                            'html': xxx,
                            'since': xxx
                        },
                    ]
                },
            ]
        }

        :Parameters:
            - `messages`: ChatMessageDocument.get_unread_messages()相同的格式. 即:
              [
                  {
                      '_id': xxx,
                      'messages':
                      [
                          {
                              'send_time': xxx,
                              'body': xxx,
                          },
                      ]
                  },
              ]
        '''

        response_data = {
            'topic': MessageTopic.CHAT_MESSAGE_NEW,
            'each_people': []
        }
        for item in messages:
            sender_id = str(item['_id'].id)
            sender = UserDocument.get_collection(pymongo=True).find_one({
                '_id': ObjectId(sender_id)
            })

            each_people = {
                'sender': {
                    'id': sender_id,
                    'name': sender['name']
                },
                'messages': []
            }
            for message in item['messages']:
                html = self.render_string(
                    "chat/template/message-others.html",
                    message=message, handler=self
                )

                new_message = {
                    'body': xhtml_escape(message['body']),
                    'html': html,
                    'since': time.mktime(
                        message['send_time'].timetuple()
                    ) * 1000
                }
                each_people['messages'].append(new_message)
            response_data['each_people'].append(each_people)

        return response_data

    def _new_message_handler(self, message):
        message['message'] = self.translate_dbref_in_document(
            message['message']
        )
        if 'data' in message['message']:
            message['message']['data'] = self.translate_dbref_in_document(
                message['message']['data'], depth=2
            )

        message_topic = message['topic']
        message = message['message']

        kwargs = {
            'message_topic': message_topic,
            'message': message,
            'MessageTopic': MessageTopic
        }

        html = self.render_string('message/template/message.html', **kwargs)
        return {'topic': message_topic, 'html': html}

    def new_message(self, data):
        '''收到nsq服务器的新消息, data必须具有`topic`和`message`两个字段,
        分别用来保存消息的topic和具体消息内容, 你需要在相关消费者的handler里边封装之.
        data结构如下所示.
        {
            'topic': xxx,
            'message': xxx
        }
        '''
        if self.request.connection.stream.closed():
            return

        assert isinstance(data, dict)
        assert 'topic' in data
        assert 'message' in data

        MessageDocument.set_read_sync(self.current_user['_id'], data['topic'])

        if data['topic'] == MessageTopic.CHAT_MESSAGE_NEW:
            # 将该消息标记为已读
            ChatMessageDocument.get_collection(pymongo=True).update(
                {'_id': ObjectId(data['message']['_id'])},
                {'$set': {'read': True}}
            )

            messages = [{
                '_id': data['message']['sender'],
                'messages': [data['message']]
            }]
            response_data = self._new_chat_message_handler(messages)
        else:
            response_data = self._new_message_handler(data)

        self.write_json(response_data)
        self.finish()

    def on_connection_close(self):
        BrowserCallbackManager.remove(self.current_user['_id'])
        # XMPPClientManager.logout(self.current_user['_id'])
