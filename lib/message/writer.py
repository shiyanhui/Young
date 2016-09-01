# -*- coding: utf-8 -*-

__all__ = ['WriterManager']


class WriterManager(object):
    writer = None

    @classmethod
    def pub(cls, topic, msg, callback=None):
        cls.writer.pub(topic, str(msg), callback)

    @classmethod
    def mpub(cls, topic, msg, callback=None):
        cls.writer.mpub(topic, map(str, msg), callback)
