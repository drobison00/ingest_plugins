#!/usr/bin/env python3
"""
Example 04: BytesIO Input

This example demonstrates how to process PDFs from BytesIO objects,
which is useful for:
- HTTP file uploads
- S3/cloud storage downloads
- In-memory PDF generation
- Streaming scenarios

Usage:
    python 04_bytesio_input.py --config pipeline.yaml --pdf sample.pdf
"""

import argparse
import logging
import os
from io import BytesIO

from devin_experimental import (
    DEFAULT_TASK_CONFIG,
    FileInput,
    ProcessingClient,
    get_pdf_page_count,
    get_stage_actor,
    launch_pipeline,
)


def simulate_http_upload(file_path: str) -> tuple[str, BytesIO]:
    """Simulate receiving a file from an HTTP upload."""
    with open(file_path, "rb") as f:
        content = f.read()
    filename = os.path.basename(file_path)
    return filename, BytesIO(content)


def simulate_s3_download(file_path: str) -> bytes:
    """Simulate downloading a file from S3."""
    with open(file_path, "rb") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="Process PDFs from BytesIO")
    parser.add_argument("--config", type=str, required=True, help="Pipeline config path")
    parser.add_argument("--pdf", type=str, required=True, help="Sample PDF file to use")
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("INGEST_LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)

    # Launch pipeline
    interface = launch_pipeline(args.config)
    source = get_stage_actor(interface, "source_stage")
    sink = get_stage_actor(interface, "broker_response")

    # Create client
    client = ProcessingClient(
        source=source,
        sink=sink,
        show_progress=True,
        progress_desc="files",
        progress_unit="file",
    )

    # Simulate various input scenarios
    logger.info("Preparing inputs from different sources...")

    # Scenario 1: HTTP upload (BytesIO with filename)
    upload_name, upload_buffer = simulate_http_upload(args.pdf)
    http_upload = FileInput(buffer=upload_buffer, name=f"http_upload_{upload_name}")

    # Scenario 2: S3 download (raw bytes)
    s3_bytes = simulate_s3_download(args.pdf)
    s3_download = FileInput(data=s3_bytes, name="s3_document.pdf")

    # Scenario 3: In-memory buffer
    with open(args.pdf, "rb") as f:
        memory_buffer = BytesIO(f.read())
    in_memory = FileInput(buffer=memory_buffer, name="in_memory.pdf")

    # Scenario 4: Direct file path (for comparison)
    file_path = FileInput(path=args.pdf)

    # Combine all inputs
    inputs = [
        http_upload,
        s3_download,
        in_memory,
        file_path,
    ]

    logger.info(f"Processing {len(inputs)} files from different sources...")

    # Process all inputs
    results = client.process_files(
        inputs,
        task_config=DEFAULT_TASK_CONFIG,
        page_count_fn=get_pdf_page_count,
    )

    # Show results
    logger.info(f"Processed {len(results)} documents")
    for i, cm in enumerate(results):
        job_id = cm.get_metadata("client_job_uuid")
        df = cm.payload()
        row_count = len(df) if df is not None else 0
        logger.info(f"  [{i}] Job {job_id[:8]}... -> {row_count} rows")


if __name__ == "__main__":
    main()
