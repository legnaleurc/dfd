import argparse
import asyncio
import logging
import os.path as op
import signal
import sys

from aiohttp import web as aw
import aiohttp_jinja2 as aj
import jinja2
from wcpan.logger import setup as setup_logger, INFO, EXCEPTION

from . import api, view, database


class Daemon(object):
    def __init__(self, args):
        self._kwargs = parse_args(args[1:])
        self._loop = asyncio.get_event_loop()
        self._finished = asyncio.Event()
        self._loggers = setup_logger(
            (
                "aiohttp",
                "dfd",
            ),
            "/tmp/dfd.log",
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
        except Exception as e:
            EXCEPTION("dfd", e)
        finally:
            self._loop.stop()
        return 1

    async def _main(self):
        app = aw.Application()

        setup_static_and_view(app)
        setup_api_path(app)

        root = op.dirname(__file__)
        root = op.join(root, "..")
        root = op.normpath(root)
        db_path = op.join(root, "filters.sqlite")

        async with database.Filters(db_path) as filters, ServerContext(
            app, self._kwargs.listen
        ):
            app["filters"] = filters
            await self._until_finished()

        return 0

    async def _until_finished(self):
        await self._finished.wait()

    def _close(self):
        self._finished.set()


class ServerContext(object):
    def __init__(self, app, port):
        log_format = "%s %r (%b) %Tfs"
        self._runner = aw.AppRunner(app, access_log_format=log_format)
        self._port = port

    async def __aenter__(self):
        await self._runner.setup()
        site = aw.TCPSite(self._runner, port=self._port)
        await site.start()
        return self._runner

    async def __aexit__(self, exc_type, exc, tb):
        await self._runner.cleanup()


def parse_args(args):
    parser = argparse.ArgumentParser("dfd")

    parser.add_argument("-l", "--listen", required=True, type=int)

    args = parser.parse_args(args)

    return args


def setup_static_and_view(app):
    root = op.dirname(__file__)
    static_path = op.join(root, "static")
    template_path = op.join(root, "templates")

    app.router.add_static("/static/", path=static_path, name="static")
    app["static_root_url"] = "/static"

    aj.setup(app, loader=jinja2.FileSystemLoader(template_path))

    app.router.add_view(r"/", view.IndexHandler)


def setup_api_path(app):
    app.router.add_view(r"/api/v1/filters", api.FiltersHandler)
    app.router.add_view(r"/api/v1/filters/{id:\d+}", api.FiltersHandler)


main = Daemon(sys.argv)
exit_code = main()
sys.exit(exit_code)
