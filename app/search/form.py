# -*- coding: utf-8 -*-

from wtforms.fields import StringField
from wtforms.validators import InputRequired, AnyOf
from wtforms_tornado import Form

__all__ = ['SearchForm']


class SearchForm(Form):
    '''搜索

    :Variables:
      - `category`: 查询的类型
      - `query`: 查询的内容
    '''
    category = StringField(validators=[
        InputRequired(), AnyOf(['user', 'topic', 'share'])
    ])
    query = StringField()
