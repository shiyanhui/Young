# -*- coding: utf-8 -*-

from wtforms.fields import FloatField, BooleanField, StringField, IntegerField
from wtforms.validators import InputRequired, AnyOf, Length, Regexp
from wtforms_tornado import Form

__all__ = ['AvatarSetForm', 'ProfileSetForm',
           'PasswordSetForm', 'ProfileCoverSetForm', 'PrivateSetForm',
           'NotificationSetForm', 'ThemeSetForm']


class AvatarSetForm(Form):
    '''
    :Variables:
      - `x`: 头像剪裁的起始x坐标
      - `y`: 头像剪裁的起始y坐标
      - `w`: 头像剪裁的宽度
      - `h`: 头像剪裁的高度
      - `target_width`: 浏览器前端对比宽度
    '''
    x = FloatField(validators=[InputRequired()])
    y = FloatField(validators=[InputRequired()])
    w = FloatField(validators=[InputRequired()])
    h = FloatField(validators=[InputRequired()])
    target_width = IntegerField(validators=[InputRequired()])


class ProfileSetForm(Form):
    sex = StringField(validators=[
        AnyOf(['', 'male', 'female'])
    ])
    birthday = StringField(validators=[
        Regexp('|\d{4}-\d{1,2}-\d{1,2}')
    ])
    relationship_status = StringField(validators=[
        AnyOf(['', 'single', 'in_love'])
    ])
    province = StringField()
    city = StringField()
    phone = StringField()
    qq = StringField()
    signature = StringField()


class PasswordSetForm(Form):
    current_password = StringField(validators=[
        InputRequired(message='请输入当前密码!')
    ])

    new_password = StringField(validators=[
        InputRequired(message='请输入新密码!'),
        Regexp(r'[-\da-zA-Z`=\\\[\];\',\./~!@#$%^&*()_+|{}:"<>?]{6,20}',
               message='新密码格式不正确!')
    ])

    repeat_password = StringField(validators=[
        InputRequired(message='请重复输入新密码!')
    ])


class ProfileCoverSetForm(Form):
    profile_cover_id = StringField(validators=[
        InputRequired(), Regexp('[0-9a-f]{24}')
    ])


class PrivateSetForm(Form):
    require_verify_when_add_friend = BooleanField(validators=[
        InputRequired()
    ])
    allow_stranger_visiting_profile = BooleanField(validators=[
        InputRequired()
    ])
    allow_stranger_chat_with_me = BooleanField(validators=[
        InputRequired()
    ])
    enable_leaving_message = BooleanField(validators=[
        InputRequired()
    ])


class NotificationSetForm(Form):
    email_notify_when_offline = BooleanField(validators=[
        InputRequired()
    ])


class ThemeSetForm(Form):
    theme = StringField(validators=[
        InputRequired(), AnyOf(['default', 'black'])
    ])
