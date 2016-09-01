# -*- coding: utf-8 -*-

from wtforms_tornado import Form
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired, NumberRange

__all__ = ['MessageUpdaterForm']


class MessageUpdaterForm(Form):
    n = IntegerField(validators=[InputRequired(), NumberRange(min=1)])
