#!/usr/bin/env python3
"""
Example 05: Async Processing

This example demonstrates how to use async/await to process results
as they become available, rather than waiting for all results.

Useful for:
- Streaming results to a client
- Processing results in parallel with submission
- Building responsive applications

Usage:
    python 05_async_processing.py --config pipeline.yaml --pdf "/data/*.pdf"
"""

import argparse
import asyncio
import logging
import os

from devin_experimental import (
    DEFAULT_TASK_CONFIG,
    ProcessingClient,
    get_pdf_page_count,
    get_stage_actor,
    launch_pipeline,
)


async def process_results_as_available(client: ProcessingClient):
    """Process results as they arrive using async iteration."""
    logger = logging.getLogger(__name__)

    count = 0
    async for cm in client.fetch_as_available():
        count += 1
        job_id = cm.get_metadata("client_job_uuid")
        df = cm.payload()
        rows = len(df) if df is not None else 0
        logger.info(f"  Result {count}: job={job_id[:8]}... rows={rows}")

        # You could do async processing here, e.g.:
        # await send_to_database(cm)
        # await notify_client(job_id)

    return count


async def main_async(args):
    logging.basicConfig(level=os.getenv("INGEST_LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)

    # Launch pipeline
    interface = launch_pipeline(args.config)
    source = get_stage_actor(interface, "source_stage")
    sink = get_stage_actor(interface, "broker_response")

    # Create client (no progress bar for async mode)
    client = ProcessingClient(
        source=source,
        sink=sink,
        inflight=args.inflight,
        show_progress=False,
    )

    # Submit files (this returns immediately after submission)
    logger.info(f"Submitting PDFs matching: {args.pdf}")
    client.submit_files(
        ProcessingClient.expand_file_pattern(args.pdf, extensions=[".pdf"], repeat_to=args.num),
        task_config=DEFAULT_TASK_CONFIG,
        page_count_fn=get_pdf_page_count,
    )
    logger.info(f"Submitted {client.submitted_count} jobs")

    # Process results as they arrive
    logger.info("Processing results as they arrive...")
    result_count = await process_results_as_available(client)

    logger.info(f"Completed: {result_count} results in {client.elapsed:.2f}s")


def main():
    parser = argparse.ArgumentParser(description="Async PDF processing")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--pdf", type=str, required=True)
    parser.add_argument("-n", "--num", type=int, default=10)
    parser.add_argument("--inflight", type=int, default=32)
    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
