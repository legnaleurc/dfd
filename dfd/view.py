from aiohttp.web import View
import aiohttp_jinja2 as aj


class IndexHandler(View):
    async def get(self):
        return aj.render_template("index.html", self.request, None)
