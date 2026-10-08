from polyfactory import Use

from makeitso.models.commit import Commit
from tests.factories.base import BaseFactory
from tests.factories.stack import StackFactory


class CommitFactory(BaseFactory[Commit]):
    # A new stack, saved with the commit
    stack = Use(StackFactory.build)
    deploys = Use(list)
    commit_statuses = Use(list)
    pull_request_number = None
