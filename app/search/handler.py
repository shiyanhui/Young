# -*- coding: utf-8 -*-

from tornado import gen
from tornado.web import HTTPError

from young.handler import BaseHandler
from app.user.document import UserDocument
from app.community.document import TopicDocument
from app.share.document import ShareDocument
from app.search.form import SearchForm

__all__ = ['SearchHandler']


class SearchHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        form = SearchForm(self.request.arguments)
        if not form.validate():
            raise HTTPError(404)

        category = form.category.data
        query = form.query.data

        response_data = []
        if category == 'user':
            res = self.es.search(
                index="young",
                doc_type=UserDocument.meta['collection'],
                body={
                    "query": {
                        "match": {
                            "name": query
                        }
                    }
                }
            )

            response_data = [
                {'name': r["_source"]['name'], '_id': r["_id"]}
                for r in res["hits"]["hits"]
            ]

        elif category == 'topic':
            res = self.es.search(
                index="young",
                doc_type=TopicDocument.meta['collection'],
                body={
                    "query": {
                        "match": {
                            "title": query
                        }
                    }
                }
            )

            response_data = [
                {'title': r["_source"]['title'], '_id': r["_id"]}
                for r in res["hits"]["hits"]
            ]

        elif category == 'share':
            res = self.es.search(
                index="young",
                doc_type=ShareDocument.meta['collection'],
                body={
                    "query": {
                        "match": {
                            "title": query
                        }
                    }
                }
            )

            response_data = [
                {'title': r["_source"]['title'], '_id': r["_id"]}
                for r in res["hits"]["hits"]
            ]

        self.write_json(response_data)
