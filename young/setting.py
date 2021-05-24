# -*- coding: utf-8 -*-

import os

ROOT_LOCATION = os.path.dirname(os.path.dirname(__file__))

APPLICATION_SETTINGS = {
    # NOTE: please use nginx to serve static file in production environment
    'static_path': ROOT_LOCATION + '/static/',
    'login_url': '/login',
    'xsrf_cookies': True,
    # 生成方式 base64.b64encode(str(uuid.uuid5(uuid.NAMESPACE_DNS, str(uuid.uuid4()))))
    'cookie_secret': 'Y2VjMTM4MzYtYWM4MC01Zjc3LWJiYmEtN2MxODQxNmIyMzky',
}

EMAIL_SETTINGS = {
    "host": "localhost",
    "port": 25,
    "robot": "root@mail.beyoung.io",
    'url': 'http://beyoung.io',
}
