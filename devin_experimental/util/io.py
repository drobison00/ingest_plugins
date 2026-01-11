"""I/O utilities for file handling and result writing."""

import json
import os
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from nv_ingest_api.internal.primitives.ingest_control_message import IngestControlMessage


@dataclass
class FileInput:
    """
    Represents a file input for processing.

    Supports multiple input sources: file path, raw bytes, or BytesIO buffer.
    """

    path: Optional[str] = None
    data: Optional[bytes] = None
    buffer: Optional[BytesIO] = None
    name: Optional[str] = None

    def get_bytes(self) -> bytes:
        """Get the file content as bytes."""
        if self.data is not None:
            return self.data
        if self.buffer is not None:
            self.buffer.seek(0)
            return self.buffer.read()
        if self.path is not None:
            with open(self.path, "rb") as f:
                return f.read()
        raise ValueError("FileInput has no data source")

    def get_name(self) -> str:
        """Get the file name."""
        if self.name:
            return self.name
        if self.path:
            return os.path.basename(self.path)
        return "unknown"


def write_results_to_directory(output_directory: str, control_message: IngestControlMessage) -> None:
    """
    Write control message results to an output directory, organized by document type.

    Parameters
    ----------
    output_directory : str
        Directory to write results to.
    control_message : IngestControlMessage
        The control message containing results.
    """
    df = control_message.payload()
    if df is None or len(df) == 0:
        return

    keep_cols = []
    for col in ("document_type", "metadata"):
        if col in df.columns:
            keep_cols.append(col)

    if not keep_cols:
        return

    records = df[keep_cols].to_dict(orient="records")
    if not records:
        return

    first_meta = records[0].get("metadata") if isinstance(records[0], dict) else None
    source_id = None
    if isinstance(first_meta, dict):
        source_meta = first_meta.get("source_metadata")
        if isinstance(source_meta, dict):
            source_id = source_meta.get("source_id")

    if not source_id:
        source_id = control_message.get_metadata("job_id") or "unknown_source"

    clean_doc_name = os.path.basename(str(source_id))
    output_name = f"{clean_doc_name}.metadata.json"

    doc_map = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        doc_type = rec.get("document_type") or "unknown"
        meta = rec.get("metadata")
        if isinstance(meta, dict):
            content_meta = meta.get("content_metadata")
            if isinstance(content_meta, dict):
                doc_type = content_meta.get("type") or doc_type

        doc_map.setdefault(str(doc_type), []).append(rec)

    for doc_type, documents in doc_map.items():
        doc_type_path = os.path.join(output_directory, doc_type)
        os.makedirs(doc_type_path, exist_ok=True)
        with open(os.path.join(doc_type_path, output_name), "w") as f:
            f.write(json.dumps(documents, indent=2, default=repr))
