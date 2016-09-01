# -*- coding: utf-8 -*-

from wtforms.fields import StringField
from wtforms.validators import InputRequired, Regexp
from wtforms_tornado import Form

__all__ = ['LoginForm', 'RegisterForm', 'ServerTicketForm',
           'AccountActiveForm', 'PasswordResetSendmailForm',
           'PasswordResetGetForm', 'PasswordResetPostForm',
           'AccountActiveSendmailForm']

email_regex = (
    '^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|'
    '(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|'
    '(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
)

password_regex = '''[-\da-zA-Z`=\\\[\];',./~!@#$%^&*()_+|{}:"<>?]{6,20}'''


class LoginForm(Form):
    '''
    :Variables:
      - `email`: 邮箱
      - `password`: 密码
    '''

    email = StringField(validators=[
        InputRequired(message='请输入邮箱')
    ])
    password = StringField(validators=[
        InputRequired(message='请输入密码')
    ])


class RegisterForm(Form):
    name = StringField(validators=[
        InputRequired(message='请填写用户名!'),
        Regexp('^[0-9A-Za-z]{1,30}$', message='用户名格式不正确! 用户名必须为'
               '字母或数字, 且长度不超过30')
    ])
    email = StringField(validators=[
        InputRequired(message='请填写你的邮箱!'),
        Regexp(email_regex, message='邮箱格式不正确!')
    ])

    password = StringField(
        validators=[
            InputRequired(message='请输入密码!'),
            Regexp(password_regex, message='密码格式不正确! 密码必须为长度至'
                   '少为6的字母、数字或者非空白字符的组合!')
        ]
    )


class ServerTicketForm(Form):
    ticket = StringField(validators=[
        InputRequired()
    ])


class AccountActiveSendmailForm(Form):
    email = StringField(validators=[
        InputRequired(), Regexp(email_regex)
    ])


class AccountActiveForm(Form):
    uid = StringField(validators=[
        InputRequired()
    ])
    code = StringField(validators=[
        InputRequired()
    ])


class PasswordResetSendmailForm(Form):
    email = StringField(validators=[
        InputRequired(), Regexp(email_regex)
    ])


class PasswordResetGetForm(Form):
    uid = StringField(validators=[
        InputRequired(), Regexp(email_regex)
    ])
    code = StringField(validators=[
        InputRequired()
    ])


class PasswordResetPostForm(Form):
    password = StringField(validators=[
        InputRequired(), Regexp(password_regex)
    ])
