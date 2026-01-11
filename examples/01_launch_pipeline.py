#!/usr/bin/env python3
"""
Example 01: Launch Pipeline

This example demonstrates how to launch an NV-Ingest pipeline and verify
that it's running correctly.

Prerequisites:
    - NV-Ingest dependencies installed
    - Pipeline YAML configuration file

Usage:
    python 01_launch_pipeline.py --config path/to/pipeline.yaml
"""

import argparse
import logging
import os
import sys

from devin_experimental import launch_pipeline, get_stage_actor


def main():
    parser = argparse.ArgumentParser(description="Launch an NV-Ingest pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default=os.getenv("NV_INGEST_PIPELINE_CONFIG_PATH", "pipeline.yaml"),
        help="Path to the pipeline YAML configuration file",
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=os.getenv("INGEST_LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Check if config file exists
    if not os.path.exists(args.config):
        logger.error(f"Pipeline config not found: {args.config}")
        sys.exit(1)

    logger.info(f"Launching pipeline from: {args.config}")

    # Launch the pipeline
    interface = launch_pipeline(args.config)

    # Verify we can access the key stages
    try:
        source = get_stage_actor(interface, "source_stage")
        logger.info(f"✓ Source stage actor: {source}")
    except RuntimeError as e:
        logger.error(f"✗ Failed to get source stage: {e}")
        sys.exit(1)

    try:
        sink = get_stage_actor(interface, "broker_response")
        logger.info(f"✓ Sink stage actor: {sink}")
    except RuntimeError as e:
        logger.error(f"✗ Failed to get sink stage: {e}")
        sys.exit(1)

    logger.info("Pipeline launched successfully!")
    logger.info("Press Ctrl+C to stop the pipeline")

    # Keep the pipeline running
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
