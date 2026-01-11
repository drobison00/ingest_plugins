#!/usr/bin/env python3
"""
Example 02: Process PDF Files

This example demonstrates how to process PDF files through the pipeline
using the ProcessingClient with the default task configuration.

Prerequisites:
    - Pipeline launched (see 01_launch_pipeline.py)
    - PDF files to process

Usage:
    python 02_process_pdfs.py --config pipeline.yaml --pdf "/data/*.pdf" -n 10
"""

import argparse
import logging
import os

from devin_experimental import (
    DEFAULT_TASK_CONFIG,
    ProcessingClient,
    get_pdf_page_count,
    get_stage_actor,
    launch_pipeline,
    write_results_to_directory,
)


def main():
    parser = argparse.ArgumentParser(description="Process PDF files")
    parser.add_argument(
        "--config",
        type=str,
        default=os.getenv("NV_INGEST_PIPELINE_CONFIG_PATH", "pipeline.yaml"),
        help="Path to pipeline config",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="PDF file or glob pattern (e.g., '/data/*.pdf')",
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        default=None,
        help="Number of jobs to process (repeats files if needed)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory for results",
    )
    parser.add_argument(
        "--inflight",
        type=int,
        default=32,
        help="Max in-flight jobs",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("INGEST_LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Launch pipeline
    logger.info(f"Launching pipeline from: {args.config}")
    interface = launch_pipeline(args.config)
    source = get_stage_actor(interface, "source_stage")
    sink = get_stage_actor(interface, "broker_response")

    # Create processing client with progress bar
    client = ProcessingClient(
        source=source,
        sink=sink,
        inflight=args.inflight,
        show_progress=True,
        progress_desc="pages",
        progress_unit="page",
    )

    # Optional: callback to write results
    def on_result(cm):
        if args.output:
            write_results_to_directory(args.output, cm)

    # Process PDFs using default configuration
    logger.info(f"Processing PDFs matching: {args.pdf}")
    results = client.process_pdf_files(
        args.pdf,
        repeat_to=args.num,
        task_config=DEFAULT_TASK_CONFIG,
        page_count_fn=get_pdf_page_count,
        on_result=on_result if args.output else None,
    )

    # Print summary
    logger.info(f"Completed!")  # noqa: F541
    logger.info(f"  Submitted: {client.submitted_count}")
    logger.info(f"  Received:  {client.received_count}")
    logger.info(f"  Elapsed:   {client.elapsed:.2f}s")

    if results:
        # Show sample result
        sample = results[0]
        df = sample.payload()
        if df is not None:
            logger.info(f"  Sample result: {len(df)} rows")
            logger.info(f"  Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
