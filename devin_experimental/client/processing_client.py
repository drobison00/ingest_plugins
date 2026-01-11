"""Processing client for submitting work to the pipeline."""

import asyncio
import glob
import os
import time
import uuid
from dataclasses import dataclass
from io import BytesIO
from typing import AsyncGenerator, Callable, Dict, List, Optional, Sequence, Tuple, Union

import ray
from tqdm import tqdm

from nv_ingest_api.internal.primitives.ingest_control_message import IngestControlMessage
from devin_experimental.config import (
    AudioExtractOptions,
    CaptionOptions,
    DocxExtractOptions,
    DocumentType,
    EmbedOptions,
    EXTENSION_TO_DOCUMENT_TYPE,
    FilterOptions,
    HtmlExtractOptions,
    ImageExtractOptions,
    PdfExtractOptions,
    PptxExtractOptions,
    SplitOptions,
    TaskConfig,
)
from devin_experimental.internal.message_builder import ControlMessageBuilder, ExtractOptions
from devin_experimental.util.io import FileInput


@dataclass(frozen=True)
class SubmittedJob:
    """Represents a submitted processing job."""

    job_id: str
    file_name: Optional[str]


class ProcessingClient:
    """
    Client for submitting files to an NV-Ingest pipeline.

    This client handles file submission, progress tracking, and result collection.
    It provides both low-level control message APIs and high-level file processing APIs.

    Example
    -------
    >>> client = ProcessingClient(source=source_actor, sink=sink_actor)
    >>> results = client.process_pdf_files("/data/*.pdf", task_config=DEFAULT_TASK_CONFIG)
    """

    def __init__(
        self,
        *,
        source: "ray.actor.ActorHandle",
        sink: "ray.actor.ActorHandle",
        inflight: int = 32,
        submit_batch: int = 32,
        recv_batch: int = 32,
        poll_interval_s: float = 0.01,
        job_id_metadata_key: str = "client_job_uuid",
        show_progress: bool = False,
        progress_desc: str = "jobs",
        progress_unit: str = "job",
    ) -> None:
        """
        Initialize the ProcessingClient.

        Parameters
        ----------
        source : ray.actor.ActorHandle
            The source stage actor to submit work to.
        sink : ray.actor.ActorHandle
            The sink stage actor to receive results from.
        inflight : int
            Maximum number of in-flight jobs.
        submit_batch : int
            Batch size for submissions.
        recv_batch : int
            Batch size for receiving results.
        poll_interval_s : float
            Polling interval in seconds.
        job_id_metadata_key : str
            Metadata key for job ID tracking.
        show_progress : bool
            Whether to show a progress bar.
        progress_desc : str
            Description for the progress bar.
        progress_unit : str
            Unit label for the progress bar.
        """
        self._source = source
        self._sink = sink
        self._inflight_limit = max(1, int(inflight))
        self._submit_batch = max(1, int(submit_batch))
        self._recv_batch = max(1, int(recv_batch))
        self._poll_interval_s = max(0.0, float(poll_interval_s))
        self._job_id_metadata_key = job_id_metadata_key
        self._show_progress = show_progress
        self._progress_desc = progress_desc
        self._progress_unit = progress_unit

        self.job_id_to_file_name: Dict[str, str] = {}
        self.job_id_to_metadata: Dict[str, dict] = {}

        self._submitted_job_ids: List[str] = []
        self._received_by_job_id: Dict[str, IngestControlMessage] = {}
        self._pbar: Optional[tqdm] = None
        self._start_time: Optional[float] = None

    def submit(
        self,
        control_messages: Sequence[IngestControlMessage],
        *,
        file_names: Optional[Sequence[Optional[str]]] = None,
        job_metadata: Optional[Sequence[Optional[dict]]] = None,
    ) -> List[SubmittedJob]:
        """Submit control messages to the pipeline."""
        if file_names is not None and len(file_names) != len(control_messages):
            raise ValueError("file_names must match length of control_messages")
        if job_metadata is not None and len(job_metadata) != len(control_messages):
            raise ValueError("job_metadata must match length of control_messages")

        submitted_jobs: List[SubmittedJob] = []

        prepared: List[Tuple[str, IngestControlMessage, Optional[str], Optional[dict]]] = []
        for i, cm in enumerate(control_messages):
            file_name = file_names[i] if file_names is not None else None
            meta = job_metadata[i] if job_metadata is not None else None

            job_id = cm.get_metadata(self._job_id_metadata_key)
            if not job_id:
                job_id = str(uuid.uuid4())
                cm.set_metadata(self._job_id_metadata_key, job_id)

            if file_name:
                self.job_id_to_file_name[job_id] = file_name
            if meta:
                self.job_id_to_metadata[job_id] = meta

            prepared.append((job_id, cm, file_name, meta))

        idx = 0
        while idx < len(prepared):
            self._drain_available(max_items=self._recv_batch)

            inflight = len(self._submitted_job_ids) - len(self._received_by_job_id)
            if inflight >= self._inflight_limit:
                time.sleep(self._poll_interval_s)
                continue

            capacity = min(self._inflight_limit - inflight, len(prepared) - idx)
            batch_size = min(self._submit_batch, capacity)
            batch = prepared[idx : idx + batch_size]

            accepted = ray.get(
                self._source.submit_many.remote([cm for _job_id, cm, _fn, _meta in batch], block=False, timeout_s=0.0)
            )
            if accepted <= 0:
                time.sleep(self._poll_interval_s)
                continue

            for j in range(accepted):
                job_id, _cm, file_name, _meta = batch[j]
                self._submitted_job_ids.append(job_id)
                submitted_jobs.append(SubmittedJob(job_id=job_id, file_name=file_name))

            idx += accepted

        return submitted_jobs

    def fetch(
        self,
        *,
        timeout_s: Optional[float] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
        progress_value_fn: Optional[Callable[[IngestControlMessage], int]] = None,
    ) -> List[IngestControlMessage]:
        """Fetch results from the pipeline."""
        deadline = None
        if timeout_s is not None:
            deadline = time.perf_counter() + float(timeout_s)

        if self._start_time is None:
            self._start_time = time.perf_counter()

        while len(self._received_by_job_id) < len(self._submitted_job_ids):
            remaining = len(self._submitted_job_ids) - len(self._received_by_job_id)
            batch = min(self._recv_batch, remaining)

            wait_timeout = 0.05
            if deadline is not None:
                remaining_time = deadline - time.perf_counter()
                if remaining_time <= 0:
                    break
                wait_timeout = min(wait_timeout, remaining_time)

            items = ray.get(self._sink.get_many.remote(batch, timeout_s=wait_timeout))
            if not items:
                continue

            progress_delta = 0
            for cm in items:
                if not isinstance(cm, IngestControlMessage):
                    continue
                job_id = cm.get_metadata(self._job_id_metadata_key)
                if job_id:
                    self._received_by_job_id[job_id] = cm
                    if on_result:
                        on_result(cm)
                    if progress_value_fn:
                        progress_delta += progress_value_fn(cm)
                    else:
                        progress_delta += 1

            self._update_progress(progress_delta)

        results: List[IngestControlMessage] = []
        for job_id in self._submitted_job_ids:
            cm = self._received_by_job_id.get(job_id)
            if cm is not None:
                results.append(cm)
        return results

    async def fetch_as_available(self) -> AsyncGenerator[IngestControlMessage, None]:
        """Asynchronously yield results as they become available."""
        remaining = len(self._submitted_job_ids) - len(self._received_by_job_id)
        while remaining > 0:
            cm = await asyncio.to_thread(self._get_next_result_blocking, 0.05)
            if cm is None:
                remaining = len(self._submitted_job_ids) - len(self._received_by_job_id)
                continue

            job_id = cm.get_metadata(self._job_id_metadata_key)
            if job_id:
                self._received_by_job_id[job_id] = cm

            remaining = len(self._submitted_job_ids) - len(self._received_by_job_id)
            yield cm

    def _get_next_result_blocking(self, timeout_s: float) -> Optional[IngestControlMessage]:
        item = ray.get(self._sink.get_next.remote(timeout_s=timeout_s))
        if isinstance(item, IngestControlMessage):
            return item
        return None

    def _drain_available(self, *, max_items: int) -> None:
        items = ray.get(self._sink.get_many.remote(max_items, timeout_s=0.0))
        if not items:
            return
        for cm in items:
            if not isinstance(cm, IngestControlMessage):
                continue
            job_id = cm.get_metadata(self._job_id_metadata_key)
            if job_id:
                self._received_by_job_id[job_id] = cm

    def start_progress(self, total: int) -> None:
        """Initialize tqdm progress bar if show_progress is enabled."""
        if self._show_progress:
            self._pbar = tqdm(total=total, desc=self._progress_desc, unit=self._progress_unit)
        self._start_time = time.perf_counter()

    def _update_progress(self, delta: int) -> None:
        if self._pbar is not None and delta > 0:
            self._pbar.update(delta)
            elapsed = time.perf_counter() - (self._start_time or time.perf_counter())
            rate = (self._pbar.n / elapsed) if elapsed > 0 else 0.0
            inflight = len(self._submitted_job_ids) - len(self._received_by_job_id)
            self._pbar.set_postfix({f"{self._progress_unit}/sec": f"{rate:.1f}", "inflight": inflight})

    def close_progress(self) -> None:
        """Close the tqdm progress bar."""
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None

    @property
    def submitted_count(self) -> int:
        return len(self._submitted_job_ids)

    @property
    def received_count(self) -> int:
        return len(self._received_by_job_id)

    @property
    def elapsed(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.perf_counter() - self._start_time

    # -------------------------------------------------------------------------
    # High-level file processing API
    # -------------------------------------------------------------------------

    def submit_files(
        self,
        files: Sequence[Union[str, bytes, BytesIO, FileInput]],
        *,
        document_type: Optional[DocumentType] = None,
        task_config: Optional[TaskConfig] = None,
        extract_options: Optional[ExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        caption_options: Optional[CaptionOptions] = None,
        split_options: Optional[SplitOptions] = None,
        filter_options: Optional[FilterOptions] = None,
        page_count_fn: Optional[Callable[[bytes], int]] = None,
    ) -> List[SubmittedJob]:
        """
        Build control messages from file inputs and submit them for processing.

        Parameters
        ----------
        files : Sequence[Union[str, bytes, BytesIO, FileInput]]
            List of file inputs (paths, bytes, BytesIO, or FileInput).
        document_type : Optional[DocumentType]
            Document type (auto-detected from extension if not provided).
        task_config : Optional[TaskConfig]
            Task configuration (overrides other options).
        extract_options : Optional[ExtractOptions]
            Extraction options for the document type.
        embed_options : Optional[EmbedOptions]
            Embedding options.
        caption_options : Optional[CaptionOptions]
            Image captioning options.
        split_options : Optional[SplitOptions]
            Text splitting/chunking options.
        filter_options : Optional[FilterOptions]
            Image filtering options.
        page_count_fn : Optional[Callable[[bytes], int]]
            Function to count pages for progress tracking.
        """
        if task_config is not None:
            extract_options = task_config.extract
            embed_options = task_config.embed
            enable_tracing = task_config.enable_tracing
        else:
            enable_tracing = True

        builder = ControlMessageBuilder(enable_tracing=enable_tracing)

        control_messages: List[IngestControlMessage] = []
        job_metadata_list: List[Optional[dict]] = []
        file_names: List[Optional[str]] = []

        for i, file_input in enumerate(files):
            if isinstance(file_input, str):
                fi = FileInput(path=file_input)
            elif isinstance(file_input, bytes):
                fi = FileInput(data=file_input, name=f"file_{i}")
            elif isinstance(file_input, BytesIO):
                fi = FileInput(buffer=file_input, name=f"file_{i}")
            elif isinstance(file_input, FileInput):
                fi = file_input
            else:
                raise TypeError(f"Unsupported file input type: {type(file_input)}")

            file_bytes = fi.get_bytes()
            file_name = fi.get_name()
            source_id = fi.path or file_name

            # Auto-detect document type from file extension if not provided
            file_doc_type = document_type
            if file_doc_type is None:
                ext = os.path.splitext(file_name)[1][1:].lower()
                file_doc_type = EXTENSION_TO_DOCUMENT_TYPE.get(ext)
                if file_doc_type is None:
                    raise ValueError(f"Unknown file extension: {ext}. Specify document_type explicitly.")

            cm = builder.build_from_bytes(
                file_bytes,
                document_type=file_doc_type,
                name=file_name,
                extract_options=extract_options,
                embed_options=embed_options,
                caption_options=caption_options,
                split_options=split_options,
                filter_options=filter_options,
                source_name=file_name,
                source_id=f"{source_id}#{i}",
            )
            control_messages.append(cm)
            file_names.append(file_name)

            meta = None
            if page_count_fn:
                try:
                    pages = page_count_fn(file_bytes)
                    meta = {"pages": pages}
                except Exception:
                    meta = {"pages": 1}
            job_metadata_list.append(meta)

        return self.submit(
            control_messages,
            file_names=file_names,
            job_metadata=job_metadata_list,
        )

    def process_files(
        self,
        files: Sequence[Union[str, bytes, BytesIO, FileInput]],
        *,
        document_type: Optional[DocumentType] = None,
        task_config: Optional[TaskConfig] = None,
        extract_options: Optional[ExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        caption_options: Optional[CaptionOptions] = None,
        split_options: Optional[SplitOptions] = None,
        filter_options: Optional[FilterOptions] = None,
        page_count_fn: Optional[Callable[[bytes], int]] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """
        Submit files and wait for all results.

        This is a convenience method that combines submit_files() and fetch().
        Supports all document types with auto-detection from file extension.
        """
        if self._show_progress and page_count_fn:
            total = 0
            for file_input in files:
                if isinstance(file_input, str):
                    fi = FileInput(path=file_input)
                elif isinstance(file_input, bytes):
                    fi = FileInput(data=file_input)
                elif isinstance(file_input, BytesIO):
                    fi = FileInput(buffer=file_input)
                elif isinstance(file_input, FileInput):
                    fi = file_input
                else:
                    continue
                try:
                    total += page_count_fn(fi.get_bytes())
                except Exception:
                    total += 1
            self.start_progress(total)
        elif self._show_progress:
            self.start_progress(len(files))

        try:
            self.submit_files(
                files,
                document_type=document_type,
                task_config=task_config,
                extract_options=extract_options,
                embed_options=embed_options,
                caption_options=caption_options,
                split_options=split_options,
                filter_options=filter_options,
                page_count_fn=page_count_fn,
            )

            def progress_value_fn(cm: IngestControlMessage) -> int:
                if page_count_fn:
                    job_id = cm.get_metadata(self._job_id_metadata_key)
                    meta = self.job_id_to_metadata.get(job_id)
                    if meta:
                        return meta.get("pages", 1)
                return 1

            return self.fetch(
                on_result=on_result,
                progress_value_fn=progress_value_fn if page_count_fn else None,
            )
        finally:
            self.close_progress()

    @staticmethod
    def expand_file_pattern(
        pattern: str,
        *,
        extensions: Optional[List[str]] = None,
        repeat_to: Optional[int] = None,
    ) -> List[str]:
        """Expand a glob pattern to a list of file paths."""
        matched = glob.glob(pattern, recursive=True)
        if not matched and os.path.exists(pattern):
            matched = [pattern]

        if extensions:
            ext_lower = [e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions]
            matched = [p for p in matched if os.path.isfile(p) and os.path.splitext(p)[1].lower() in ext_lower]
        else:
            matched = [p for p in matched if os.path.isfile(p)]

        matched = sorted(matched)

        if repeat_to and matched:
            matched = (matched * ((repeat_to // len(matched)) + 1))[:repeat_to]

        return matched

    def process_pdf_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        task_config: Optional[TaskConfig] = None,
        extract_options: Optional[PdfExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        page_count_fn: Optional[Callable[[bytes], int]] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """
        Process PDF files matching a glob pattern or from a list of paths.

        Parameters
        ----------
        pattern_or_files : Union[str, Sequence[str]]
            Glob pattern (str) or list of file paths.
        repeat_to : Optional[int]
            Repeat files to reach this count.
        task_config : Optional[TaskConfig]
            Task configuration.
        extract_options : Optional[PdfExtractOptions]
            PDF extraction options.
        embed_options : Optional[EmbedOptions]
            Embedding options.
        page_count_fn : Optional[Callable[[bytes], int]]
            Function to count pages for progress tracking.
        on_result : Optional[Callable[[IngestControlMessage], None]]
            Callback for each result.
        """
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(
                pattern_or_files,
                extensions=[".pdf"],
                repeat_to=repeat_to,
            )
            if not files:
                raise RuntimeError(f"No PDF files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            document_type=DocumentType.PDF,
            task_config=task_config,
            extract_options=extract_options,
            embed_options=embed_options,
            page_count_fn=page_count_fn,
            on_result=on_result,
        )

    def process_docx_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        extract_options: Optional[DocxExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process DOCX files matching a glob pattern or from a list of paths."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(pattern_or_files, extensions=[".docx"], repeat_to=repeat_to)
            if not files:
                raise RuntimeError(f"No DOCX files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            document_type=DocumentType.DOCX,
            extract_options=extract_options,
            embed_options=embed_options,
            on_result=on_result,
        )

    def process_pptx_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        extract_options: Optional[PptxExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process PPTX files matching a glob pattern or from a list of paths."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(pattern_or_files, extensions=[".pptx"], repeat_to=repeat_to)
            if not files:
                raise RuntimeError(f"No PPTX files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            document_type=DocumentType.PPTX,
            extract_options=extract_options,
            embed_options=embed_options,
            on_result=on_result,
        )

    def process_image_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        extract_options: Optional[ImageExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        caption_options: Optional[CaptionOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process image files (JPEG, PNG, BMP, TIFF) matching a glob pattern."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(
                pattern_or_files, extensions=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"], repeat_to=repeat_to
            )
            if not files:
                raise RuntimeError(f"No image files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            extract_options=extract_options,
            embed_options=embed_options,
            caption_options=caption_options,
            on_result=on_result,
        )

    def process_text_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        embed_options: Optional[EmbedOptions] = None,
        split_options: Optional[SplitOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process text files (TXT, MD, JSON) matching a glob pattern."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(
                pattern_or_files, extensions=[".txt", ".md", ".json", ".sh"], repeat_to=repeat_to
            )
            if not files:
                raise RuntimeError(f"No text files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            document_type=DocumentType.TEXT,
            embed_options=embed_options,
            split_options=split_options,
            on_result=on_result,
        )

    def process_html_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        extract_options: Optional[HtmlExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process HTML files matching a glob pattern."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(pattern_or_files, extensions=[".html"], repeat_to=repeat_to)
            if not files:
                raise RuntimeError(f"No HTML files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            document_type=DocumentType.HTML,
            extract_options=extract_options,
            embed_options=embed_options,
            on_result=on_result,
        )

    def process_audio_files(
        self,
        pattern_or_files: Union[str, Sequence[str]],
        *,
        repeat_to: Optional[int] = None,
        extract_options: Optional[AudioExtractOptions] = None,
        embed_options: Optional[EmbedOptions] = None,
        on_result: Optional[Callable[[IngestControlMessage], None]] = None,
    ) -> List[IngestControlMessage]:
        """Process audio files (MP3, WAV) matching a glob pattern."""
        if isinstance(pattern_or_files, str):
            files = self.expand_file_pattern(pattern_or_files, extensions=[".mp3", ".wav"], repeat_to=repeat_to)
            if not files:
                raise RuntimeError(f"No audio files matched pattern: {pattern_or_files}")
        else:
            files = list(pattern_or_files)
            if repeat_to and files:
                files = (files * ((repeat_to // len(files)) + 1))[:repeat_to]

        return self.process_files(
            files,
            extract_options=extract_options,
            embed_options=embed_options,
            on_result=on_result,
        )
