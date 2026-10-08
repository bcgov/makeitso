from polyfactory import Ignore, PostGenerated, Use

from makeitso.deploys.tasks import start_deploy
from makeitso.models.commit import Commit
from makeitso.models.deploy import Deploy, DeployStatus
from tests.factories.base import BaseFactory
from tests.factories.commit import CommitFactory


# A finished, successful deploy
class DeployFactory(BaseFactory[Deploy]):
    commit = Use(CommitFactory.build)
    # Always the commit's own stack
    stack = PostGenerated(lambda _name, values: values["commit"].stack)
    since_commit = None
    status = DeployStatus.SUCCEEDED
    output = ""
    deployed_with_bypass = False
    deployed_by = "octocat"
    # The database sets it to now
    started_at = Ignore()
    ended_at = None


def start_running_deploy(commit: Commit | None = None) -> Deploy:
    """A running deploy with its queued job, as the deploy page starts it.
    DeployFactory can't make one: without a job, pages would mark it as lost"""
    commit = commit or CommitFactory.create_sync()
    return start_deploy(commit.stack, commit, timeout=600, deployed_by="octocat")
