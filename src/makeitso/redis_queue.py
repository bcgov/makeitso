from flask import Flask, current_app
from redis import Redis
from rq import Queue, Worker


class RedisQueue:
    def init_app(self, app: Flask) -> None:
        # Client connection to the Redis server
        connection = Redis.from_url(app.config["REDIS_URL"])
        # The "default" queue, stored on the app so any code can reach it via `queue`
        app.extensions["rq_queue"] = Queue(connection=connection)

        # Adds `flask worker`; it runs in the app context
        @app.cli.command("worker")
        def worker() -> None:
            """Run a background job worker."""
            queue = self.queue
            # Listen on the queue and run jobs until stopped
            Worker([queue], connection=queue.connection).work()

    # The current app's job queue
    @property
    def queue(self) -> Queue:
        return current_app.extensions["rq_queue"]
