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

from . import api, view
from .database import Filters


class Daemon(object):
    def __init__(self, args):
        self._kwargs = parse_args(args[1:])
        self._finished = asyncio.Event()
        dictConfig(
            ConfigBuilder(path="/tmp/dfd.log", rotate=True)
            .add("dfd", level="D")
            .to_dict()
        )

    async def __call__(self):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._close)
        try:
            return await self._main()
        except Exception:
            getLogger(__name__).exception("main function error")
        finally:
            loop.stop()
        return 1

    async def _main(self):
        app = Application()

        setup_static_and_view(app)
        setup_api_path(app)

        db_path = self._kwargs.database

        async with Filters(db_path) as filters:
            app["filters"] = filters
            async with server_context(app, self._kwargs.listen):
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
    parser.add_argument("--database", required=True, type=str)

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


if __name__ == "__main__":
    main = Daemon(sys.argv)
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
