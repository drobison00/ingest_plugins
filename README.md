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
pip install -e .
```

## Local Development with Docker Compose

To test with the default local docker-compose deployment of the pipeline NIMs:

```bash
source scripts/setup_local_env_paths.sh
```

This configures the environment variables for connecting to locally deployed NIM services.

## Quick Start

### Using Glob Paths

```python
from devin_experimental import (
    launch_pipeline,
    get_stage_actor,
    ProcessingClient,
    DEFAULT_TASK_CONFIG,
)

# Launch pipeline and get actors
interface = launch_pipeline("pipeline.yaml")
source = get_stage_actor(interface, "source_stage")
sink = get_stage_actor(interface, "broker_response")

# Create client
client = ProcessingClient(source=source, sink=sink, show_progress=True)

# Process files using glob patterns
results = client.process_files("/data/*.pdf", task_config=DEFAULT_TASK_CONFIG)

# Or use document-type specific methods
results = client.process_pdf_files("/data/documents/*.pdf")
results = client.process_image_files("/data/images/*.jpg")
```

### Using BytesIO Objects

```python
from io import BytesIO
from devin_experimental import ProcessingClient, FileInput, DEFAULT_TASK_CONFIG

# Process BytesIO objects (e.g., from HTTP uploads)
pdf_buffer = BytesIO(uploaded_file_bytes)

results = client.process_files(
    [pdf_buffer],
    task_config=DEFAULT_TASK_CONFIG,
)

# For multiple BytesIO with custom names
files = [
    FileInput(buffer=BytesIO(pdf1_bytes), name="report.pdf"),
    FileInput(buffer=BytesIO(pdf2_bytes), name="invoice.pdf"),
]
results = client.process_files(files, task_config=DEFAULT_TASK_CONFIG)
```

### Mixed Input Types

```python
from io import BytesIO
from devin_experimental import FileInput

# Combine paths, bytes, and BytesIO in a single call
files = [
    "/path/to/local/file.pdf",              # File path
    raw_pdf_bytes,                           # Raw bytes
    BytesIO(uploaded_bytes),                 # BytesIO buffer
    FileInput(data=pdf_bytes, name="doc.pdf"),  # Named bytes
]

results = client.process_files(files, task_config=DEFAULT_TASK_CONFIG)
```

## Documentation

- **[API Reference](docs/api.md)** - Pipeline management and ProcessingClient methods
- **[Configuration](docs/configuration.md)** - Extraction options, TaskConfig, and document types
- **[Utilities](docs/utilities.md)** - FileInput, page counting, and result writing

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
