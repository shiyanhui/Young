# -*- coding: utf-8 -*-

__all__ = ['MessageTopic']


class MessageTopic(object):
    '''消息类型

    注意: 在此处添加新的类型后别忘了在`MessageDocument`的`message_type`变量里添加

    :Variables:
      - `CHAT_MESSAGE_NEW`: 新私聊信息
      - `COMMENT`: 评论
      - `REPLY`: 回复
      - `LIKE`: 赞
      - `AT`: @
      - `STATUS_NEW`: 朋友发表新状态时
      - `TOPIC_NEW`: 朋友发表新话题时
      - `FRIEND_REQUEST_NEW`: 新好友请求
      - `LEAVE_MESSAGE_NEW`: 新留言
      - `SHARE_NEW`: 朋友发布了新的分享

      - `SEND_ACTIVATION_EMAIL`: 给用户发送激活邮件
      - `SEND_RESET_PASSWORD_EMAIL`: 给用户发送重置密码邮件
      - `SEND_HAS_UNREAD_MESSAGE_EMAIL`: 给用户发送有未读消息邮件

      - `_COMMENT_AND_REPLY`: 评论和回复, 该项是为了在查询历史消息时的方便而拼凑出的,
                              实际上不会存在该类型的消息
      - `_FRIENDS_DYNAMIC`: 朋友动态, 同上.
    '''

    # 用户发给用户的消息
    CHAT_MESSAGE_NEW = 'chat_message_new'
    COMMENT = 'comment'
    REPLY = 'reply'
    LIKE = 'like'
    AT = 'at'
    STATUS_NEW = 'status_new'
    TOPIC_NEW = 'topic_new'
    FRIEND_REQUEST_NEW = 'friend_request_new'
    LEAVE_MESSAGE_NEW = 'leave_message_new'
    SHARE_NEW = 'share_new'

    # 系统自己发给自己的消息, 不会保存到MessageDocument里边
    SEND_ACTIVATION_EMAIL = 'send_activation_email'
    SEND_RESET_PASSWORD_EMAIL = 'send_reset_password_email'
    SEND_HAS_UNREAD_MESSAGE_EMAIL = 'send_has_unread_message_email'

    _COMMENT_AND_REPLY = 'comment_and_reply'
    _FRIENDS_DYNAMIC = 'friends_dynamic'

    all_topic = [
        CHAT_MESSAGE_NEW, COMMENT, REPLY, LIKE, AT, STATUS_NEW, TOPIC_NEW,
        FRIEND_REQUEST_NEW, LEAVE_MESSAGE_NEW, SHARE_NEW, SEND_ACTIVATION_EMAIL,
        SEND_RESET_PASSWORD_EMAIL, SEND_HAS_UNREAD_MESSAGE_EMAIL
    ]

    @classmethod
    def message_type2topic(cls, message_type):
        for topic in cls.all_topic:
            if message_type.startswith(topic):
                return topic

        return None
