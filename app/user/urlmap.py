# -*- coding: utf-8 -*-

from handler import (
    LoginHandler, LogoutHandler, AvatarStaticFileHandler,
    RegisterTemplateHandler, RegisterHandler, AccountActiveSendmailHandler,
    AccountActiveHandler, PasswordResetSendmailHandler, PasswordResetHandler,
    FetchLoginRewardHandler
)

urlpattern = (
    (r'/login/?', LoginHandler),
    (r'/logout/?', LogoutHandler),
    (r'/avatar/([a-f0-9]{24})/?(thumbnail50x50|thumbnail180x180)?', AvatarStaticFileHandler),
    (r'/register/template/?', RegisterTemplateHandler),
    (r'/register/?', RegisterHandler),
    (r'/account/active/sendmail/?', AccountActiveSendmailHandler),
    (r'/account/active/?', AccountActiveHandler),
    (r'/password/reset/sendmail/?', PasswordResetSendmailHandler),
    (r'/password/reset/?', PasswordResetHandler),
    (r'/reward/login/fetch/?', FetchLoginRewardHandler),
)
