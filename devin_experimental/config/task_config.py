"""Task configuration for processing jobs."""

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .options import EmbedOptions, PdfExtractOptions


@dataclass
class TaskConfig:
    """Configuration for processing tasks, loadable from JSON."""

    extract: Optional[PdfExtractOptions] = None
    embed: Optional[EmbedOptions] = None
    enable_tracing: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        extract_opts = None
        embed_opts = None

        if "extract" in data:
            extract_opts = PdfExtractOptions.from_dict(data["extract"])
        if "embed" in data:
            embed_opts = EmbedOptions.from_dict(data["embed"])

        return cls(
            extract=extract_opts,
            embed=embed_opts,
            enable_tracing=data.get("enable_tracing", True),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "TaskConfig":
        """Load TaskConfig from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, path: str) -> "TaskConfig":
        """Load TaskConfig from a JSON file."""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskConfig to a dictionary."""
        result: Dict[str, Any] = {"enable_tracing": self.enable_tracing}
        if self.extract:
            result["extract"] = asdict(self.extract)
        if self.embed:
            result["embed"] = asdict(self.embed)
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert TaskConfig to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# Default configuration with all processing enabled
DEFAULT_TASK_CONFIG = TaskConfig(
    extract=PdfExtractOptions(
        extract_method="pdfium",
        text_depth="document",
        extract_text=True,
        extract_images=True,
        extract_images_method="group",
        extract_tables=True,
        extract_tables_method="yolox",
        extract_charts=True,
        extract_infographics=False,
        extract_page_as_image=False,
        table_output_format="markdown",
    ),
    embed=EmbedOptions(
        endpoint_url=None,
        model_name=None,
        filter_errors=False,
    ),
    enable_tracing=True,
)

# JSON representation of the default config
DEFAULT_TASK_CONFIG_JSON = """{
  "extract": {
    "extract_method": "pdfium",
    "text_depth": "document",
    "extract_text": true,
    "extract_images": true,
    "extract_images_method": "group",
    "extract_tables": true,
    "extract_tables_method": "yolox",
    "extract_charts": true,
    "extract_infographics": false,
    "extract_page_as_image": false,
    "table_output_format": "markdown"
  },
  "embed": {
    "endpoint_url": null,
    "model_name": null,
    "api_key": null,
    "filter_errors": false
  },
  "enable_tracing": true
}"""
