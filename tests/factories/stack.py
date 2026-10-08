from polyfactory import Use

from makeitso.models.stack import Stack
from tests.factories.base import BaseFactory


class StackFactory(BaseFactory[Stack]):
    # No commits, deploys or env vars unless a test makes them
    __set_relationships__ = False

    environment = "dev"
    locked = False
    lock_reason = None
    continuous_deploy = False
    allow_failures = Use(list)
    synced_at = None
    sync_failures = 0
    archived_at = None
