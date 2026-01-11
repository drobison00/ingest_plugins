# Examples

This folder contains examples demonstrating how to use the `devin_experimental` library.

## Prerequisites

1. Install the library:
   ```bash
   cd scratch/devin_experimental
   pip install -e .
   ```

2. Have a pipeline configuration YAML file (see `pipeline.yaml` for an example)

3. Have some PDF files to process

## Examples

### 01_launch_pipeline.py

**Launch and verify a pipeline**

```bash
python 01_launch_pipeline.py --config pipeline.yaml
```

This example shows how to:
- Load a pipeline from a YAML configuration
- Verify the source and sink stages are accessible
- Keep the pipeline running

### 02_process_pdfs.py

**Process PDF files with default configuration**

```bash
# Process all PDFs in a directory
python 02_process_pdfs.py --config pipeline.yaml --pdf "/data/*.pdf"

# Process with a specific count (repeating files if needed)
python 02_process_pdfs.py --config pipeline.yaml --pdf "/data/*.pdf" -n 100

# Save results to disk
python 02_process_pdfs.py --config pipeline.yaml --pdf "/data/*.pdf" --output ./results
```

This example shows how to:
- Use `ProcessingClient` to submit work
- Use `DEFAULT_TASK_CONFIG` for standard extraction
- Track progress with tqdm
- Write results to disk

### 03_custom_config.py

**Use custom extraction and embedding settings**

```bash
# With custom embedding endpoint
python 03_custom_config.py --config pipeline.yaml --pdf "/data/*.pdf" \
    --embed-endpoint "http://localhost:8012/v1/embeddings"
```

This example shows how to:
- Create custom `TaskConfig` programmatically
- Use `PdfExtractOptions` and `EmbedOptions`
- Load config from JSON string or file
- Inspect extraction results

### 04_bytesio_input.py

**Process PDFs from BytesIO objects**

```bash
python 04_bytesio_input.py --config pipeline.yaml --pdf sample.pdf
```

This example shows how to:
- Use `FileInput` with different data sources
- Process HTTP uploads (BytesIO)
- Process S3 downloads (bytes)
- Mix file paths and in-memory data

### 05_async_processing.py

**Process results asynchronously as they arrive**

```bash
python 05_async_processing.py --config pipeline.yaml --pdf "/data/*.pdf" -n 50
```

This example shows how to:
- Use `fetch_as_available()` for async iteration
- Process results in real-time
- Build streaming/responsive applications

## Pipeline Configuration

The `pipeline.yaml` file configures the NV-Ingest pipeline for direct submission.
Key stages:

- `source_stage` - Receives jobs from `ProcessingClient`
- `broker_response` - Collects results for retrieval

See the main NV-Ingest documentation for full configuration options.
