# Utilities

## FileInput

Structured file input supporting multiple data sources.

```python
from devin_experimental import FileInput
from io import BytesIO

# From path
fi = FileInput(path="/path/to/file.pdf")

# From bytes with custom name
fi = FileInput(data=pdf_bytes, name="document.pdf")

# From BytesIO
fi = FileInput(buffer=BytesIO(pdf_bytes), name="uploaded.pdf")
```

## get_pdf_page_count

Count pages in a PDF for progress tracking.

```python
from devin_experimental import get_pdf_page_count

with open("document.pdf", "rb") as f:
    page_count = get_pdf_page_count(f.read())
```

## write_results_to_directory

Write extraction results to disk, organized by document type.

```python
from devin_experimental import write_results_to_directory

def on_result(cm):
    write_results_to_directory("/output", cm)

results = client.process_pdf_files("/data/*.pdf", on_result=on_result)
```
