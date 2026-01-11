"""Extraction and embedding options dataclasses."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Literal, Optional


class DocumentType(str, Enum):
    """Supported document types."""

    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    TEXT = "text"
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    SVG = "svg"
    MP3 = "mp3"
    WAV = "wav"


# Maps file extensions to document types
EXTENSION_TO_DOCUMENT_TYPE = {
    "pdf": DocumentType.PDF,
    "docx": DocumentType.DOCX,
    "pptx": DocumentType.PPTX,
    "html": DocumentType.HTML,
    "txt": DocumentType.TEXT,
    "md": DocumentType.TEXT,
    "json": DocumentType.TEXT,
    "sh": DocumentType.TEXT,
    "jpeg": DocumentType.JPEG,
    "jpg": DocumentType.JPEG,
    "png": DocumentType.PNG,
    "bmp": DocumentType.BMP,
    "tiff": DocumentType.TIFF,
    "svg": DocumentType.SVG,
    "mp3": DocumentType.MP3,
    "wav": DocumentType.WAV,
}

# Default extraction methods per document type
DEFAULT_EXTRACT_METHOD = {
    DocumentType.PDF: "pdfium",
    DocumentType.DOCX: "python_docx",
    DocumentType.PPTX: "python_pptx",
    DocumentType.HTML: "markitdown",
    DocumentType.TEXT: "txt",
    DocumentType.JPEG: "image",
    DocumentType.PNG: "image",
    DocumentType.BMP: "image",
    DocumentType.TIFF: "image",
    DocumentType.SVG: "image",
    DocumentType.MP3: "audio",
    DocumentType.WAV: "audio",
}


@dataclass
class EmbedOptions:
    """Configuration for text embedding."""

    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    filter_errors: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbedOptions":
        return cls(
            endpoint_url=data.get("endpoint_url"),
            model_name=data.get("model_name"),
            api_key=data.get("api_key"),
            filter_errors=data.get("filter_errors", False),
        )


@dataclass
class PdfExtractOptions:
    """Configuration for PDF extraction."""

    extract_method: Literal[
        "pdfium",
        "pdfium_hybrid",
        "adobe",
        "nemotron_parse",
        "haystack",
        "llama_parse",
        "tika",
        "unstructured_io",
        "unstructured_local",
        "ocr",
    ] = "pdfium"
    text_depth: Literal["document", "page"] = "document"
    extract_text: bool = True
    extract_images: bool = True
    extract_images_method: Literal["group", "yolox"] = "group"
    extract_tables: bool = True
    extract_tables_method: Literal["yolox", "paddle"] = "yolox"
    extract_charts: bool = True
    extract_infographics: bool = False
    extract_page_as_image: bool = False
    table_output_format: Literal["markdown", "html", "json"] = "markdown"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PdfExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "pdfium"),
            text_depth=data.get("text_depth", "document"),
            extract_text=data.get("extract_text", True),
            extract_images=data.get("extract_images", True),
            extract_images_method=data.get("extract_images_method", "group"),
            extract_tables=data.get("extract_tables", True),
            extract_tables_method=data.get("extract_tables_method", "yolox"),
            extract_charts=data.get("extract_charts", True),
            extract_infographics=data.get("extract_infographics", False),
            extract_page_as_image=data.get("extract_page_as_image", False),
            table_output_format=data.get("table_output_format", "markdown"),
        )


@dataclass
class DocxExtractOptions:
    """Configuration for DOCX extraction."""

    extract_method: Literal["python_docx", "render_as_pdf"] = "python_docx"
    text_depth: Literal["document", "page"] = "document"
    extract_text: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    extract_charts: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocxExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "python_docx"),
            text_depth=data.get("text_depth", "document"),
            extract_text=data.get("extract_text", True),
            extract_images=data.get("extract_images", True),
            extract_tables=data.get("extract_tables", True),
            extract_charts=data.get("extract_charts", True),
        )


@dataclass
class PptxExtractOptions:
    """Configuration for PPTX extraction."""

    extract_method: Literal["python_pptx", "render_as_pdf"] = "python_pptx"
    text_depth: Literal["document", "page"] = "document"
    extract_text: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    extract_charts: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PptxExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "python_pptx"),
            text_depth=data.get("text_depth", "document"),
            extract_text=data.get("extract_text", True),
            extract_images=data.get("extract_images", True),
            extract_tables=data.get("extract_tables", True),
            extract_charts=data.get("extract_charts", True),
        )


@dataclass
class ImageExtractOptions:
    """Configuration for image extraction (JPEG, PNG, BMP, TIFF, SVG)."""

    extract_method: str = "image"
    extract_text: bool = True  # OCR

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "image"),
            extract_text=data.get("extract_text", True),
        )


@dataclass
class TextExtractOptions:
    """Configuration for text file extraction (TXT, MD, JSON, SH)."""

    extract_method: str = "txt"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "txt"),
        )


@dataclass
class HtmlExtractOptions:
    """Configuration for HTML extraction."""

    extract_method: str = "markitdown"
    extract_text: bool = True
    extract_images: bool = True
    extract_tables: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HtmlExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "markitdown"),
            extract_text=data.get("extract_text", True),
            extract_images=data.get("extract_images", True),
            extract_tables=data.get("extract_tables", True),
        )


@dataclass
class AudioExtractOptions:
    """Configuration for audio extraction (MP3, WAV)."""

    extract_method: str = "audio"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudioExtractOptions":
        return cls(
            extract_method=data.get("extract_method", "audio"),
        )


@dataclass
class CaptionOptions:
    """Configuration for image captioning."""

    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    prompt: str = "Caption the content of this image:"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaptionOptions":
        return cls(
            endpoint_url=data.get("endpoint_url"),
            model_name=data.get("model_name"),
            api_key=data.get("api_key"),
            prompt=data.get("prompt", "Caption the content of this image:"),
        )


@dataclass
class SplitOptions:
    """Configuration for text splitting/chunking."""

    split_by: Literal["page", "size", "word", "sentence"] = "sentence"
    split_length: int = 512
    split_overlap: int = 50
    max_character_length: Optional[int] = None
    sentence_window_size: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SplitOptions":
        return cls(
            split_by=data.get("split_by", "sentence"),
            split_length=data.get("split_length", 512),
            split_overlap=data.get("split_overlap", 50),
            max_character_length=data.get("max_character_length"),
            sentence_window_size=data.get("sentence_window_size"),
        )


@dataclass
class FilterOptions:
    """Configuration for image filtering."""

    content_type: str = "image"
    filter: bool = False
    min_size: int = 128
    max_aspect_ratio: float = 5.0
    min_aspect_ratio: float = 0.2

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterOptions":
        return cls(
            content_type=data.get("content_type", "image"),
            filter=data.get("filter", False),
            min_size=data.get("min_size", 128),
            max_aspect_ratio=data.get("max_aspect_ratio", 5.0),
            min_aspect_ratio=data.get("min_aspect_ratio", 0.2),
        )


@dataclass
class DedupOptions:
    """Configuration for deduplication."""

    content_type: str = "image"
    filter: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DedupOptions":
        return cls(
            content_type=data.get("content_type", "image"),
            filter=data.get("filter", False),
        )


# Type alias for any extraction options
ExtractOptions = (
    PdfExtractOptions
    | DocxExtractOptions
    | PptxExtractOptions
    | ImageExtractOptions
    | TextExtractOptions
    | HtmlExtractOptions
    | AudioExtractOptions
)
