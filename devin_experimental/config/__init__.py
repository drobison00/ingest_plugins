"""Configuration classes for the processing pipeline."""

from .options import (
    AudioExtractOptions,
    CaptionOptions,
    DedupOptions,
    DocxExtractOptions,
    DocumentType,
    EmbedOptions,
    ExtractOptions,
    EXTENSION_TO_DOCUMENT_TYPE,
    DEFAULT_EXTRACT_METHOD,
    FilterOptions,
    HtmlExtractOptions,
    ImageExtractOptions,
    PdfExtractOptions,
    PptxExtractOptions,
    SplitOptions,
    TextExtractOptions,
)
from .task_config import DEFAULT_TASK_CONFIG, DEFAULT_TASK_CONFIG_JSON, TaskConfig

__all__ = [
    # Document types
    "DocumentType",
    "EXTENSION_TO_DOCUMENT_TYPE",
    "DEFAULT_EXTRACT_METHOD",
    # Extraction options
    "ExtractOptions",
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
    "TaskConfig",
    "DEFAULT_TASK_CONFIG",
    "DEFAULT_TASK_CONFIG_JSON",
]
