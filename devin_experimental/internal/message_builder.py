"""Internal control message builder."""

import base64
import os
import time
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional, Tuple, Union

import pandas as pd

from nv_ingest_api.internal.primitives.control_message_task import ControlMessageTask
from nv_ingest_api.internal.primitives.ingest_control_message import IngestControlMessage
from devin_experimental.config import (
    AudioExtractOptions,
    CaptionOptions,
    DocxExtractOptions,
    DocumentType,
    EmbedOptions,
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

# Type alias for any extraction options
ExtractOptions = Union[
    PdfExtractOptions,
    DocxExtractOptions,
    PptxExtractOptions,
    ImageExtractOptions,
    TextExtractOptions,
    HtmlExtractOptions,
    AudioExtractOptions,
]


class ControlMessageBuilder:
    """Builds IngestControlMessage objects for pipeline submission."""

    def __init__(self, *, enable_tracing: bool = True) -> None:
        self._enable_tracing = enable_tracing

    # -------------------------------------------------------------------------
    # Generic builder (auto-detects document type from extension)
    # -------------------------------------------------------------------------

    def build_from_file(
        self,
        file_path: str,
        *,
        document_type: Optional[DocumentType] = None,
        extract_options: Optional[ExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        caption_options: Optional[CaptionOptions] = None,
        split_options: Optional[SplitOptions] = None,
        filter_options: Optional[FilterOptions] = None,
        source_name: Optional[str] = None,
        source_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> IngestControlMessage:
        """Build a control message from a file path, auto-detecting document type."""
        with open(file_path, "rb") as f:
            data = f.read()

        # Auto-detect document type from extension
        if document_type is None:
            ext = os.path.splitext(file_path)[1][1:].lower()
            document_type = EXTENSION_TO_DOCUMENT_TYPE.get(ext)
            if document_type is None:
                raise ValueError(f"Unknown file extension: {ext}")

        return self.build_from_bytes(
            data,
            document_type=document_type,
            name=source_name or os.path.basename(file_path),
            extract_options=extract_options,
            embed_options=embed_options,
            caption_options=caption_options,
            split_options=split_options,
            filter_options=filter_options,
            source_name=source_name or file_path,
            source_id=source_id or file_path,
            job_id=job_id,
        )

    def build_from_bytes(
        self,
        data: bytes,
        *,
        document_type: DocumentType,
        name: str = "document",
        extract_options: Optional[ExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        caption_options: Optional[CaptionOptions] = None,
        split_options: Optional[SplitOptions] = None,
        filter_options: Optional[FilterOptions] = None,
        source_name: Optional[str] = None,
        source_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> IngestControlMessage:
        """Build a control message from bytes for any document type."""
        # Create default options if not provided
        if extract_options is None:
            extract_options = self._get_default_extract_options(document_type)

        content_b64 = base64.b64encode(data).decode("utf-8")
        job_id_str = job_id or str(uuid.uuid4())
        client_job_uuid_str = str(uuid.uuid4())

        # Build payload
        job_payload = {
            "source_name": [source_name or name],
            "source_id": [source_id or name],
            "content": [content_b64],
            "document_type": [document_type.value],
        }
        df = pd.DataFrame(job_payload)

        # Build extract task properties
        task_properties = self._build_extract_task_properties(document_type, extract_options)

        # Create control message
        cm = IngestControlMessage()
        cm.payload(df)
        cm.set_metadata("response_channel", job_id_str)
        cm.set_metadata("job_id", job_id_str)
        cm.set_metadata("client_job_uuid", client_job_uuid_str)
        cm.set_metadata("timestamp", datetime.now().timestamp())

        # Add extract task
        cm.add_task(
            ControlMessageTask(
                id=str(uuid.uuid4()),
                type="extract",
                properties=task_properties,
            )
        )

        # Add table/chart extraction tasks for document types that support them
        if document_type in (DocumentType.PDF, DocumentType.DOCX, DocumentType.PPTX):
            if hasattr(extract_options, "extract_tables") and extract_options.extract_tables:
                cm.add_task(
                    ControlMessageTask(
                        id=str(uuid.uuid4()),
                        type="table_data_extract",
                        properties={"params": {}},
                    )
                )
            if hasattr(extract_options, "extract_charts") and extract_options.extract_charts:
                cm.add_task(
                    ControlMessageTask(
                        id=str(uuid.uuid4()),
                        type="chart_data_extract",
                        properties={"params": {}},
                    )
                )

        # Add caption task if options provided
        if caption_options is not None:
            cm.add_task(
                ControlMessageTask(
                    id=str(uuid.uuid4()),
                    type="caption",
                    properties=self._build_caption_task_properties(caption_options),
                )
            )

        # Add split task if options provided
        if split_options is not None:
            cm.add_task(
                ControlMessageTask(
                    id=str(uuid.uuid4()),
                    type="split",
                    properties=self._build_split_task_properties(split_options),
                )
            )

        # Add filter task if options provided
        if filter_options is not None:
            cm.add_task(
                ControlMessageTask(
                    id=str(uuid.uuid4()),
                    type="filter",
                    properties=self._build_filter_task_properties(filter_options),
                )
            )

        # Add embed task if options provided
        if embed_options is not None:
            cm.add_task(
                ControlMessageTask(
                    id=str(uuid.uuid4()),
                    type="embed",
                    properties=self._build_embed_task_properties(embed_options),
                )
            )

        # Add tracing metadata
        if self._enable_tracing:
            ts_entry = datetime.now()
            cm.set_metadata("config::add_trace_tagging", True)
            cm.set_timestamp("trace::entry::direct_submit", ts_entry)
            cm.set_timestamp("trace::exit::direct_submit", datetime.now())
            cm.set_timestamp("latency::ts_send", datetime.now())
            cm.set_metadata("tracing_options", {"trace": True, "ts_send": time.time_ns()})
        else:
            cm.set_metadata("config::add_trace_tagging", False)

        return cm

    # -------------------------------------------------------------------------
    # Legacy PDF-specific builders (for backward compatibility)
    # -------------------------------------------------------------------------

    def build_pdf_text_extract_from_path(
        self,
        file_path: str,
        *,
        source_name: Optional[str] = None,
        source_id: Optional[str] = None,
        job_id: Optional[str] = None,
        client_job_uuid: Optional[str] = None,
        options: Optional[PdfExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
    ) -> IngestControlMessage:
        """Build a control message from a PDF file path (legacy method)."""
        return self.build_from_file(
            file_path,
            document_type=DocumentType.PDF,
            extract_options=options,
            embed_options=embed_options,
            source_name=source_name,
            source_id=source_id,
            job_id=job_id,
        )

    def build_pdf_text_extract_from_bytes(
        self,
        name: str,
        data: bytes,
        *,
        source_name: Optional[str] = None,
        source_id: Optional[str] = None,
        job_id: Optional[str] = None,
        client_job_uuid: Optional[str] = None,
        options: Optional[PdfExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
    ) -> IngestControlMessage:
        """Build a control message from PDF bytes (legacy method)."""
        return self.build_from_bytes(
            data,
            document_type=DocumentType.PDF,
            name=name,
            extract_options=options,
            embed_options=embed_options,
            source_name=source_name,
            source_id=source_id,
            job_id=job_id,
        )

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _get_default_extract_options(self, document_type: DocumentType) -> ExtractOptions:
        """Get default extraction options for a document type."""
        if document_type == DocumentType.PDF:
            return PdfExtractOptions()
        elif document_type == DocumentType.DOCX:
            return DocxExtractOptions()
        elif document_type == DocumentType.PPTX:
            return PptxExtractOptions()
        elif document_type == DocumentType.HTML:
            return HtmlExtractOptions()
        elif document_type == DocumentType.TEXT:
            return TextExtractOptions()
        elif document_type in (
            DocumentType.JPEG,
            DocumentType.PNG,
            DocumentType.BMP,
            DocumentType.TIFF,
            DocumentType.SVG,
        ):
            return ImageExtractOptions()
        elif document_type in (DocumentType.MP3, DocumentType.WAV):
            return AudioExtractOptions()
        else:
            raise ValueError(f"Unknown document type: {document_type}")

    def _build_extract_task_properties(self, document_type: DocumentType, options: ExtractOptions) -> Dict[str, Any]:
        """Build extract task properties from options."""
        method = getattr(options, "extract_method", DEFAULT_EXTRACT_METHOD.get(document_type, "pdfium"))

        params: Dict[str, Any] = {}

        # Common params
        if hasattr(options, "extract_text"):
            params["extract_text"] = options.extract_text
        if hasattr(options, "text_depth"):
            params["text_depth"] = options.text_depth

        # Image extraction params
        if hasattr(options, "extract_images"):
            params["extract_images"] = options.extract_images
        if hasattr(options, "extract_images_method"):
            params["extract_images_method"] = options.extract_images_method

        # Table extraction params
        if hasattr(options, "extract_tables"):
            params["extract_tables"] = options.extract_tables
        if hasattr(options, "extract_tables_method"):
            params["extract_tables_method"] = options.extract_tables_method
        if hasattr(options, "table_output_format"):
            params["table_output_format"] = options.table_output_format

        # Chart extraction params
        if hasattr(options, "extract_charts"):
            params["extract_charts"] = options.extract_charts

        # Other params
        if hasattr(options, "extract_infographics"):
            params["extract_infographics"] = options.extract_infographics
        if hasattr(options, "extract_page_as_image"):
            params["extract_page_as_image"] = options.extract_page_as_image

        return {
            "method": method,
            "document_type": document_type.value,
            "params": params,
        }

    def _build_embed_task_properties(self, embed_options: EmbedOptions) -> Dict[str, Any]:
        """Build embed task properties."""
        props: Dict[str, Any] = {"filter_errors": embed_options.filter_errors}
        if embed_options.endpoint_url:
            props["endpoint_url"] = embed_options.endpoint_url
        if embed_options.model_name:
            props["model_name"] = embed_options.model_name
        if embed_options.api_key:
            props["api_key"] = embed_options.api_key
        return props

    def _build_caption_task_properties(self, caption_options: CaptionOptions) -> Dict[str, Any]:
        """Build caption task properties."""
        props: Dict[str, Any] = {"prompt": caption_options.prompt}
        if caption_options.endpoint_url:
            props["endpoint_url"] = caption_options.endpoint_url
        if caption_options.model_name:
            props["model_name"] = caption_options.model_name
        if caption_options.api_key:
            props["api_key"] = caption_options.api_key
        return props

    def _build_split_task_properties(self, split_options: SplitOptions) -> Dict[str, Any]:
        """Build split task properties."""
        props: Dict[str, Any] = {
            "split_by": split_options.split_by,
            "split_length": split_options.split_length,
            "split_overlap": split_options.split_overlap,
        }
        if split_options.max_character_length is not None:
            props["max_character_length"] = split_options.max_character_length
        if split_options.sentence_window_size is not None:
            props["sentence_window_size"] = split_options.sentence_window_size
        return props

    def _build_filter_task_properties(self, filter_options: FilterOptions) -> Dict[str, Any]:
        """Build filter task properties."""
        return {
            "content_type": filter_options.content_type,
            "params": {
                "filter": filter_options.filter,
                "min_size": filter_options.min_size,
                "max_aspect_ratio": filter_options.max_aspect_ratio,
                "min_aspect_ratio": filter_options.min_aspect_ratio,
            },
        }

    def build_job_payload_from_buffer(
        self,
        name: str,
        buffer: BytesIO,
        *,
        document_type: str,
        source_name: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, str]:
        """Build a job payload DataFrame from a BytesIO buffer."""
        content_b64 = base64.b64encode(buffer.read()).decode("utf-8")
        job_payload = {
            "source_name": [source_name or name],
            "source_id": [source_id or name],
            "content": [content_b64],
            "document_type": [document_type],
        }
        return pd.DataFrame(job_payload), str(uuid.uuid4())
