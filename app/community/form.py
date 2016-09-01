# -*- coding: utf-8 -*-

from wtforms_tornado import Form
from wtforms.fields import StringField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Regexp, Length, AnyOf

__all__ = ['NodeSuggestionForm', 'TopicNewForm',
           'TopicCommentNewForm', 'TopicCommentMoreForm',
           'TopicLikeForm', 'NodeOneForm',
           'NodeAvatarSetForm', 'NodeDescriptionEditTemplateForm',
           'NodeDescriptionEditForm', 'TopicEditModalForm', 'TopicEditForm']


class NodeSuggestionForm(Form):
    '''
    :Variables:
      - `content`: 搜索的内容
    '''

    q = StringField(validators=[InputRequired()])


class TopicNewForm(Form):
    '''
    :Variables:
      - `title`: 标题
      - `nodes`: 所属的节点
      - `content`: 话题的内容
      - `anonymous`: 是否匿名
    '''

    title = StringField(validators=[
        InputRequired(message="标题不能为空!"),
        Length(max=100, message="标题太长了!")
    ])
    nodes = StringField(validators=[
        InputRequired(message="节点不能为空!")
    ])
    content = StringField(validators=[
        Length(max=10 ** 5, message="内容太长了")
    ])
    anonymous = BooleanField()


class TopicCommentNewForm(Form):
    '''
    :Variables:
      - `topic_id`: 被评论的话题
      - `content`: 回答内容
      - `anonymous`: 是否匿名
    '''

    topic_id = StringField(validators=[
        InputRequired(message='请指定要评论的话题'),
        Regexp('[a-f0-9]{24}', message='要评论的话题不存在')
    ])

    content = StringField(validators=[
        InputRequired(message='评论内容不能为空'),
        Length(max=10 ** 5, message='评论的内容太长了')
    ])

    anonymous = BooleanField()
    replyeder_id = StringField()


class TopicCommentMoreForm(Form):
    '''
    :Variables:
      - `topic_id`: 相关的话题id
      - `page`: 当前页
    '''
    topic_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])
    page = IntegerField(validators=[InputRequired()])


class TopicLikeForm(Form):
    '''
    喜欢某话题

    :Variables:
      - `topic_id`: 相关的话题
    '''

    topic_id = StringField(validators=[
        InputRequired(message='话题不能为空'),
        Regexp('[a-f0-9]{24}', message='话题不存在')
    ])


class NodeOneForm(Form):
    '''
    :Variables:
      - `node_id`: 节点id
      - `sort`: 排序方式
    '''

    sort = StringField(validators=[
        InputRequired(), AnyOf(['time', 'popularity'])
    ])


class NodeAvatarSetForm(Form):
    '''
    :Variables:
      - `node_id`: 节点id
      - `x`: 头像剪裁的起始x坐标
      - `y`: 头像剪裁的起始y坐标
      - `w`: 头像剪裁的宽度
      - `h`: 头像剪裁的高度
      - `target_width`: 浏览器前端对比宽度
    '''
    node_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])
    x = FloatField(validators=[InputRequired()])
    y = FloatField(validators=[InputRequired()])
    w = FloatField(validators=[InputRequired()])
    h = FloatField(validators=[InputRequired()])
    target_width = IntegerField(validators=[InputRequired()])


class NodeDescriptionEditTemplateForm(Form):
    node_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])


class NodeDescriptionEditForm(Form):
    node_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])
    description = StringField(validators=[
        InputRequired(), Length(max=300)
    ])


class TopicEditModalForm(Form):
    topic_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])


class TopicEditForm(Form):
    '''
    :Variables:
      - `topic_id`: 话题id
      - `title`: 标题
      - `nodes`: 所属的节点
      - `content`: 话题的内容
      - `anonymous`: 是否匿名
    '''

    topic_id = StringField(validators=[
        InputRequired(), Regexp('[a-f0-9]{24}')
    ])
    title = StringField(validators=[
        InputRequired(), Length(max=100)
    ])
    nodes = StringField(validators=[InputRequired()])
    content = StringField(validators=[Length(max=10 ** 5)])
    anonymous = BooleanField()
