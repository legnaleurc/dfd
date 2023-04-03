from argparse import ArgumentParser
import asyncio
from contextlib import asynccontextmanager
from logging import getLogger
from logging.config import dictConfig
import os.path as op
import signal
import sys

from aiohttp.web import Application, AppRunner, TCPSite
import aiohttp_jinja2 as aj
import jinja2
from wcpan.logging import ConfigBuilder

from . import api, view, database


class Daemon(object):
    def __init__(self, args):
        self._kwargs = parse_args(args[1:])
        self._loop = asyncio.get_event_loop()
        self._finished = asyncio.Event()
        dictConfig(
            ConfigBuilder(path="/tmp/dfd.log", rotate=True)
            .add("dfd", level="D")
            .to_dict()
        )

    def __call__(self):
        self._loop.create_task(self._guard())
        self._loop.add_signal_handler(signal.SIGINT, self._close)
        self._loop.run_forever()
        self._loop.close()

        return 0

    async def _guard(self):
        try:
            return await self._main()
        except Exception:
            getLogger(__name__).exception("main function error")
        finally:
            self._loop.stop()
        return 1

    async def _main(self):
        app = Application()

        setup_static_and_view(app)
        setup_api_path(app)

        root = op.dirname(__file__)
        root = op.join(root, "..")
        root = op.normpath(root)
        db_path = op.join(root, "filters.sqlite")

        async with database.Filters(db_path) as filters, server_context(
            app, self._kwargs.listen
        ):
            app["filters"] = filters
            await self._until_finished()

        return 0

    async def _until_finished(self):
        await self._finished.wait()

    def _close(self):
        self._finished.set()


@asynccontextmanager
async def server_context(app: Application, port: int):
    log_format = "%s %r (%b) %Tfs"
    runner = AppRunner(app, access_log_format=log_format)
    await runner.setup()
    try:
        site = TCPSite(runner, port=port)
        await site.start()
        yield runner
    finally:
        await runner.cleanup()


def parse_args(args):
    parser = ArgumentParser("dfd")

    parser.add_argument("-l", "--listen", required=True, type=int)

    args = parser.parse_args(args)

    return args


def setup_static_and_view(app: Application):
    root = op.dirname(__file__)
    static_path = op.join(root, "static")
    template_path = op.join(root, "templates")

    app.router.add_static("/static/", path=static_path, name="static")
    app["static_root_url"] = "/static"

    aj.setup(app, loader=jinja2.FileSystemLoader(template_path))

    app.router.add_view(r"/", view.IndexHandler)


def setup_api_path(app: Application):
    app.router.add_view(r"/api/v1/filters", api.FiltersHandler)
    app.router.add_view(r"/api/v1/filters/{id:\d+}", api.FiltersHandler)


main = Daemon(sys.argv)
exit_code = main()
sys.exit(exit_code)
