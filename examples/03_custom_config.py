#!/usr/bin/env python3
"""
Example 03: Custom Configuration

This example demonstrates how to use custom extraction and embedding
configurations instead of the default settings.

Usage:
    python 03_custom_config.py --config pipeline.yaml --pdf "/data/*.pdf"
"""

import argparse
import logging
import os

from devin_experimental import (
    EmbedOptions,
    PdfExtractOptions,
    ProcessingClient,
    TaskConfig,
    get_pdf_page_count,
    get_stage_actor,
    launch_pipeline,
)


def main():
    parser = argparse.ArgumentParser(description="Process PDFs with custom config")
    parser.add_argument("--config", type=str, required=True, help="Pipeline config path")
    parser.add_argument("--pdf", type=str, required=True, help="PDF file or glob pattern")
    parser.add_argument("--embed-endpoint", type=str, default=None, help="Embedding endpoint URL")
    args = parser.parse_args()

    logging.basicConfig(level=os.getenv("INGEST_LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)

    # Launch pipeline
    interface = launch_pipeline(args.config)
    source = get_stage_actor(interface, "source_stage")
    sink = get_stage_actor(interface, "broker_response")

    # Create custom configuration
    # Option 1: Programmatic configuration
    custom_config = TaskConfig(
        extract=PdfExtractOptions(
            extract_method="pdfium",
            extract_text=True,
            extract_images=True,
            extract_tables=True,
            extract_charts=True,
            extract_infographics=False,  # Disable infographics
            text_depth="page",  # Page-level text instead of document
            table_output_format="markdown",
        ),
        embed=(
            EmbedOptions(
                endpoint_url=args.embed_endpoint,
                filter_errors=True,
            )
            if args.embed_endpoint
            else None
        ),
        enable_tracing=True,
    )

    # Option 2: Load from JSON string
    # custom_config = TaskConfig.from_json('''
    # {
    #     "extract": {
    #         "extract_text": true,
    #         "extract_tables": true,
    #         "extract_charts": false,
    #         "text_depth": "page"
    #     },
    #     "embed": {
    #         "endpoint_url": "http://localhost:8012/v1/embeddings"
    #     }
    # }
    # ''')

    # Option 3: Load from JSON file
    # custom_config = TaskConfig.from_file("my_config.json")

    logger.info("Custom configuration:")
    logger.info(custom_config.to_json())

    # Create client
    client = ProcessingClient(
        source=source,
        sink=sink,
        show_progress=True,
        progress_desc="pages",
        progress_unit="page",
    )

    # Process with custom config
    results = client.process_pdf_files(
        args.pdf,
        task_config=custom_config,
        page_count_fn=get_pdf_page_count,
    )

    logger.info(f"Processed {len(results)} documents")

    # Inspect a result
    if results:
        df = results[0].payload()
        if df is not None and "metadata" in df.columns:
            for idx, row in df.iterrows():
                meta = row.get("metadata", {})
                content_meta = meta.get("content_metadata", {}) if isinstance(meta, dict) else {}
                content_type = content_meta.get("type", "unknown")
                logger.info(f"  Row {idx}: type={content_type}")


if __name__ == "__main__":
    main()
