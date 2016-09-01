# -*- coding: utf-8 -*-

from wtforms.fields import StringField, IntegerField, BooleanField
from wtforms.validators import InputRequired, NumberRange, Length, Regexp
from wtforms_tornado import Form

__all__ = ['ShareCategoryForm', 'ShareNewForm', 'ShareNewCancelForm',
           'ShareCommentNewForm', 'ShareLikeForm', 'SharePreviewForm']


class ShareCategoryForm(Form):
    category = StringField(validators=[InputRequired()])


class ShareNewForm(Form):
    resumableChunkNumber = IntegerField(validators=[
        InputRequired(), NumberRange(min=1)
    ])
    resumableTotalChunks = IntegerField(validators=[
        InputRequired(), NumberRange(min=1)
    ])
    resumableChunkSize = IntegerField(validators=[
        InputRequired(), NumberRange(min=1)
    ])
    resumableTotalSize = IntegerField(validators=[
        InputRequired(), NumberRange(min=1)
    ])
    resumableIdentifier = StringField(validators=[
        InputRequired()
    ])
    resumableFilename = StringField(validators=[
        InputRequired(), Length(max=500)
    ])
    resumableRelativePath = StringField(validators=[
        InputRequired()
    ])
    upload_token = StringField(validators=[
        InputRequired(), Length(max=100)
    ])
    title = StringField(validators=[
        InputRequired(), Length(max=100)
    ])
    category = StringField(validators=[
        InputRequired()
    ])
    cost = IntegerField(validators=[
        InputRequired(), NumberRange(min=0)
    ])
    description = StringField(validators=[
        Length(max=10 ** 5)
    ])


class ShareNewCancelForm(Form):
    upload_token = StringField(validators=[
        InputRequired(), Length(max=100)
    ])


class ShareCommentNewForm(Form):
    '''
    :Variables:
      - `share_id`: 被评论的分享
      - `content`: 回答内容
      - `anonymous`: 是否匿名
    '''

    share_id = StringField(validators=[
        InputRequired(message='请指定要评论的话题'),
        Regexp('[a-f0-9]{24}', message='要评论的话题不存在')
    ])

    content = StringField(validators=[
        InputRequired(message='评论内容不能为空'),
        Length(max=10 ** 5, message='评论的内容太长了')
    ])

    anonymous = BooleanField()
    replyeder_id = StringField()


class ShareLikeForm(Form):
    '''
    :Variables:
      - `share_id`: 相关的分享
    '''

    share_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])


class SharePreviewForm(Form):
    share_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])
