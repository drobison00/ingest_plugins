# devin_experimental

A lightweight Python library for running in-process NV-Ingest pipelines with direct submission capabilities.

## Overview

This library provides a clean, simple interface for:

- **Launching** an NV-Ingest pipeline from a YAML configuration
- **Submitting** documents for processing (from file paths, bytes, or BytesIO)
- **Supporting** all document types: PDF, DOCX, PPTX, images, text, HTML, and audio
- **Collecting** results with progress tracking
- **Configuring** extraction, embedding, captioning, and splitting tasks

## Installation

```bash
cd scratch/devin_experimental
pip install -e .
```

## Quick Start

```python
from devin_experimental import (
    launch_pipeline,
    get_stage_actor,
    ProcessingClient,
    DEFAULT_TASK_CONFIG,
    get_pdf_page_count,
)

# 1. Launch the pipeline
interface = launch_pipeline("path/to/pipeline.yaml")

# 2. Get the source and sink actors
source = get_stage_actor(interface, "source_stage")
sink = get_stage_actor(interface, "broker_response")

# 3. Create a processing client
client = ProcessingClient(
    source=source,
    sink=sink,
    show_progress=True,
    progress_desc="pages",
    progress_unit="page",
)

# 4. Process PDF files
results = client.process_pdf_files(
    "/data/*.pdf",                      # Glob pattern or list of paths
    task_config=DEFAULT_TASK_CONFIG,    # Use default extraction config
    page_count_fn=get_pdf_page_count,   # For progress tracking
)

print(f"Processed {len(results)} documents")
```

## API Reference

### Pipeline Management

#### `launch_pipeline(config_path: str)`

Launch an NV-Ingest pipeline from a YAML configuration file.

```python
interface = launch_pipeline("pipeline.yaml")
```

#### `get_stage_actor(interface, stage_name: str)`

Get a Ray actor handle for a specific pipeline stage.

```python
source = get_stage_actor(interface, "source_stage")
sink = get_stage_actor(interface, "broker_response")
```

### Processing Client

#### `ProcessingClient`

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

#### Document-Type Specific Methods

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

#### `client.process_pdf_files(pattern_or_files, ...)`

Process PDF files from a glob pattern or list of paths.

```python
# From glob pattern
results = client.process_pdf_files("/data/*.pdf", task_config=config)

# From list of paths
results = client.process_pdf_files(["/path/to/a.pdf", "/path/to/b.pdf"])

# Repeat files to reach N total jobs
results = client.process_pdf_files("/data/*.pdf", repeat_to=100)
```

#### `client.process_files(files, ...)`

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

### Supported Document Types

| Type | Extensions | Extract Options | Default Method |
|------|------------|-----------------|----------------|
| PDF | `.pdf` | `PdfExtractOptions` | `pdfium` |
| DOCX | `.docx` | `DocxExtractOptions` | `python_docx` |
| PPTX | `.pptx` | `PptxExtractOptions` | `python_pptx` |
| Images | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` | `ImageExtractOptions` | `image` |
| Text | `.txt`, `.md`, `.json`, `.sh` | `TextExtractOptions` | `txt` |
| HTML | `.html` | `HtmlExtractOptions` | `markitdown` |
| Audio | `.mp3`, `.wav` | `AudioExtractOptions` | `audio` |

### Configuration

#### Extraction Options

```python
from devin_experimental import (
    PdfExtractOptions,
    DocxExtractOptions,
    ImageExtractOptions,
    EmbedOptions,
    CaptionOptions,
    SplitOptions,
)

# PDF extraction with all features
pdf_opts = PdfExtractOptions(
    extract_method="pdfium",      # or "pdfium_hybrid", "nemotron_parse", "ocr"
    extract_text=True,
    extract_images=True,
    extract_tables=True,
    extract_charts=True,
    text_depth="document",        # or "page"
    table_output_format="markdown",
)

# Office document extraction
docx_opts = DocxExtractOptions(
    extract_method="python_docx",  # or "render_as_pdf"
    extract_text=True,
    extract_images=True,
)

# Image captioning
caption_opts = CaptionOptions(
    endpoint_url="http://localhost:8000/v1/chat/completions",
    prompt="Describe this image:",
)

# Text splitting/chunking
split_opts = SplitOptions(
    split_by="sentence",    # or "page", "word", "size"
    split_length=512,
    split_overlap=50,
)

# Embedding
embed_opts = EmbedOptions(
    endpoint_url="http://localhost:8012/v1/embeddings",
    model_name="nvidia/llama-3.2-nv-embedqa-1b-v2",
)
```

#### `TaskConfig`

JSON-loadable configuration for processing tasks.

```python
from devin_experimental import TaskConfig, DEFAULT_TASK_CONFIG

# Use default config
results = client.process_pdf_files("/data/*.pdf", task_config=DEFAULT_TASK_CONFIG)

# Load from JSON file
config = TaskConfig.from_file("config.json")

# Load from JSON string
config = TaskConfig.from_json('''
{
    "extract": {
        "extract_text": true,
        "extract_tables": true,
        "extract_charts": true
    },
    "embed": {
        "endpoint_url": "http://localhost:8012/v1/embeddings"
    }
}
''')

# Create programmatically
from devin_experimental import PdfExtractOptions, EmbedOptions

config = TaskConfig(
    extract=PdfExtractOptions(extract_tables=True, extract_charts=True),
    embed=EmbedOptions(endpoint_url="http://localhost:8012/v1/embeddings"),
)
```

#### Default Configuration

The `DEFAULT_TASK_CONFIG` enables all extraction features:

```json
{
  "extract": {
    "extract_method": "pdfium",
    "text_depth": "document",
    "extract_text": true,
    "extract_images": true,
    "extract_tables": true,
    "extract_charts": true,
    "table_output_format": "markdown"
  },
  "embed": {
    "endpoint_url": null,
    "model_name": null
  },
  "enable_tracing": true
}
```

### Utilities

#### `FileInput`

Structured file input supporting multiple data sources.

```python
from devin_experimental import FileInput

# From path
fi = FileInput(path="/path/to/file.pdf")

# From bytes with custom name
fi = FileInput(data=pdf_bytes, name="document.pdf")

# From BytesIO
fi = FileInput(buffer=BytesIO(pdf_bytes), name="uploaded.pdf")
```

#### `get_pdf_page_count(pdf_bytes: bytes) -> int`

Count pages in a PDF for progress tracking.

```python
from devin_experimental import get_pdf_page_count

with open("document.pdf", "rb") as f:
    page_count = get_pdf_page_count(f.read())
```

#### `write_results_to_directory(output_dir, control_message)`

Write extraction results to disk, organized by document type.

```python
from devin_experimental import write_results_to_directory

def on_result(cm):
    write_results_to_directory("/output", cm)

results = client.process_pdf_files("/data/*.pdf", on_result=on_result)
```

## Examples

See the `examples/` folder for complete working examples:

- `01_launch_pipeline.py` - Launch a pipeline and verify it's running
- `02_process_pdfs.py` - Process PDF files with the default configuration
- `03_custom_config.py` - Use custom extraction and embedding settings
- `04_bytesio_input.py` - Process PDFs from BytesIO (e.g., HTTP uploads)

## Pipeline Configuration

The pipeline is configured via a YAML file. See `examples/pipeline.yaml` for a complete example.

Key stages for direct submission:

- `source_stage` - DirectSubmitSourceStage for receiving work
- `broker_response` - OutputQueueSinkStage for collecting results

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                         │
├─────────────────────────────────────────────────────────────┤
│  ProcessingClient                                            │
│  ├── process_pdf_files() / process_files()                  │
│  ├── submit() / fetch()                                      │
│  └── Progress tracking (tqdm)                                │
├─────────────────────────────────────────────────────────────┤
│  Pipeline (Ray Actors)                                       │
│  ├── DirectSubmitSourceStage  ←── Jobs submitted here       │
│  ├── PDF Extraction Stage                                    │
│  ├── Table/Chart Extraction                                  │
│  ├── Embedding Stage                                         │
│  └── OutputQueueSinkStage    ←── Results collected here     │
└─────────────────────────────────────────────────────────────┘
```

## License

See the main NV-Ingest repository for license information.
