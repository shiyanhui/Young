# -*- coding: utf-8 -*-

import os
import smtplib
import logging
from email.mime.text import MIMEText

from bson.objectid import ObjectId
from tornado import template
from bs4 import BeautifulSoup

from young.setting import EMAIL_SETTINGS
from lib.message.topic import MessageTopic
from lib.message.browser import BrowserCallbackManager
from lib.message.writer import WriterManager

__all__ = ['chat_message_handler', 'message_handler',
           'send_activation_email_handler',
           'send_reset_password_email_handler',
           'send_has_unread_message_email_handler']


def send_email(receiver, msg):
    sender = "Young社区<%s>" % EMAIL_SETTINGS["robot"]
    receiver = receiver

    msg["from"] = sender
    msg["to"] = receiver

    s = smtplib.SMTP(EMAIL_SETTINGS["host"], EMAIL_SETTINGS["port"])
    s.sendmail(sender, receiver, msg.as_string())
    s.quit()


def _send_email_handler(message, type_="activate"):
    from app.user.document import CodeDocument, UserDocument

    code_id = message.body

    code = CodeDocument.get_collection(True).find_one({
        '_id': ObjectId(code_id)
    })
    if not code:
        return True

    user = UserDocument.get_collection(True).find_one({
        "_id": ObjectId(code["uid"])
    })
    if not user:
        return True

    if type_ == "activate":
        subject = "账号激活【Young社区】"
        tpl = ''.join([
            '请点击链接激活你的Young社区帐号！',
            '<a href="{0}/account/active?uid={1}&code={2}">',
            '{0}/account/active?uid={1}&code={2}</a>'
        ])
    else:
        subject = "密码重置【Young社区】"
        tpl = ''.join([
            '请点击链接重置你的Young社区账号密码！',
            '<a href="{0}/password/reset?uid={1}&code={2}">',
            '{0}/password/reset?uid={1}&code={2}</a>'
        ])

    body = tpl.format(EMAIL_SETTINGS['url'], code['uid'], code['code'])

    msg = MIMEText(body, "html", 'utf-8')
    msg["subject"] = subject

    try:
        send_email(user['email'], msg)
    except Exception as e:
        logging.error('%s' % e)

    return True


def send_activation_email_handler(message):
    '''发送激活邮件'''

    return _send_email_handler(message, type_="activate")


def send_reset_password_email_handler(message):
    return _send_email_handler(message, type_="reset_password")


def send_has_unread_message_email_handler(message):
    '''如果用户不在线就发送邮件'''

    from young.handler import BaseHandler
    from app.user.document import UserDocument
    from app.message.document import MessageDocument

    message = MessageDocument.get_collection(pymongo=True).find_one(
        {'_id': ObjectId(message.body)}
    )

    if not message:
        return True

    recipient_id = message['recipient'].id
    topic = MessageTopic.message_type2topic(message['message_type'])

    recipient = UserDocument.get_user_sync(recipient_id)
    if recipient and recipient['activated']:
        message = BaseHandler.translate_dbref_in_document(message)
        if 'data' in message:
            message['data'] = BaseHandler.translate_dbref_in_document(
                message['data'], depth=2
            )

        kwargs = {
            'message_topic': topic,
            'message': message,
            'MessageTopic': MessageTopic,
            'handler': BaseHandler
        }

        root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        ))
        path = os.path.join(root, 'app/message/template')

        loader = template.Loader(path)
        html = loader.load("message.html").generate(**kwargs)

        soup = BeautifulSoup(html, "html.parser")
        link_list = soup.find_all('a')
        for link in link_list:
            new_link = link
            if link['href'].startswith('/'):
                new_link['href'] = EMAIL_SETTINGS['url'] + link['href']
                link.replace_with(new_link)

        img_list = soup.find_all('img')
        for img in img_list:
            new_img = img
            if img['src'].startswith('/'):
                new_img['src'] = EMAIL_SETTINGS['url'] + img['src']
                img.replace_with(new_img)

        body = (
            '{} &nbsp;&nbsp; <a href="{}/setting/notification">'
            '关闭邮件提醒</a>'
        ).format(soup.prettify(), EMAIL_SETTINGS["url"])

        msg = MIMEText(body, "html", 'utf-8')
        msg["subject"] = "你有未读消息【Young社区】"
        send_email(recipient['email'], msg)

    return True


def chat_message_handler(message):
    '''topic: 'CHAT_MESSAGE'

    用户在线的话, 调用callback. 不在线的保存成离线消息.
    '''

    from app.chat.document import ChatMessageDocument

    message = ChatMessageDocument.get_collection(
        pymongo=True).find_one({'_id': ObjectId(message.body)})

    if not message:
        return True

    user_id = message['recipient'].id
    callback = BrowserCallbackManager.get(user_id)

    if callback:
        message = {
            'topic': MessageTopic.CHAT_MESSAGE_NEW,
            'message': message
        }

        try:
            callback(message)
        except:
            pass

    return True


def _reponse_browser_callback(recipient_id, topic, message):
    from app.user.document import UserSettingDocument

    callback = BrowserCallbackManager.get(recipient_id)

    if callback:
        message = {
            'topic': topic,
            'message': message
        }

        try:
            callback(message)
        except:
            pass

        return True

    user_setting = UserSettingDocument.get_user_setting_sync(
        recipient_id
    )
    if user_setting['email_notify_when_offline']:
        WriterManager.pub(
            MessageTopic.SEND_HAS_UNREAD_MESSAGE_EMAIL,
            message['_id']
        )

    return True


def message_handler(message):
    '''向用户发送消息'''

    from app.message.document import MessageDocument

    message = MessageDocument.get_collection(pymongo=True).find_one(
        {'_id': ObjectId(message.body)}
    )

    if not message:
        return True

    recipient_id = message['recipient'].id
    topic = MessageTopic.message_type2topic(message['message_type'])

    _reponse_browser_callback(recipient_id, topic, message)
    return True
