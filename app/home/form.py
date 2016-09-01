# -*- coding: utf-8 -*-

from wtforms.fields import IntegerField, StringField
from wtforms.validators import InputRequired, Length, AnyOf, Regexp
from wtforms_tornado import Form

from lib.message import MessageTopic


__all__ = ['StatusMoreForm', 'StatusNewForm', 'StatusCommentsForm',
           'StatusCommentNewForm', 'FriendActionForm',
           'StatusLikeForm', 'MessageForm', 'MessageMoreForm']


class StatusMoreForm(Form):
    '''
    :Variables:
      - `page`: 当前页数
    '''

    page = IntegerField(validators=[InputRequired()])


class StatusNewForm(Form):
    '''
    :Variables:
      - `content`: 内容
    '''

    content = StringField(validators=[
        Length(max=1000, message='状态内容不能超过140字!')
    ])


class StatusCommentsForm(Form):
    '''
    :Variables:
      - `status_id`: 状态id
    '''

    status_id = StringField(validators=[
        InputRequired(message='请指定状态'),
        Regexp('[0-9a-f]{24}', message='状态不存在')
    ])


class StatusCommentNewForm(Form):
    '''
    :Variables:
      - `status_id`: 状态id
      - `content`: 内容
    '''

    status_id = StringField(validators=[
        InputRequired(message='请指定状态'),
        Regexp('[0-9a-f]{24}', message='状态不存在')
    ])

    content = StringField(validators=[
        InputRequired(message='评论内容不能为空'),
        Length(max=200, message="评论内容不能操作200字!")
    ])

    replyeder_id = StringField()


class StatusLikeForm(Form):
    status_id = StringField(validators=[
        InputRequired(),
        Regexp('[a-f0-9]{24}')
    ])


class FriendActionForm(Form):
    friend_id = StringField(validators=[
        InputRequired(message='朋友不存在'),
        Regexp('[0-9a-f]{24}', message='朋友不存在')
    ])


class MessageForm(Form):
    category = StringField(validators=[
        InputRequired(),
        AnyOf([
            MessageTopic._FRIENDS_DYNAMIC,
            MessageTopic._COMMENT_AND_REPLY,
            MessageTopic.LIKE,
            MessageTopic.AT,
            MessageTopic.CHAT_MESSAGE_NEW,
            MessageTopic.FRIEND_REQUEST_NEW
        ])
    ])


class MessageMoreForm(Form):
    '''
    :Variables:
      - `page`: 当前页数
      - `category`: 消息种类
    '''

    page = IntegerField(validators=[InputRequired()])
    category = StringField(validators=[
        InputRequired(),
        AnyOf([
            MessageTopic._FRIENDS_DYNAMIC,
            MessageTopic._COMMENT_AND_REPLY,
            MessageTopic.LIKE,
            MessageTopic.AT,
            MessageTopic.CHAT_MESSAGE_NEW,
            MessageTopic.FRIEND_REQUEST_NEW
        ])
    ])
