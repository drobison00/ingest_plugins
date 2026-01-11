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

### `client.process_files(files, ...)`

Process files from glob patterns, paths, bytes, BytesIO, or FileInput. Document type is auto-detected from the file extension.

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
