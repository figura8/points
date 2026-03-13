"""Minimal scheduler skeleton for orchestrating scan jobs."""

from __future__ import annotations

import logging

from crawler.queue import get_next_jobs

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def run_once() -> None:
    """Run one minimal scheduler pass."""
    jobs = get_next_jobs(limit=5)
    logger.info("Scheduler tick: found %s pending jobs", len(jobs))
    # TODO: For each job, run crawler and parser, then upsert results and update job status.


if __name__ == "__main__":
    logger.info("Starting minimal scheduler skeleton")
    run_once()
