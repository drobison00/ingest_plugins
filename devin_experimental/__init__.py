"""
devin_experimental - A clean plugin for running in-process NV-Ingest pipelines.

Supports all document types: PDF, DOCX, PPTX, images, text, HTML, and audio.

Quick Start
-----------
>>> from devin_experimental import launch_pipeline, get_stage_actor, ProcessingClient, DEFAULT_TASK_CONFIG
>>>
>>> # Launch the pipeline
>>> interface = launch_pipeline("pipeline.yaml")
>>> source = get_stage_actor(interface, "source_stage")
>>> sink = get_stage_actor(interface, "broker_response")
>>>
>>> # Create a client and process files (auto-detects document type)
>>> client = ProcessingClient(source=source, sink=sink, show_progress=True)
>>> results = client.process_files("/data/*", task_config=DEFAULT_TASK_CONFIG)
"""

# Configuration - Document types and mappings
from .config import (
    DocumentType,
    EXTENSION_TO_DOCUMENT_TYPE,
    DEFAULT_EXTRACT_METHOD,
)

# Configuration - Extraction options for each document type
from .config import (
    PdfExtractOptions,
    DocxExtractOptions,
    PptxExtractOptions,
    ImageExtractOptions,
    TextExtractOptions,
    HtmlExtractOptions,
    AudioExtractOptions,
)

# Configuration - Processing task options
from .config import (
    EmbedOptions,
    CaptionOptions,
    SplitOptions,
    FilterOptions,
    DedupOptions,
)

# Configuration - Task config
from .config import (
    DEFAULT_TASK_CONFIG,
    DEFAULT_TASK_CONFIG_JSON,
    TaskConfig,
)

# Pipeline launching
from .pipeline import (
    get_stage_actor,
    launch_pipeline,
)

# Processing client
from .client import (
    ProcessingClient,
    SubmittedJob,
)

# Utilities
from .util import (
    FileInput,
    get_pdf_page_count,
    write_results_to_directory,
)

# Custom stages (for pipeline configuration)
from .stages import (
    DirectSubmitSourceStage,
    OutputQueueSinkStage,
)

__all__ = [
    # Document types
    "DocumentType",
    "EXTENSION_TO_DOCUMENT_TYPE",
    "DEFAULT_EXTRACT_METHOD",
    # Extraction options
    "PdfExtractOptions",
    "DocxExtractOptions",
    "PptxExtractOptions",
    "ImageExtractOptions",
    "TextExtractOptions",
    "HtmlExtractOptions",
    "AudioExtractOptions",
    # Processing options
    "EmbedOptions",
    "CaptionOptions",
    "SplitOptions",
    "FilterOptions",
    "DedupOptions",
    # Task config
    "DEFAULT_TASK_CONFIG",
    "DEFAULT_TASK_CONFIG_JSON",
    "TaskConfig",
    # Pipeline
    "get_stage_actor",
    "launch_pipeline",
    # Client
    "ProcessingClient",
    "SubmittedJob",
    # Utilities
    "FileInput",
    "get_pdf_page_count",
    "write_results_to_directory",
    # Stages
    "DirectSubmitSourceStage",
    "OutputQueueSinkStage",
]
