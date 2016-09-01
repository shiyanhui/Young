# -*- coding: utf-8 -*-

import os
from datetime import datetime

import pymongo
import simplejson as json
from tornado import gen
from tornado.web import authenticated, HTTPError
from bson.dbref import DBRef
from bson.objectid import ObjectId
from bson.binary import Binary

from lib.message import WriterManager
from young.handler import BaseHandler
from young.setting import ROOT_LOCATION
from app.share.setting import SHARE_SETTINGS
from app.base.setting import WEALTH_SETTINGS
from app.base.document import TemporaryFileDocument
from app.message.document import MessageDocument, MessageTopic
from app.user.document import (
    UserDocument, UserActivityDocument, WealthRecordDocument
)
from app.share.document import (
    ShareCategoryDocument, ShareDocument,
    ShareLikeDocument, ShareCommentDocument, ShareDownloadDocument
)
from app.share.form import (
    ShareCategoryForm, ShareNewForm, ShareNewCancelForm,
    ShareCommentNewForm, ShareLikeForm
)

__all__ = ['ShareHandler', 'ShareNewTemplateHandler', 'ShareNewHandler',
           'ShareNewCancelHandler', 'ShareCategoryHandler', 'ShareOneHandler',
           'ShareDownloadHandler', 'ShareCommentNewHandler', 'ShareLikeHandler']


class ShareBaseHandler(BaseHandler):
    UNKNOWN = -1
    AUDIO = 0
    VIDEO = 1
    IMAGE = 2
    PDF = 3
    DOC = 4
    PPT = 5
    CODE = 6
    TEXT = 7

    @classmethod
    def get_extension(cls, share):
        return os.path.splitext(share['filename'])[1].lower()

    @classmethod
    def get_content_type(cls, share):
        return share['content_type']

    @classmethod
    def get_file_type(cls, share):
        extension = cls.get_extension(share)
        content_type = cls.get_content_type(share)

        if extension in [
                '.mp3', '.wma', '.wav', '.ape', '.ogg', '.flac',
                '.pcm', '.aac']:
            return cls.AUDIO

        if extension in [
                '.mp4', '.rmvb', '.rm', '.ra', '.mov', '.avi',
                '.wmv', '.3gp', '.mkv', '.flv', '.mpg', '.mpeg']:
            return cls.VIDEO

        if (extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp'] or
                content_type.startswith('image/')):
            return cls.IMAGE

        if extension in ['.pdf']:
            return cls.PDF

        if extension in ['.doc', '.docx']:
            return cls.DOC

        if extension in ['.ppt', '.pptx']:
            return cls.PPT

        if extension in set([
                '.as', '.scpt', '.asp', '.aspx', '.c', '.cs', '.cpp',
                '.clj', '.css', '.D', '.erl', '.go', '.groovy', '.hs',
                '.htm', '.html', '.java', '.js', '.lsp', '.lua', '.mat',
                '.m', '.ml', '.p', '.pl', '.php', '.py', '.R', '.rb',
                '.scala', '.sh', '.sql', '.xml']):
            return cls.CODE

        if content_type.startswith('text/plain'):
            return cls.TEXT

        return cls.UNKNOWN

    @classmethod
    def get_filename(cls, share, upper=False):
        filename = share['title']

        file_type = cls.get_file_type(share)
        if file_type == cls.TEXT:
            extension = '.txt'
        else:
            extension = cls.get_extension(share)

        if extension:
            if upper:
                extension = extension.upper()

            filename += extension

        return filename

    @classmethod
    def get_icon_name(cls, share):
        '''根据content_type得到文件后缀'''

        extension = cls.get_extension(share)
        if not extension:
            return 'readme'

        extension = extension[1:]
        root = os.path.join(ROOT_LOCATION, "static/app/share/img/icons")

        if not os.path.exists(os.path.join(root, "%s.png" % extension)):
            if extension in [
                    'rmvb', 'rm', 'mp4'] or extension.startswith('video'):
                extension = 'mov'

            elif extension.startswith('text'):
                extension = 'text'

            elif extension.startswith('image'):
                extension = 'jpeg'

            elif extension.startswith('audio'):
                extension = 'mp3'

            elif extension in ['torrent']:
                extension = 'url'

            else:
                extension = 'readme'

        return extension

    @gen.coroutine
    def get_sidebar_arguments(self):
        category_list = yield ShareCategoryDocument.get_share_category_list()

        kwargs = {
            'SHARE_SETTINGS': SHARE_SETTINGS,
            'current_category': None,
            'category_list': category_list,
        }

        raise gen.Return(kwargs)


class ShareHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        kwargs = yield self.get_sidebar_arguments()

        recommend_func = ShareDownloadDocument.get_hot_download_list

        recommend_share_list = yield recommend_func()
        uploader_list = yield ShareDocument.get_uploader_list()
        newest_share_list = yield ShareDocument.get_share_list(limit=6)

        kwargs.update({
            'uploader_list': uploader_list,
            'recommend_share_list': recommend_share_list,
            'newest_share_list': newest_share_list
        })

        self.render('share/template/share.html', **kwargs)


class ShareNewTemplateHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        kwargs = yield self.get_sidebar_arguments()
        self.render('share/template/share-new.html', **kwargs)


class ShareNewHandler(ShareBaseHandler):
    '''上传新分享'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = ShareNewForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        title = form.title.data
        description = form.description.data
        category = form.category.data
        cost = form.cost.data
        upload_token = form.upload_token.data

        if 'file' not in self.request.files:
            raise HTTPError(404)

        resumableChunkNumber = form.resumableChunkNumber.data
        resumableTotalChunks = form.resumableTotalChunks.data
        resumableFilename = form.resumableFilename.data
        resumableTotalSize = form.resumableTotalSize.data

        document = {
            'chunk_index': resumableChunkNumber,
            'upload_token': upload_token
        }

        existed = yield TemporaryFileDocument.find_one(document)
        if not existed:
            document.update({
                'body': Binary(self.request.files['file'][0]['body']),
                'filename': resumableFilename,
                'uploader': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'upload_time': datetime.now(),
            })

            yield TemporaryFileDocument.insert(document)

        count = yield TemporaryFileDocument.find({
            'upload_token': upload_token
        }).count()

        if resumableTotalChunks == count:
            # 此处又插入最后一个上传的chunk的原因是为了防止，最后一个chunk多次上传后，插入多个分享
            yield TemporaryFileDocument.insert(document)

            _category = yield ShareCategoryDocument.find_one({
                'name': category
            })
            if not _category:
                raise HTTPError(404)

            cursor = TemporaryFileDocument.find({
                'upload_token': upload_token
            }).sort([('chunk_index', pymongo.ASCENDING)])

            chunk_index_list, total_size, data = set(), 0, []
            while (yield cursor.fetch_next):
                chunk = cursor.next_object()
                if chunk['chunk_index'] not in chunk_index_list:
                    data.append(chunk['body'])
                    total_size += len(str(chunk['body']))
                    chunk_index_list.add(chunk['chunk_index'])

            # remove all temporary files
            yield TemporaryFileDocument.remove({'upload_token': upload_token})

            if total_size != resumableTotalSize:
                response_data.update({'message': '上传过程中数据受损，请重新上传！'})
            else:
                gridfs = ShareDocument.get_gridfs()

                try:
                    f = yield gridfs.new_file()
                    yield f.write("".join(data))
                except:
                    response_data.update({"message": "保存失败! 请重新上传!"})
                else:
                    now = datetime.now()
                    content_type = self.request.files['file'][0]['content_type']

                    document = {
                        'title': title,
                        'category': category,
                        'filename': resumableFilename,
                        'content_type': content_type,
                        'description': description,
                        'uploader': DBRef(
                            UserDocument.meta['collection'],
                            ObjectId(self.current_user['_id'])
                        ),
                        'upload_time': now,
                        'cost': cost,
                        'origin_file': ObjectId(f._id)
                    }
                    share_id = yield ShareDocument.insert(document)

                    response_data = {
                        'share_id': str(share_id),
                        'upload_token': upload_token
                    }

                finally:
                    yield f.close()

        self.finish(json.dumps(response_data))


class ShareNewCancelHandler(ShareBaseHandler):
    '''取消上传'''

    @authenticated
    @gen.coroutine
    def post(self):
        form = ShareNewCancelForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        upload_token = form.upload_token.data
        yield TemporaryFileDocument.remove({'upload_token': upload_token})

        self.finish()


class ShareCategoryHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self):
        form = ShareCategoryForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        category = form.category.data

        existed = yield ShareCategoryDocument.find_one({
            'name': category
        })
        if not existed:
            raise HTTPError(404)

        kwargs = yield self.get_sidebar_arguments()

        share_list = yield ShareDocument.get_share_list(
            category=category,
            limit=SHARE_SETTINGS['share_number_per_page']
        )

        share_number = yield ShareDocument.get_share_number(
            category=category
        )
        uploader_number = yield ShareDocument.get_uploader_number(
            category=category
        )

        kwargs.update({
            'current_category': category,
            'share_list': share_list,
            'share_number': share_number,
            'uploader_number': uploader_number
        })

        self.render('share/template/share-category.html', **kwargs)


class ShareDownloadHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, share_id):
        share = yield ShareDocument.get_share(share_id)

        if not share or not share['passed'] or 'origin_file' not in share:
            raise HTTPError(404)

        self.set_header('Content-Type', self.get_content_type(share))
        self.set_header(
            'Content-Disposition',
            'attachment; filename=%s' % self.get_filename(share)
        )

        fs = self.get_gridfs()
        gridout = yield fs.get(ObjectId(share['origin_file']))
        if gridout.length <= 0:
            raise HTTPError(404)

        if (self.current_user['_id'] != share['uploader']['_id']
                and self.current_user['wealth'] < share['cost']):
            raise HTTPError(404)

        size = 0
        while size < gridout.length:
            content = yield gridout.read(gridout.chunk_size)
            size += len(content)
            self.write(content)

        yield ShareDocument.update(
            {'_id': ObjectId(share_id)},
            {'$inc': {'download_times': 1}}
        )

        now = datetime.now()
        document = {
            'user': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'activity_type': UserActivityDocument.DOWNLOAD_SHARE,
            'time': now,
            'data': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            )
        }
        activity_id = yield UserActivityDocument.insert(document)

        document = {
            'share': DBRef(
                ShareDocument.meta['collection'],
                ObjectId(share_id)
            ),
            'downloader': DBRef(
                UserDocument.meta['collection'],
                ObjectId(self.current_user['_id'])
            ),
            'download_time': now
        }
        yield ShareDownloadDocument.insert(document)

        if (share['cost'] > 0 and
                self.current_user['_id'] != share['uploader']['_id']):
            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'in_out_type': WealthRecordDocument.OUT,
                'activity': DBRef(
                    UserActivityDocument.meta['collection'],
                    ObjectId(activity_id)
                ),
                'quantity': share['cost'],
                'time': now
            }
            yield WealthRecordDocument.insert(document)
            yield UserDocument.update_wealth(
                self.current_user['_id'], -share['cost']
            )

            document = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(share['uploader']['_id'])
                ),
                'in_out_type': WealthRecordDocument.IN,
                'activity': DBRef(
                    UserActivityDocument.meta['collection'],
                    ObjectId(activity_id)
                ),
                'quantity': share['cost'],
                'time': now
            }
            yield WealthRecordDocument.insert(document)
            yield UserDocument.update_wealth(
                share['uploader']['_id'], share['cost']
            )

        self.finish()


class ShareOneHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def get(self, share_id):
        share = yield ShareDocument.get_share(
            share_id, self.current_user['_id']
        )
        if not share:
            raise HTTPError(404)

        like_list = yield ShareLikeDocument.get_like_list(
            share_id, limit=10
        )
        recommend_share_list = yield ShareDocument.get_recommend_share_list(
            share_id
        )
        comment_list = yield ShareCommentDocument.get_comment_list(
            share_id, limit=SHARE_SETTINGS['share_comment_number_per_page']
        )

        kwargs = {
            'share': share,
            'like_list': like_list,
            'recommend_share_list': recommend_share_list,
            'comment_list': comment_list,
            'SHARE_SETTINGS': SHARE_SETTINGS
        }
        self.render('share/template/share-one.html', **kwargs)


class ShareCommentNewHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = ShareCommentNewForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}

        content = form.content.data
        share_id = form.share_id.data
        anonymous = form.anonymous.data
        replyeder_id = form.replyeder_id.data

        replyeder = None
        if replyeder_id:
            replyeder = yield UserDocument.find_one({
                '_id': ObjectId(replyeder_id)
            })
            if (not replyeder or
                    anonymous or
                    self.current_user['_id'] == replyeder['_id']):
                raise HTTPError(404)

        share = yield ShareDocument.find_one({'_id': ObjectId(share_id)})
        if not share:
            raise HTTPError(404)

        if not response_data:
            now = datetime.now()

            document = {
                'author': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'share': DBRef(
                    ShareDocument.meta['collection'],
                    ObjectId(share['_id'])
                ),
                'comment_time': now,
                'content': content,
                'anonymous': anonymous
            }

            if replyeder:
                document.update({
                    'replyeder': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(replyeder_id)
                    )
                })

            comment_id = yield ShareCommentDocument.insert_one(document)

            activity = {
                'user': DBRef(
                    UserDocument.meta['collection'],
                    ObjectId(self.current_user['_id'])
                ),
                'activity_type': UserActivityDocument.COMMENT,
                'time': now,
                'data': DBRef(
                    ShareCommentDocument.meta['collection'],
                    ObjectId(comment_id)
                )
            }
            yield UserActivityDocument.insert(activity)

            if replyeder:
                recipient_id = replyeder_id
                message_type = 'reply:share'
                message_share = MessageTopic.REPLY
            else:
                recipient_id = share['uploader'].id
                message_type = 'comment:share'
                message_share = MessageTopic.COMMENT

            if (str(self.current_user['_id']) != str(recipient_id) and
                    not anonymous):
                message = {
                    'sender': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'recipient': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(recipient_id)
                    ),
                    'message_type': message_type,
                    'time': now,
                    'read': False,
                    'data': DBRef(
                        ShareCommentDocument.meta['collection'],
                        ObjectId(comment_id)
                    )
                }
                message_id = yield MessageDocument.insert(message)
                WriterManager.pub(message_share, message_id)

            comment_times = yield ShareCommentDocument.get_comment_times(
                share_id
            )

            document.update({
                '_id': ObjectId(comment_id),
                'author': self.current_user,
                'floor': comment_times
            })

            if replyeder:
                document.update({'replyeder': replyeder})

            item = self.render_string(
                'share/template/share-comment-list-item.html',
                comment=document
            )
            response_data.update({'item': item})

        self.finish(json.dumps(response_data))


class ShareLikeHandler(ShareBaseHandler):
    @authenticated
    @gen.coroutine
    def post(self):
        form = ShareLikeForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        response_data = {}
        share_id = form.share_id.data

        share = yield ShareDocument.find_one({
            '_id': ObjectId(share_id)
        })
        if not share:
            raise HTTPError(404)

        can_afford = yield UserDocument.can_afford(
            self.current_user['_id'], WEALTH_SETTINGS['like']
        )

        if (not can_afford and
                str(self.current_user['_id']) != str(share['uploader'].id)):
            response_data.update({'error': '金币不足！'})

        share_dbref = DBRef(
            ShareDocument.meta['collection'],
            ObjectId(share_id)
        )
        liker_dbref = DBRef(
            UserDocument.meta['collection'],
            ObjectId(self.current_user['_id'])
        )

        document = {
            'share': share_dbref,
            'liker': liker_dbref
        }

        liked = yield ShareLikeDocument.is_liked(
            share_id, self.current_user['_id']
        )
        if not liked and not response_data:
            now = datetime.now()

            document.update({
                'like_time': now
            })
            like_id = yield ShareLikeDocument.insert_one(document)

            if str(self.current_user['_id']) != str(share['uploader'].id):
                activity = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'activity_type': UserActivityDocument.LIKE,
                    'time': now,
                    'data': DBRef(
                        ShareLikeDocument.meta['collection'],
                        ObjectId(like_id)
                    )
                }
                activity_id = yield UserActivityDocument.insert(activity)

                # 赞者
                wealth = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'in_out_type': WealthRecordDocument.OUT,
                    'activity': DBRef(
                        UserActivityDocument.meta['collection'],
                        ObjectId(activity_id)
                    ),
                    'quantity': WEALTH_SETTINGS['like'],
                    'time': now
                }
                yield WealthRecordDocument.insert(wealth)
                yield UserDocument.update_wealth(
                    self.current_user['_id'], -WEALTH_SETTINGS['like']
                )

                # 被赞者
                wealth = {
                    'user': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(share['uploader'].id)
                    ),
                    'in_out_type': WealthRecordDocument.IN,
                    'activity': DBRef(
                        UserActivityDocument.meta['collection'],
                        ObjectId(activity_id)
                    ),
                    'quantity': WEALTH_SETTINGS['like'],
                    'time': now
                }
                yield WealthRecordDocument.insert(wealth)
                yield UserDocument.update_wealth(
                    share['uploader'].id, WEALTH_SETTINGS['like']
                )

                message = {
                    'sender': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(self.current_user['_id'])
                    ),
                    'recipient': DBRef(
                        UserDocument.meta['collection'],
                        ObjectId(share['uploader'].id)
                    ),
                    'message_type': 'like:share',
                    'time': now,
                    'read': False,
                    'data': DBRef(
                        ShareLikeDocument.meta['collection'],
                        ObjectId(like_id)
                    )
                }

                message_id = yield MessageDocument.insert(message)
                WriterManager.pub(MessageTopic.LIKE, str(message_id))

        like_times = yield ShareLikeDocument.get_like_times(share_id)
        response_data.update({'like_times': like_times})

        self.finish(json.dumps(response_data))
