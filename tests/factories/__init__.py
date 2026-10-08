"""Test data, one file per model. Each factory fills the fields a test doesn't set with random
values, and `create_sync()` saves the row: DeployFactory.create_sync(status=DeployStatus.FAILED)

Fields that change how the app behaves (status, locks, archiving...) are pinned to normal values,
so a test only sets what it is about. A new factory goes in its own file and is added below"""

from tests.factories.commit import CommitFactory
from tests.factories.commit_status import CommitStatusFactory
from tests.factories.deploy import DeployFactory, start_running_deploy
from tests.factories.stack import StackFactory

__all__ = [
    "CommitFactory",
    "CommitStatusFactory",
    "DeployFactory",
    "StackFactory",
    "start_running_deploy",
]
