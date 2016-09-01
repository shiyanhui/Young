# -*- coding: utf-8 -*-

import sys
import os
from signal import signal, SIGINT

import nsq
from monguo.connection import Connection
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.options import define, options, parse_command_line
from tornado.httpserver import HTTPServer
from elasticsearch import Elasticsearch
from torsession.sync import SessionManager

from young import setting, urlmap
from lib.message import (
    WriterManager, MessageTopic, chat_message_handler,
    send_activation_email_handler, send_reset_password_email_handler,
    send_has_unread_message_email_handler, message_handler
)


def register_message_writers():
    '''为nsq消息系统建立生产者'''

    WriterManager.writer = nsq.Writer(['127.0.0.1:4150'])


def register_message_readers():
    '''为nsq消息系统建立消费者'''

    for topic in MessageTopic.all_topic:
        handler = None

        if topic == MessageTopic.CHAT_MESSAGE_NEW:
            handler = chat_message_handler

        elif topic == MessageTopic.SEND_ACTIVATION_EMAIL:
            handler = send_activation_email_handler

        elif topic == MessageTopic.SEND_RESET_PASSWORD_EMAIL:
            handler = send_reset_password_email_handler

        elif topic == MessageTopic.SEND_HAS_UNREAD_MESSAGE_EMAIL:
            handler = send_has_unread_message_email_handler

        else:
            handler = message_handler

        if handler is not None:
            reader = {
                'message_handler': handler,
                "nsqd_tcp_addresses": ['127.0.0.1:4150'],
                'topic': topic,
                'channel': topic,
                'lookupd_poll_interval': 15
            }

            nsq.Reader(**reader)


# controlling is in c, Crtl^C won't exit, so we should kill self
def suicide(signum, frame):
    os.system("kill -9 %d" % os.getpid())


def runserver():
    '''启动服务器'''

    signal(SIGINT, suicide)

    # for sleekxmpp
    reload(sys)
    sys.setdefaultencoding('utf8')

    define('port', default=8000, help='run on the given port', type=int)
    define("database", default="Young", help="database to use", type=str)
    define("debug", default=False, help="whether is debug mode", type=bool)

    parse_command_line()

    register_message_writers()
    register_message_readers()

    Connection.connect(options.database)

    setting.APPLICATION_SETTINGS.update({
        "debug": options.debug,
        "template_path": os.path.join(
            setting.ROOT_LOCATION,
            "app" if options.debug else "templates"
        ),
        "es": Elasticsearch(),
        "session_manager": SessionManager(
            Connection.get_database(pymongo=True).session
        )
    })
    application = Application(
        handlers=urlmap.urlpattern,
        **setting.APPLICATION_SETTINGS
    )

    http_server = HTTPServer(application, xheaders=True)
    http_server.listen(options.port)

    IOLoop.instance().start()


if __name__ == '__main__':
    runserver()
