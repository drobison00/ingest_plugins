# API Reference

## Pipeline Management

### `launch_pipeline(config_path: str)`

Launch an NV-Ingest pipeline from a YAML configuration file.

```python
interface = launch_pipeline("pipeline.yaml")
```

### `get_stage_actor(interface, stage_name: str)`

Get a Ray actor handle for a specific pipeline stage.

```python
source = get_stage_actor(interface, "source_stage")
sink = get_stage_actor(interface, "broker_response")
```

## Processing Client

### `ProcessingClient`

The main client for submitting work to the pipeline.

```python
client = ProcessingClient(
    source=source_actor,      # Source stage actor
    sink=sink_actor,          # Sink stage actor
    inflight=32,              # Max in-flight jobs
    show_progress=True,       # Show tqdm progress bar
    progress_desc="pages",    # Progress bar description
    progress_unit="page",     # Progress bar unit
)
```

### Document-Type Specific Methods

```python
# Process any files (auto-detects type from extension)
results = client.process_files("/data/*")

# PDF files
results = client.process_pdf_files("/data/*.pdf", task_config=config)

# Office documents
results = client.process_docx_files("/data/*.docx")
results = client.process_pptx_files("/data/*.pptx")

# Images (JPEG, PNG, BMP, TIFF)
results = client.process_image_files("/data/*.jpg", caption_options=caption_opts)

# Text files (TXT, MD, JSON)
results = client.process_text_files("/data/*.txt", split_options=split_opts)

# HTML files
results = client.process_html_files("/data/*.html")

# Audio files (MP3, WAV)
results = client.process_audio_files("/data/*.mp3")
```

### `client.process_pdf_files(pattern_or_files, ...)`

Process PDF files from a glob pattern or list of paths.

```python
# From glob pattern
results = client.process_pdf_files("/data/*.pdf", task_config=config)

# From list of paths
results = client.process_pdf_files(["/path/to/a.pdf", "/path/to/b.pdf"])

# Repeat files to reach N total jobs
results = client.process_pdf_files("/data/*.pdf", repeat_to=100)
```

### `client.process_files(files, ...)`

Process files from mixed input types (paths, bytes, BytesIO, FileInput).

```python
from io import BytesIO
from devin_experimental import FileInput

files = [
    "/path/to/file.pdf",                           # Path string
    pdf_bytes,                                      # Raw bytes
    BytesIO(pdf_bytes),                            # BytesIO buffer
    FileInput(data=pdf_bytes, name="custom.pdf"),  # Named bytes
]

results = client.process_files(files, task_config=config)
```
