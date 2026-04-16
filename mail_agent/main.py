import logging
import time

import click

from .agent import Agent
from .config import Config

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@click.group()
@click.option(
    "--config",
    "config_path",
    default="config.yaml",
    show_default=True,
    help="Path to the YAML config file.",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@click.pass_context
def cli(ctx: click.Context, config_path: str, verbose: bool) -> None:
    """Mail AI Agent — triage your inbox with a local LLM."""
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.from_yaml(config_path)


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Process all unread emails once, then exit."""
    agent = Agent(ctx.obj["config"])
    agent.run_once()


@cli.command()
@click.option(
    "--interval",
    default=None,
    type=int,
    help="Poll interval in seconds (overrides config value).",
)
@click.pass_context
def watch(ctx: click.Context, interval: int | None) -> None:
    """Poll for new emails in a continuous loop. Stop with Ctrl+C."""
    config: Config = ctx.obj["config"]
    poll_interval = interval or config.agent.poll_interval
    agent = Agent(config)

    logger.info(
        "Starting watch mode (interval=%ds, folder=%s). Press Ctrl+C to stop.",
        poll_interval,
        config.agent.folder or "INBOX",
    )

    while True:
        try:
            agent.run_once()
        except Exception as exc:
            logger.error("Unhandled error during run: %s", exc, exc_info=True)

        logger.info("Sleeping %ds until next poll...", poll_interval)
        time.sleep(poll_interval)


if __name__ == "__main__":
    cli()
