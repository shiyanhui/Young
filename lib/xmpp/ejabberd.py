# -*- coding: utf-8 -*-

import commands

__all__ = ['Ejabberd']


class Ejabberd(object):
    @classmethod
    def registered(cls, user, host='localhost'):
        '''
        :Parm:
            - `user`: @前面的部分
            - `host`: @后面的部分
        '''
        status, output = commands.getstatusoutput(
            'ejabberdctl registered_users %s' % host)

        if status == 0:
            return str(user) in output.split('\n')

        raise Exception(output)

    @classmethod
    def register(cls, user, password, host='localhost'):
        '''
        :Parm:
            - `user`: @前面的部分
            - `host`: @后面的部分
            - `password`: 密码
        '''
        status, output = commands.getstatusoutput(
            'ejabberdctl register %s %s %s' % (user, host, password))

        if status != 0:
            raise Exception(output)

    @classmethod
    def unregister(cls, user, host='localhost'):
        '''
        :Parm:
            - `user`: @前面的部分
            - `host`: @后面的部分
        '''
        status, output = commands.getstatusoutput(
            'ejabberdctl unregister %s %s' % (user, host))

        if status != 0:
            raise Exception(output)
