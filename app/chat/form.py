# -*- coding: utf-8 -*-

from wtforms_tornado import Form
from wtforms.fields import StringField, FloatField
from wtforms.validators import InputRequired, Length, Regexp

__all__ = ['MessageNewForm', 'MessageUpdateForm', 'MessageHistoryForm']


class MessageNewForm(Form):
    body = StringField(validators=[
        InputRequired(message='消息不能为空！'),
        Length(max=1000, message='消息太长了！')
    ])

    chat_with = StringField(validators=[
        InputRequired(message='请设置交谈对象！'),
        Regexp('^[a-f0-9]{24}$', message='交谈对象错误！')
    ])


class MessageUpdateForm(Form):
    chat_with = StringField(validators=[
        InputRequired(), Regexp('^[a-f0-9]{24}$')
    ])


class MessageHistoryForm(Form):
    chat_with = StringField(validators=[
        InputRequired(), Regexp('^[a-f0-9]{24}$')
    ])
    since = FloatField(validators=[InputRequired()])
