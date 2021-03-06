import json

from aiohttp import web as aw

from .database import InvalidFilterError


# NOTE we dont expect filters will be large text
class FiltersHandler(aw.View):

    async def post(self):
        filters = self.request.app['filters']
        new_filter = await self.request.text()
        try:
            new_id = await filters.add(new_filter)
        except InvalidFilterError:
            return aw.Response(status=400)
        rv = str(new_id)
        return aw.Response(text=rv, content_type='application/json')

    async def get(self):
        filters = self.request.app['filters']
        rv = await filters.get()
        rv = json.dumps(rv)
        rv = rv + '\n'
        return aw.Response(text=rv, content_type='application/json')

    async def put(self):
        id_ = self.request.match_info['id']
        if id_ is None:
            return aw.Response(status=400)
        id_ = int(id_)

        filters = self.request.app['filters']
        new_filter = await self.request.text()
        try:
            ok = await filters.update(id_, new_filter)
        except InvalidFilterError:
            return aw.Response(status=400)
        if not ok:
            return aw.Response(status=500)
        return aw.Response()

    async def delete(self):
        id_ = self.request.match_info['id']
        if id_ is None:
            return aw.Response(status=400)
        id_ = int(id_)

        filters = self.request.app['filters']
        ok = await filters.remove(id_)
        if not ok:
            return aw.Response(status=500)
        return aw.Response()
