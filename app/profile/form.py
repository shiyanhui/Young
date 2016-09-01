# -*- coding: utf-8 -*-

from wtforms.fields import IntegerField, StringField, BooleanField
from wtforms.validators import InputRequired, Regexp, Length
from wtforms_tornado import Form

__all__ = ['ProfileCardForm', 'StatusMoreForm',
           'LeaveMessageNewForm', 'LeaveMessageMoreForm', 'FriendRequestForm',
           'LeagueBulletinSaveForm']


class StatusMoreForm(Form):
    '''
    :Variables:
      - `page`: 当前页数
    '''

    page = IntegerField(validators=[InputRequired()])


class LeaveMessageNewForm(Form):
    '''新留言'''

    user_id = StringField(validators=[
        InputRequired(), Regexp('[0-9a-f]{24}')
    ])
    private = BooleanField(validators=[
        InputRequired()
    ])
    content = StringField(validators=[
        InputRequired(), Length(max=5000)
    ])
    replyeder_id = StringField()


class LeaveMessageMoreForm(Form):
    '''陌生人访问界面更多留言'''

    user_id = StringField(validators=[
        InputRequired(), Regexp('[0-9a-f]{24}')
    ])
    page = IntegerField(validators=[InputRequired()])


class ProfileCardForm(Form):
    '''用户名片'''

    user_id = StringField(validators=[
        InputRequired(), Regexp('[0-9a-f]{24}')
    ])


class FriendRequestForm(Form):
    '''添加好友请求'''

    user_id = StringField(validators=[
        InputRequired(), Regexp('[0-9a-f]{24}')
    ])


class LeagueBulletinSaveForm(Form):
    '''修改社团公告'''

    league_bulletin = StringField(validators=[
        Length(max=300)
    ])
