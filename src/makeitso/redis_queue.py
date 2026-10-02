import click
from flask import Flask, current_app
from redis import Redis
from rq import Queue, Worker

QUEUE_NAMES = ("deploys", "syncs")


class RedisQueue:
    def init_app(self, app: Flask) -> None:
        # Client connection to the Redis server
        connection = Redis.from_url(app.config["REDIS_URL"])
        # Stored on the app so any code can reach them via `deploys` and `syncs`
        app.extensions["rq_queues"] = {
            name: Queue(name, connection=connection) for name in QUEUE_NAMES
        }

        # Adds `flask worker`; it runs in the app context
        @app.cli.command("worker")
        @click.option(
            "--queue",
            "names",
            multiple=True,
            type=click.Choice(QUEUE_NAMES),
            help="Queue to listen on, can be repeated. Defaults to all of them",
        )
        def worker(names: tuple[str, ...]) -> None:
            """Run a background job worker."""
            queues = [self._queue(name) for name in names or QUEUE_NAMES]
            # Listen on the queues and run jobs until stopped
            Worker(queues, connection=connection).work()

    @property
    def deploys(self) -> Queue:
        return self._queue("deploys")

    @property
    def syncs(self) -> Queue:
        return self._queue("syncs")

    def _queue(self, name: str) -> Queue:
        return current_app.extensions["rq_queues"][name]
