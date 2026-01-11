"""Test that the devin_experimental plugin can be imported."""

import pytest


def test_import_devin_experimental():
    """Test that the main package can be imported."""
    import devin_experimental

    assert devin_experimental is not None


def test_import_public_api():
    """Test that all public API exports can be imported."""
    from devin_experimental import (
        # Document types
        DocumentType,
        EXTENSION_TO_DOCUMENT_TYPE,
        DEFAULT_EXTRACT_METHOD,
        # Extraction options
        PdfExtractOptions,
        DocxExtractOptions,
        PptxExtractOptions,
        ImageExtractOptions,
        TextExtractOptions,
        HtmlExtractOptions,
        AudioExtractOptions,
        # Processing options
        EmbedOptions,
        CaptionOptions,
        SplitOptions,
        FilterOptions,
        DedupOptions,
        # Task config
        DEFAULT_TASK_CONFIG,
        DEFAULT_TASK_CONFIG_JSON,
        TaskConfig,
        # Pipeline
        get_stage_actor,
        launch_pipeline,
        # Client
        ProcessingClient,
        SubmittedJob,
        # Utilities
        FileInput,
        get_pdf_page_count,
        write_results_to_directory,
        # Stages
        DirectSubmitSourceStage,
        OutputQueueSinkStage,
    )

    # Verify all imports are not None
    assert DocumentType is not None
    assert EXTENSION_TO_DOCUMENT_TYPE is not None
    assert DEFAULT_EXTRACT_METHOD is not None
    assert PdfExtractOptions is not None
    assert DocxExtractOptions is not None
    assert PptxExtractOptions is not None
    assert ImageExtractOptions is not None
    assert TextExtractOptions is not None
    assert HtmlExtractOptions is not None
    assert AudioExtractOptions is not None
    assert EmbedOptions is not None
    assert CaptionOptions is not None
    assert SplitOptions is not None
    assert FilterOptions is not None
    assert DedupOptions is not None
    assert DEFAULT_TASK_CONFIG is not None
    assert DEFAULT_TASK_CONFIG_JSON is not None
    assert TaskConfig is not None
    assert get_stage_actor is not None
    assert launch_pipeline is not None
    assert ProcessingClient is not None
    assert SubmittedJob is not None
    assert FileInput is not None
    assert get_pdf_page_count is not None
    assert write_results_to_directory is not None
    assert DirectSubmitSourceStage is not None
    assert OutputQueueSinkStage is not None


def test_all_exports_match():
    """Test that __all__ contains all expected exports."""
    import devin_experimental

    expected_exports = {
        "DocumentType",
        "EXTENSION_TO_DOCUMENT_TYPE",
        "DEFAULT_EXTRACT_METHOD",
        "PdfExtractOptions",
        "DocxExtractOptions",
        "PptxExtractOptions",
        "ImageExtractOptions",
        "TextExtractOptions",
        "HtmlExtractOptions",
        "AudioExtractOptions",
        "EmbedOptions",
        "CaptionOptions",
        "SplitOptions",
        "FilterOptions",
        "DedupOptions",
        "DEFAULT_TASK_CONFIG",
        "DEFAULT_TASK_CONFIG_JSON",
        "TaskConfig",
        "get_stage_actor",
        "launch_pipeline",
        "ProcessingClient",
        "SubmittedJob",
        "FileInput",
        "get_pdf_page_count",
        "write_results_to_directory",
        "DirectSubmitSourceStage",
        "OutputQueueSinkStage",
    }

    assert set(devin_experimental.__all__) == expected_exports
