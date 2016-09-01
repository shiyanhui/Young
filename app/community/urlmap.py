# -*- coding: utf-8 -*-

from app.community.handler import (
    CommunityHandler, TopicNewHandler,
    TopicCommentNewHandler, TopicCommentMoreHandler, TopicLikeHandler,
    TopicEditHandler, NodeHandler, NodeAvatarSetHandler,
    NodeAvatarEditTemplateHandler, NodeDescriptionEditHandler,
    NodeDescriptionEditTemplateHandler, NodeSuggestionHandler, TopicHandler
)

urlpattern = (
    (r'/?', CommunityHandler),
    (r'/community/?', CommunityHandler),
    (r'/community/topic/new/?', TopicNewHandler),
    (r'/community/topic/([a-f0-9]{24})/?', TopicHandler),
    (r'/community/topic/comment/new/?', TopicCommentNewHandler),
    (r'/community/topic/comment/more/?', TopicCommentMoreHandler),
    (r'/community/topic/like/?', TopicLikeHandler),
    (r'/community/topic/edit/?', TopicEditHandler),
    (r'/community/node/([a-f0-9]{24})/?', NodeHandler),
    (r'/community/node/avatar/edit/template/?', NodeAvatarEditTemplateHandler),
    (r'/community/node/avatar/set/?', NodeAvatarSetHandler),
    (r'/community/node/description/edit/template/?', NodeDescriptionEditTemplateHandler),
    (r'/community/node/description/edit/?', NodeDescriptionEditHandler),
    (r'/community/node/suggestion/?', NodeSuggestionHandler),
)
