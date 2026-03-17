# prisma-s-lit-review

A transparent, reproducible Python library for keyword corpus analysis of PDF and Word documents, built on PRISMA-S methodology.

Designed so that any researcher can run the **same keyword search** on their own Google Drive folder of collected literature and get identical, auditable results.

---

## What it does

- Downloads PDFs and `.docx` files from a **Google Drive folder** (or reads a local path)
- Extracts full text from each document
- Counts occurrences of every term in a versioned **keyword dictionary**
- Writes a **long-format Excel matrix** (one row per document × term) with full reproducibility metadata

Every output row records the **protocol version**, **keyword dictionary version**, **run timestamp**, and **source reference** so results can be independently replicated.

---

## Methodology

Keyword matching follows the locked **PRISMA-S Keyword Protocol v1.1** (`protocol/PRISMA_keyword_protocol_v1.1.md`):

| Rule | Setting |
|------|---------|
| Case sensitivity | Case-insensitive |
| Word matching | Exact word boundaries — no partial substrings |
| Multi-word terms | Exact phrase, whitespace-flexible (handles OCR line-breaks) |
| Stemming / lemmatisation | None |
| Zero-count rows | Included for every document × term combination |

---

## Installation

```bash
pip install prisma-s-lit-review
```

Or install from source (recommended for development):

```bash
git clone https://github.com/wielgosz/PRISMA_S_Lit_Report.git
cd PRISMA_S_Lit_Report
pip install -e ".[dev]"
```

---

## Quick start

### Python API

```python
from prisma_s import run_analysis

# From a local folder
df = run_analysis(
    batch_id="batch_01",
    output_xlsx="results/batch_01.xlsx",
    input_path="/path/to/your/pdfs",
)

# From Google Drive
df = run_analysis(
    batch_id="batch_01",
    output_xlsx="results/batch_01.xlsx",
    drive_folder_id="YOUR_FOLDER_ID",
    drive_credentials="credentials.json",
)

# Custom keyword dictionary
df = run_analysis(
    batch_id="batch_01",
    output_xlsx="results/batch_01.xlsx",
    input_path="/path/to/pdfs",
    keyword_csv="keywords/keyword_dictionary_v1.2.csv",
)
```

### Command-line interface

```bash
# Local directory
prisma-s run --batch batch_01 --output results/batch_01.xlsx --input /path/to/pdfs

# Google Drive folder
prisma-s run \
  --batch batch_01 \
  --output results/batch_01.xlsx \
  --drive-folder YOUR_FOLDER_ID \
  --drive-credentials credentials.json

# Custom keyword dictionary
prisma-s run \
  --batch batch_01 \
  --output results/batch_01.xlsx \
  --input /path/to/pdfs \
  --keywords keywords/keyword_dictionary_v1.2.csv

# Check version
prisma-s --version
```

---

## Output format

A single Excel sheet (`Long_AllTerms`) in long format:

| Column | Description |
|--------|-------------|
| `Batch` | Batch identifier supplied at runtime |
| `Document Name` | Filename of the source document |
| `Title` | Extracted document title |
| `Year` | Extracted publication year |
| `Group` | Keyword group (e.g. AOI, Commodity, Supply Chain Node) |
| `Term` | Matched keyword |
| `Count` | Number of matches in full document text |
| `Protocol Version` | Locked protocol version used (e.g. `1.1`) |
| `Keyword Dict Version` | Version of the keyword dictionary CSV used |
| `Run UTC` | ISO-8601 timestamp of the run |
| `Source Ref` | Local path or `gdrive:<folder_id>` |

---

## Google Drive setup

You need a Google Cloud project with the Drive API enabled and an OAuth 2.0 credentials file.

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create or select a project
3. Enable the **Google Drive API** (`APIs & Services → Library → Google Drive API`)
4. Create credentials: `APIs & Services → Credentials → Create Credentials → OAuth client ID`
   - Application type: **Desktop app**
5. Download the JSON and save it as `credentials.json`
6. On first run a browser window opens for consent; a `token.json` is cached for subsequent runs

> Keep `credentials.json` and `token.json` out of version control — add them to `.gitignore`.

---

## Keyword dictionary

The bundled dictionary is `keywords/keyword_dictionary_v1.1.csv` — 120 terms across three groups:

| Group | Description |
|-------|-------------|
| `AOI` | Area of Interest — geospatial and administrative terms |
| `Commodity` | Agricultural commodity terms |
| `Supply Chain Node` | Supply chain node and facility terms |

CSV schema (`group,term`):

```csv
group,term
AOI,Coordinate
Commodity,Coffee
Supply Chain Node,Mill
```

To create a new version, copy the CSV, make changes, and name it `keyword_dictionary_v1.2.csv`. Pass it via `--keywords`. The version is inferred from the filename automatically.

**Never modify a previously used dictionary version** — create a new one to preserve replicability.

---

## Replicating results

To reproduce a previous run exactly:

1. Use the same `Protocol Version` and `Keyword Dict Version` shown in the output
2. Run against the same source documents (Drive folder ID or local path in `Source Ref`)
3. The `Run UTC` timestamp will differ but all counts will be identical

---

## Running tests

```bash
pytest tests/ -v
```

---

## Repository structure

```
PRISMA_S_Lit_Report/
├── prisma_s/                  # Installable Python package
│   ├── __init__.py
│   ├── keywords.py            # Keyword dictionary loader
│   ├── extract.py             # PDF + DOCX text extraction
│   ├── search.py              # Keyword matching engine
│   ├── drive.py               # Google Drive integration
│   ├── runner.py              # Analysis orchestrator
│   └── cli.py                 # Command-line interface
├── keywords/
│   └── keyword_dictionary_v1.1.csv
├── protocol/
│   └── PRISMA_keyword_protocol_v1.1.md
├── tests/
│   └── test_search.py
├── scripts/
│   └── keyword_corpus_analysis.py   # Original standalone script (retained for reference)
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` + `openpyxl` | DataFrame manipulation and Excel output |
| `PyMuPDF` (`fitz`) | Primary PDF text extraction |
| `PyPDF2` | Fallback PDF extraction |
| `python-docx` | Word document text extraction |
| `google-api-python-client` | Google Drive API |
| `google-auth-oauthlib` | OAuth 2.0 authentication flow |

---

## Versioning policy

- **Protocol versions** (`protocol/`) are append-only — never edit a released version
- **Keyword dictionaries** (`keywords/`) follow `keyword_dictionary_v{MAJOR}.{MINOR}.csv` naming
- **Package versions** follow [Semantic Versioning](https://semver.org)

---

## License

MIT © Benjamin Wielgosz 2026
