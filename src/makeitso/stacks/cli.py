# The command-line library Flask's `flask` command is built on
import click

from makeitso.stacks.routes import bp
from makeitso.stacks.tasks import enqueue_stale_syncs


@bp.cli.command("sync")
def sync_command() -> None:
    """Queue syncs for stacks that haven't synced in a while"""
    count = enqueue_stale_syncs()
    click.echo(f"Queued a sync for {count} stack(s)")
