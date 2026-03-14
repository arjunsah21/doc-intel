# 🧾 Invoice Data Extractor

AI-powered invoice data extraction using **BAML** (Boundary AI Markup Language) and **Google Gemini**. Upload an invoice PDF or image and extract structured data — invoice numbers, order IDs, line items, totals, and more.

## Tech Stack

- **[BAML](https://docs.boundaryml.com/)** — Structured LLM output extraction with typed schemas
- **[Streamlit](https://streamlit.io/)** — Interactive web UI
- **[Google Gemini](https://ai.google.dev/)** — LLM (via Google AI Studio)
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package management
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** — PDF text extraction

## Setup

### 1. Clone & Install

```bash
# Install dependencies
uv sync
```

### 2. Configure API Key

Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey).

```bash
cp .env.example .env
# Edit .env and paste your Google AI Studio API key
```

```env
GOOGLE_API_KEY=your-google-ai-studio-api-key
```

### 3. Generate BAML Client

```bash
uv run baml-cli generate
```

This generates the typed Python client in `baml_client/` from the schemas in `baml_src/`.

### 4. Run

```bash
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Usage

1. **Choose extraction mode** — PDF text extraction or image-based (vision) extraction
2. **Upload an invoice** — Drop a PDF or image file
3. **Click "Extract Invoice Data"** — AI extracts structured data
4. **View results** — See details, line items, and download as JSON

## Extracted Fields

| Field | Description |
|-------|-------------|
| `invoice_number` | Invoice identifier |
| `order_id` | Associated order ID |
| `purchase_order_number` | PO number |
| `invoice_date` / `due_date` | Key dates (YYYY-MM-DD) |
| `vendor_name` / `customer_name` | Party names |
| `vendor_address` / `customer_address` | Full addresses |
| `line_items[]` | Description, quantity, unit price, total |
| `subtotal` / `tax` / `total_amount` | Financial summary |
| `currency` | ISO 4217 code (USD, EUR, INR, etc.) |
| `payment_terms` | Payment conditions |
| `notes` | Additional notes |

## Project Structure

```
├── baml_src/
│   ├── invoice.baml       # Extraction schemas & functions
│   ├── clients.baml       # LLM client config (Gemini)
│   └── generators.baml    # Python codegen config
├── baml_client/            # Auto-generated (do not edit)
├── app.py                  # Streamlit application
├── pyproject.toml          # Dependencies (uv)
├── .env.example            # API key template
└── README.md
```

## Switching LLM Providers

To use a different LLM, edit `baml_src/clients.baml`. BAML supports OpenAI, Anthropic, Google AI, Vertex AI, Azure OpenAI, AWS Bedrock, and any OpenAI-compatible endpoint. After changes, re-run:

```bash
uv run baml-cli generate
```
