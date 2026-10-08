from polyfactory import Use

from makeitso.models.commit_status import CommitStatus
from tests.factories.base import BaseFactory
from tests.factories.commit import CommitFactory


# A CI check; passing unless the test sets state="failure"
class CommitStatusFactory(BaseFactory[CommitStatus]):
    commit = Use(CommitFactory.build)
    state = "success"
