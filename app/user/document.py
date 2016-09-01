# -*- coding: utf-8 -*-

import hashlib
import random
import base64
from uuid import uuid1
from datetime import datetime, timedelta

import pymongo
from tornado import gen
from bson.dbref import DBRef
from bson.objectid import ObjectId
from monguo import (
    Document, EmbeddedDocument, ReferenceField, DateTimeField,
    StringField, IntegerField, EmailField, ListField,
    EmbeddedDocumentField, BooleanField, DateField, BinaryField,
    ObjectIdField
)

from lib.message.topic import MessageTopic
from app.home.setting import HOME_SETTINGS

__all__ = ['AvatarDocument', 'UserDocument', 'OfficialProfileCoverDocument',
           'UserSettingDocument', 'CodeDocument', 'FriendDocument',
           'LeagueMemberDocument', 'WealthRecordDocument',
           'UserActivityDocument']


class OfficialProfileCoverDocument(Document):
    '''官方提供的个人封面.

    :Variables:
      - `image`: 注意: 里边是ImageDocument, 因为出现了循环引用, 因此没写
    '''

    image = ReferenceField(required=True)

    meta = {
        'collection': 'user_official_profile_cover'
    }

    @gen.coroutine
    def get_profile_cover_list(skip=0, limit=None):
        from app.base.document import ImageDocument

        cursor = OfficialProfileCoverDocument.find().skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)

        profile_cover_list = yield OfficialProfileCoverDocument.to_list(
            cursor
        )

        for item in profile_cover_list:
            url = yield ImageDocument.generate_image_url(item['image'].id)
            thumbnail = yield ImageDocument.generate_image_url(
                item['image'].id,
                thumbnail=True
            )

            item['photo'] = {
                'url': url,
                'thumbnail': thumbnail
            }

        raise gen.Return(profile_cover_list)


class ForbiddenLoginInfoEmbeddedDocument(EmbeddedDocument):
    '''禁止登陆的相关信息

    :Variables:
      - `time`: 禁止登陆的时间
      - `reason`: 禁止登陆原因
    '''

    time = DateTimeField(required=True)
    reason = StringField(required=True, max_length=100)


class UserDocument(Document):
    '''用户

    :Variables:
      - `email`: 邮箱
      - `password`: 密码
      - `name`: 名称
      - `register_date`: 注册日期
      - `user_type`: 用户类型
      - `activated`: 账号是否已经激活
      - `sex`: 性别
      - `avatar_updated`: 头像是否更新
      - `wealth`: 金币的个数
      - `continuous_login_days`: 现在连续登录的天数

      - `forbidden_login`: 是否禁止登陆
      - `forbidden_login_info`: 禁止登陆的相关信息

      - `relationship_status`: 感情状况
      - `birthday`: 生日
      - `home`: 家乡, 格式: 省份-城市
      - `qq`: QQ
      - `wechat`: 微信
      - `phone`: 手机号码
      - `signature`: 签名
      - `league_bulletin`: 如果是社团, 社团公告
    '''
    email = EmailField(required=True, unique=True)
    password = StringField(required=True, min_length=6)
    name = StringField(required=True)
    register_date = DateTimeField(required=True)
    user_type = StringField(required=True, candidate=['person', 'league'])
    activated = BooleanField(required=True, default=False)
    sex = StringField(
        required=True, candidate=['male', 'female'], default='male'
    )
    avatar_updated = BooleanField(required=True, default=False)
    wealth = IntegerField(required=True, default=100)
    continuous_login_days = IntegerField(required=True, default=0)

    forbidden_login = BooleanField(required=True, default=False)
    forbidden_login_info = ListField(
        EmbeddedDocumentField(ForbiddenLoginInfoEmbeddedDocument)
    )

    relationship_status = StringField(candidate=['', 'single', 'in_love'])
    birthday = DateField()
    home = StringField(max_length=100)
    qq = StringField(max_length=30)
    wechat = StringField(max_length=30)
    phone = StringField(max_length=30)
    signature = StringField(max_length=100)
    league_bulletin = StringField(max_length=300)

    meta = {
        'collection': 'user'
    }

    def get_user_sync(user_id):
        return UserDocument.get_collection(pymongo=True).find_one({
            '_id': ObjectId(user_id)
        })

    @gen.coroutine
    def get_user_list(skip=0, limit=51):
        cursor = UserDocument.find().sort(
            [('register_date', pymongo.DESCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        user_list = yield UserDocument.to_list(cursor)
        raise gen.Return(user_list)

    @gen.coroutine
    def get_avatared_user_list(skip=0, limit=48):
        '''得到头像改变的人的列表'''

        cursor = UserDocument.find({
            'avatar_updated': True, 'user_type': {'$ne': 'league'}
        }).sort([('register_date', pymongo.DESCENDING)]).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        user_list = yield UserDocument.to_list(cursor)

        raise gen.Return(user_list)

    @gen.coroutine
    def get_random_user_list(user_id, size=4):
        '''得到随机推荐的size个用户.

        :Parameters:
          - `user_id`: 为谁推荐?
          - `size`: 推荐数量
        '''

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise gen.Return([])

        friend_list = yield FriendDocument.get_friend_list(user['_id'])
        friend_objectid_list = [user['_id']] + [
            friend['_id'] for friend in friend_list
        ]

        query = {
            '_id': {'$nin': friend_objectid_list},
            'activated': True
        }
        cursor = UserDocument.find(query)

        count = yield UserDocument.find(query).count()
        if count > size:
            cursor = cursor.skip(random.randint(0, count - size))

        cursor = cursor.limit(size)
        user_list = yield UserDocument.to_list(cursor)

        raise gen.Return(user_list)

    @gen.coroutine
    def get_recommend_friends(user_id, size=5):
        '''得到推荐的朋友

        :Parameters:
          - `user_id`: 为谁推荐?
          - `size`: 推荐数量
        '''
        from app.message.document import MessageDocument

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise gen.Return([])

        friend_list = yield FriendDocument.get_friend_list(user['_id'])
        friend_objectid_list = [user['_id']] + [
            friend['_id'] for friend in friend_list
        ]

        cursor = MessageDocument.find({
            'sender': DBRef(
                UserDocument.meta['collection'],
                ObjectId(user_id)
            ),
            'message_type': MessageTopic.FRIEND_REQUEST_NEW
        })

        message_list = yield MessageDocument.to_list(cursor)
        for message in message_list:
            friend_objectid_list.append(
                ObjectId(message['recipient'].id)
            )

        query = {
            '_id': {'$nin': friend_objectid_list},
            'activated': True,
            'avatar_updated': True
        }

        cursor = UserDocument.find(query)

        count = yield UserDocument.find(query).count()
        if count > size:
            cursor = cursor.skip(random.randint(0, count - size))

        cursor = cursor.limit(size)
        user_list = yield UserDocument.to_list(cursor)

        raise gen.Return(user_list)

    @gen.coroutine
    def encrypt_password(password):
        '''加密密码'''
        raise gen.Return(hashlib.new('md5', password).hexdigest())

    @gen.coroutine
    def can_seen(user_id, visitor_id):
        '''visitor能否访问user的个人主页'''

        is_friend = yield FriendDocument.is_friend(user_id, visitor_id)
        user_setting = yield UserSettingDocument.get_user_setting(user_id)

        can_seen = (
            is_friend or
            str(user_id) == str(visitor_id) or
            (user_setting and user_setting["allow_stranger_visiting_profile"])
        )

        raise gen.Return(can_seen)

    @gen.coroutine
    def update_wealth(user_id, quantity):
        yield UserDocument.update(
            {'_id': ObjectId(user_id)},
            {'$inc': {'wealth': quantity}}
        )

        raise gen.Return()

    @gen.coroutine
    def get_continuous_login_days(user_id):
        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if not user:
            raise gen.Return(0)

        yesterday = datetime.now() - timedelta(days=1)
        login_reward_fetched = UserActivityDocument.login_reward_fetched(
            user_id, day=yesterday
        )

        if login_reward_fetched:
            raise gen.Return(user['continuous_login_days'])

        yield UserDocument.update(
            {'_id': ObjectId(user_id)},
            {'$set': {'continuous_login_days': 0}}
        )

        raise gen.Return(0)

    @gen.coroutine
    def can_afford(user_id, quantity):
        '''某人是否能够支出quantity金币'''

        user = yield UserDocument.find_one({'_id': ObjectId(user_id)})
        if user:
            raise gen.Return(user['wealth'] >= quantity)

        raise gen.Return(False)


class ImageCropAreaDocument(EmbeddedDocument):
    '''图片被剪切的图片区域.

    :Variables:
      - `x`: 左上角x坐标
      - `y`: 左上角y坐标
      - `w`: 宽度
      - `h`: 高度
      - `target_width`: 显示图片的宽度，以便计算放缩比例
    '''

    x = IntegerField(required=True)
    y = IntegerField(required=True)
    w = IntegerField(required=True)
    h = IntegerField(required=True)
    target_width = IntegerField(required=True)


class AvatarDocument(Document):
    '''头像

    :Variables:
      - `owner`: 所有者
      - `name`: 图片名称
      - `content`: 完整头像内容
      - `content_type`: 图片类型
      - `upload_time`: 上传时间
      - `thumbnail50x50`: 略缩图50x50
      - `thumbnail180x180`: 略缩图180x180
      - `crop_area`: 头像裁剪区域
    '''
    owner = ReferenceField(UserDocument, required=True)
    name = StringField(required=True)
    content = BinaryField(required=True)
    content_type = StringField(required=True)
    upload_time = DateTimeField(required=True)
    thumbnail50x50 = BinaryField(required=True)
    thumbnail180x180 = BinaryField(required=True)
    crop_area = EmbeddedDocumentField(ImageCropAreaDocument)

    meta = {
        'collection': 'user_avatar'
    }


class UserSettingDocument(Document):
    '''用户的设置

    :Variables:
      - `user`: 用户
      - `profile_cover`: 个人封面
      - `require_verify_when_add_friend`: 加我为朋友时是否需要验证
      - `allow_stranger_visiting_profile`: 是否允许陌生人查看个人主页
      - `allow_stranger_chat_with_me`: 是否允许陌生人和我聊天
      - `enable_leaving_message`: 是否允许留言
      - `email_notify_when_offline`: 当离线有新的消息时发邮件通知
      - `theme`: 主题
    '''

    user = ReferenceField(UserDocument, required=True)
    profile_cover = ReferenceField(required=True)
    require_verify_when_add_friend = BooleanField(required=True, default=True)
    allow_stranger_visiting_profile = BooleanField(required=True, default=False)
    allow_stranger_chat_with_me = BooleanField(required=True, default=False)
    enable_leaving_message = BooleanField(required=True, default=True)
    email_notify_when_offline = BooleanField(required=True, default=True)
    theme = StringField(required=True, default='default')

    meta = {
        'collection': 'user_setting'
    }

    def get_user_setting_sync(user_id):
        return UserSettingDocument.get_collection(True).find_one({
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })

    @gen.coroutine
    def get_user_setting(user_id):
        user_setting = yield UserSettingDocument.find_one({
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        })

        raise gen.Return(user_setting)

    @gen.coroutine
    def get_profile_cover(user_id):
        '''得到用户profile_cover图片地址'''

        from app.base.document import ImageDocument

        user_setting = yield UserSettingDocument.get_user_setting(user_id)
        if not (user_setting and
                'profile_cover' in user_setting and
                user_setting['profile_cover']):
            raise gen.Return("")

        cover = user_setting['profile_cover']
        if cover.collection == OfficialProfileCoverDocument.meta['collection']:
            cover = yield OfficialProfileCoverDocument.translate_dbref(cover)
            url = yield ImageDocument.generate_image_url(
                cover['image'].id
            )
        else:
            url = yield ImageDocument.generate_image_url(
                cover.id, thumbnail=True
            )

        raise gen.Return(url)

    @gen.coroutine
    def set_profile_cover(user_id, cover):
        '''设置用户的个人封面'''

        from app.base.document import ImageDocument

        assert isinstance(cover, DBRef)

        uploader = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        user_setting = yield UserSettingDocument.get_user_setting(user_id)
        if (user_setting and 'profile_cover' in user_setting and
                user_setting['profile_cover'] and
                user_setting[
                    'profile_cover'
                ].collection == ImageDocument.meta['collection']):
            yield ImageDocument.remove({
                '_id': ObjectId(user_setting['profile_cover'].id)
            })

        yield UserSettingDocument.update(
            {'user': uploader},
            {'$set': {'profile_cover': cover}}
        )

        raise gen.Return()


class FriendDocument(Document):
    '''朋友

    :Variables:
      - `owner`: 谁的朋友?
      - `friend`: 朋友
      - `be_time`: 成为朋友的时间
      - `shielded`: 该朋友是否被屏蔽, 被屏蔽后, 用户将收不到其朋友的动态
      - `blocked`: 该朋友是否被拉黑, 被拉黑后, 朋友将收不到该用户的动态
    '''

    owner = ReferenceField(UserDocument, required=True)
    friend = ReferenceField(UserDocument, required=True)
    be_time = DateTimeField(required=True)
    shielded = BooleanField(required=True, default=False)
    blocked = BooleanField(required=True, default=False)

    meta = {
        'collection': 'user_friend'
    }

    @gen.coroutine
    def _gen_friend_list(friends, role):
        assert role in ["owner", "friend"]

        friend_list = []

        for friend in friends:
            friend[role] = yield UserDocument.translate_dbref(friend[role])
            friend[role].update({
                'shielded': friend['shielded'],
                'blocked': friend['blocked']
            })
            friend_list.append(friend[role])

        raise gen.Return(friend_list)

    @gen.coroutine
    def get_friend_list(user_id, skip=0, limit=None):
        '''得到某一个人的朋友列表

        :Parameters:
          - `user_id`: 相关用户
        '''

        owner = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        cursor = FriendDocument.find({'owner': owner}).sort(
            [('be_time', pymongo.DESCENDING)]
        ).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        friends = yield FriendDocument.to_list(cursor)
        friend_list = yield FriendDocument._gen_friend_list(
            friends, "friend"
        )

        raise gen.Return(friend_list)

    @gen.coroutine
    def get_shielded_friends(user_id, skip=0, limit=None):
        '''得到我将对方屏蔽的好友'''

        owner = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
        cursor = FriendDocument.find({
            'owner': owner, 'shielded': True
        }).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        friends = yield FriendDocument.to_list(cursor)
        friend_list = yield FriendDocument._gen_friend_list(
            friends, "friend"
        )

        raise gen.Return(friend_list)

    @gen.coroutine
    def get_blocked_friends(user_id, skip=0, limit=None):
        '''得到对方将我拉黑的朋友'''

        friend = DBRef(
            UserDocument.meta['collection'],
            ObjectId(user_id)
        )
        cursor = FriendDocument.find({
            'friend': friend, 'blocked': True
        }).skip(skip)

        if limit is not None:
            cursor = cursor.limit(limit)

        friends = yield FriendDocument.to_list(cursor)
        friend_list = yield FriendDocument._gen_friend_list(
            friends, "owner"
        )

        raise gen.Return(friend_list)

    @gen.coroutine
    def get_reached_friends(user_id, skip=0, limit=None):
        '''我既没将对方屏蔽, 对方也没将我拉黑的朋友'''

        friend_list = yield FriendDocument.get_friend_list(user_id)
        shielded_friends = yield FriendDocument.get_shielded_friends(user_id)
        blocked_friends = yield FriendDocument.get_blocked_friends(user_id)

        shielded_friends_id = set([
            friend['_id'] for friend in shielded_friends
        ])
        blocked_friends_id = set([
            friend['_id'] for friend in blocked_friends
        ])

        friends = []
        for friend in friend_list:
            if (friend['_id'] not in shielded_friends_id and
                    friend['_id'] not in blocked_friends_id):
                friends.append(friend)

        raise gen.Return(friends)

    def get_reached_friends_sync(user_id, skip=0, limit=None):
        user = DBRef(UserDocument.meta['collection'], ObjectId(user_id))

        cursor = FriendDocument.get_collection(True).find({
            'owner': user, 'shielded': False, 'blocked': False
        })
        friend_list = set(item['friend'] for item in cursor)

        cursor = FriendDocument.get_collection(True).find({
            'friend': user, 'shielded': False, 'blocked': False
        })
        for item in cursor:
            friend_list.add(item['owner'])

        return list(friend_list)

    @gen.coroutine
    def get_same_friends(user_a, user_b):
        '''得到user_a和user_b的共同好友.

        :Parameters:
          - `user_a`: 用户a(id)
          - `user_b`: 用户b(id)
        '''

        @gen.coroutine
        def get_friends(user_id):
            owner = DBRef(UserDocument.meta['collection'], ObjectId(user_id))
            cursor = FriendDocument.find({'owner': owner})

            friends = yield FriendDocument.to_list(cursor)
            friends = {friend['friend'] for friend in friends}

            raise gen.Return(friends)

        friends_a = yield get_friends(user_a)
        friends_b = yield get_friends(user_b)

        same_friends = [
            (yield UserDocument.translate_dbref(friend))
            for friend in friends_a.intersection(friends_b)
        ]

        raise gen.Return(same_friends)

    @gen.coroutine
    def get_same_friend_ids(user_a, user_b):
        same_friends = yield FriendDocument.get_same_friends(user_a, user_b)
        raise gen.Return([friend["_id"] for friend in same_friends])

    @gen.coroutine
    def is_friend(user_a, user_b):
        '''判断user_a和user_b是否是好友.

        :Parameters:
          - `user_a`: 用户a(id)
          - `user_b`: 用户b(id)
        '''

        a = DBRef(UserDocument.meta['collection'], ObjectId(user_a))
        b = DBRef(UserDocument.meta['collection'], ObjectId(user_b))

        friend = yield FriendDocument.find_one({
            '$or': [{'owner': a, 'friend': b}, {'owner': b, 'friend': a}]
        })

        raise gen.Return(True if friend else False)

    def is_friend_sync(user_a, user_b):
        '''判断user_a和user_b的是否是好友.

        :Parameters:
          - `user_a`: 用户a(id)
          - `user_b`: 用户b(id)
        '''

        a = DBRef(UserDocument.meta['collection'], ObjectId(user_a))
        b = DBRef(UserDocument.meta['collection'], ObjectId(user_b))

        friend = FriendDocument.get_collection(True).find_one({
            '$or': [{'owner': a, 'friend': b}, {'owner': b, 'friend': a}]
        })

        return True if friend else False

    @gen.coroutine
    def add_friend(user_a, user_b):
        '''添加一对朋友'''

        now = datetime.now()

        user_a_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(user_a)
        )
        user_b_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(user_b)
        )

        yield FriendDocument.insert({
            'owner': user_a_dbref,
            'friend': user_b_dbref,
            'be_time': now
        })

        yield FriendDocument.insert({
            'owner': user_b_dbref,
            'friend': user_a_dbref,
            'be_time': now
        })

        raise gen.Return()

    @gen.coroutine
    def delete_friend(user_a, user_b):
        '''删除一对朋友'''

        user_a_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(user_a)
        )
        user_b_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(user_b)
        )

        yield FriendDocument.remove({
            '$or': [
                {'owner': user_a_dbref, 'friend': user_b_dbref},
                {'owner': user_b_dbref, 'friend': user_a_dbref}
            ]
        })

        raise gen.Return()


class LeagueMemberDocument(Document):
    '''社团成员.

    :Parameters:
      - `league`: 社团
      - `member`: 社团成员
      - `join_time`: 将该成员添加到该社团中的时间
    '''

    league = ReferenceField(UserDocument, required=True)
    member = ReferenceField(UserDocument, required=True)
    time = DateTimeField(required=True)

    meta = {
        'collection': 'user_league_member'
    }

    @gen.coroutine
    def get_member(league_id, skip=0, limit=9):
        '''得到某个社团的成员'''

        cursor = LeagueMemberDocument.find({
            'league': DBRef(
                UserDocument.meta['collection'],
                ObjectId(league_id)
            )
        }).sort([('time', pymongo.DESCENDING)]).skip(skip).limit(limit)

        member_list = yield LeagueMemberDocument.to_list(cursor)
        for member in member_list:
            member['member'] = yield LeagueMemberDocument.translate_dbref(
                member['member']
            )

        raise gen.Return(member_list)

    @gen.coroutine
    def get_member_num(league_id):
        '''得到某社团成员数量'''

        cursor = LeagueMemberDocument.find({
            'league': DBRef(
                UserDocument.meta['collection'],
                ObjectId(league_id)
            )
        })
        result = yield cursor.count()

        raise gen.Return(result)

    @gen.coroutine
    def get_member_page_size(league_id):
        member_num = yield LeagueMemberDocument.find({
            'league': DBRef(
                UserDocument.meta['collection'],
                ObjectId(league_id)
            )
        }).count()

        result = member_num / HOME_SETTINGS['league_member_num_per_page']
        if member_num % HOME_SETTINGS['league_member_num_per_page']:
            result += 1

        raise gen.Return(result)


class CodeDocument(Document):
    '''激活码或者是重设密码码.

    :Variables:
      - `uid`: user id
      - `code`: 激活码, 生成规则base64.64encode(str(uuid1()))
      - `expired_time`: 到期时间
    '''

    uid = ObjectIdField(required=True)
    code = StringField(required=True, unique=True)
    expired_time = DateTimeField(required=True)

    meta = {
        'collection': 'user_code'
    }

    @classmethod
    def generate_code(cls):
        return base64.b64encode(str(uuid1()))


class UserActivityDocument(Document):
    '''用户的活动

    :Variables:
      - `user`: 用户
      - `activity_type`: 活动类型
      - `time`: 时间
      - `relevant`: 相关者
      - `data`: 有关的数据
    '''

    VISIT = 'visit'
    COMMENT = 'comment'
    REPLY = 'reply'
    LIKE = 'like'
    DOWNLOAD_SHARE = 'download_share'
    FETCH_LOGIN_REWARD = 'fetch_login_reward'

    STATUS_NEW = 'status_new'
    TOPIC_NEW = 'topic_new'
    SHARE_NEW = 'share_new'
    FRIEND_REQUEST_NEW = 'friend_request_new'
    LEAVE_MESSAGE_NEW = 'leave_message_new'

    user = ReferenceField(UserDocument, required=True)
    activity_type = StringField(required=True)
    time = DateTimeField(required=True)
    relevant = ReferenceField(UserDocument)
    data = ReferenceField()

    meta = {
        'collection': 'user_activity'
    }

    @gen.coroutine
    def login_reward_fetched(user_id, day=None):
        '''判断某一天是否领取了登陆奖励'''

        if day is None:
            day = datetime.now()

        today = datetime(year=day.year, month=day.month, day=day.day)
        tomorrow = today + timedelta(days=1)

        activity = yield UserActivityDocument.find_one({
            'user': DBRef(UserDocument.meta['collection'], ObjectId(user_id)),
            'activity_type': UserActivityDocument.FETCH_LOGIN_REWARD,
            'time': {'$gte': today, '$lt': tomorrow}
        })

        raise gen.Return(True if activity else False)


class WealthRecordDocument(Document):
    '''用户财富记录

    :Variables:
      - `user`: 相关的用户
      - `in_out_type`: 支出还是收入
      - `activity`: 相关的活动
      - `quantity`: 支出或者收入数量
      - `time`: 时间
    '''

    IN = 'in'
    OUT = 'out'

    user = ReferenceField(UserDocument, required=True)
    in_out_type = StringField(required=True, candidate=[IN, OUT])
    activity = ReferenceField(UserActivityDocument, required=True)
    quantity = IntegerField(required=True)
    time = DateTimeField(required=True)

    meta = {
        'collection': 'user_wealth_record'
    }
