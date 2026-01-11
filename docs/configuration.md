# Configuration

## Extraction Options

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

## TaskConfig

JSON-loadable configuration for processing tasks.

```python
from devin_experimental import TaskConfig, DEFAULT_TASK_CONFIG

# Use default config
results = client.process_files("/data/*.pdf", task_config=DEFAULT_TASK_CONFIG)

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

## Default Configuration

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

## Supported Document Types

| Type | Extensions | Extract Options | Default Method |
|------|------------|-----------------|----------------|
| PDF | `.pdf` | `PdfExtractOptions` | `pdfium` |
| DOCX | `.docx` | `DocxExtractOptions` | `python_docx` |
| PPTX | `.pptx` | `PptxExtractOptions` | `python_pptx` |
| Images | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` | `ImageExtractOptions` | `image` |
| Text | `.txt`, `.md`, `.json`, `.sh` | `TextExtractOptions` | `txt` |
| HTML | `.html` | `HtmlExtractOptions` | `markitdown` |
| Audio | `.mp3`, `.wav` | `AudioExtractOptions` | `audio` |
