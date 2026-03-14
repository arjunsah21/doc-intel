import streamlit as st
import json
import logging
import time
import base64
import fitz  # PyMuPDF
from dotenv import load_dotenv
from pathlib import Path

# ── Logging Setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

logger.info("Starting Invoice Data Extractor application")

load_dotenv()
logger.info("Environment variables loaded from .env")

from baml_client.sync_client import b
from baml_client.types import InvoiceData

logger.info("BAML client and types imported successfully")

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invoice Data Extractor",
    page_icon=":material/receipt_long:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helper Functions ─────────────────────────────────────────────────
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    logger.info("Starting PDF text extraction (%d bytes)", len(pdf_bytes))
    start = time.perf_counter()

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)
    logger.info("PDF opened — %d page(s) detected", page_count)

    text = ""
    for i, page in enumerate(doc):
        page_text = page.get_text()
        text += page_text
        logger.info("  Page %d/%d extracted — %d characters", i + 1, page_count, len(page_text))

    doc.close()
    elapsed = time.perf_counter() - start
    logger.info("PDF text extraction complete — %d total characters in %.3fs", len(text), elapsed)
    return text


def format_address(addr) -> str:
    """Format an Address object into a readable string."""
    if addr is None:
        return "N/A"
    parts = [addr.street, addr.city, addr.state, addr.zip, addr.country]
    return ", ".join(p for p in parts if p) or "N/A"


def invoice_to_dict(inv: InvoiceData) -> dict:
    """Convert InvoiceData to a plain dict for JSON export."""
    def addr_dict(a):
        if a is None:
            return None
        return {
            "street": a.street, "city": a.city, "state": a.state,
            "zip": a.zip, "country": a.country,
        }

    return {
        "invoice_number": inv.invoice_number,
        "order_id": inv.order_id,
        "purchase_order_number": inv.purchase_order_number,
        "invoice_date": inv.invoice_date,
        "due_date": inv.due_date,
        "vendor_name": inv.vendor_name,
        "vendor_address": addr_dict(inv.vendor_address),
        "customer_name": inv.customer_name,
        "customer_address": addr_dict(inv.customer_address),
        "line_items": [
            {
                "description": li.description,
                "quantity": li.quantity,
                "unit_price": li.unit_price,
                "total": li.total,
            }
            for li in inv.line_items
        ],
        "subtotal": inv.subtotal,
        "tax": inv.tax,
        "total_amount": inv.total_amount,
        "currency": inv.currency,
        "payment_terms": inv.payment_terms,
        "notes": inv.notes,
    }


# ── Session State ────────────────────────────────────────────────────
if "extraction_history" not in st.session_state:
    st.session_state.extraction_history = []


# ── Header ───────────────────────────────────────────────────────────
st.title("Invoice Data Extractor", anchor=False)
st.caption("Upload an invoice and extract structured data using AI — powered by BAML + Gemini")


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings", anchor=False)
    st.divider()

    extraction_mode = st.radio(
        "Extraction Mode",
        ["Text Extraction (PDF)", "Image Extraction"],
        help="Text mode extracts text from PDFs first, then sends to LLM.\n"
             "Image mode sends the image directly to the LLM for vision-based extraction.",
    )

    st.divider()
    st.header("History", anchor=False)
    if st.session_state.extraction_history:
        for i, entry in enumerate(reversed(st.session_state.extraction_history)):
            inv = entry["result"]
            label = inv.invoice_number or inv.order_id or f"Invoice #{i+1}"
            with st.expander(label, icon=":material/description:"):
                st.write(f"**Vendor:** {inv.vendor_name or 'N/A'}")
                st.write(f"**Total:** {inv.currency or ''} {inv.total_amount or 'N/A'}")
                st.write(f"**Date:** {inv.invoice_date or 'N/A'}")
    else:
        st.caption("No extractions yet. Upload an invoice to get started!")

    st.divider()
    st.caption("Built with BAML + Streamlit")


# ── Main Content ─────────────────────────────────────────────────────
st.subheader("Upload Invoice", anchor=False, divider="blue")

if "Text" in extraction_mode:
    uploaded_file = st.file_uploader(
        "Drop your invoice PDF here",
        type=["pdf"],
        help="Upload a PDF invoice to extract data from",
    )
else:
    uploaded_file = st.file_uploader(
        "Drop your invoice image here",
        type=["png", "jpg", "jpeg", "webp"],
        help="Upload an invoice image for vision-based extraction",
    )

if uploaded_file is not None:
    logger.info("File uploaded: name=%s, type=%s, size=%d bytes",
                 uploaded_file.name, uploaded_file.type, uploaded_file.size)
    file_bytes = uploaded_file.read()

    # Preview
    if "Text" in extraction_mode:
        st.info(f"**{uploaded_file.name}** — {len(file_bytes) / 1024:.1f} KB", icon=":material/description:")
        with st.expander("Extracted Text Preview", expanded=False, icon=":material/article:"):
            preview_text = extract_text_from_pdf(file_bytes)
            st.text(preview_text[:2000] + ("..." if len(preview_text) > 2000 else ""))
    else:
        with st.expander("Image Preview", expanded=False, icon=":material/image:"):
            st.image(file_bytes, caption=uploaded_file.name, width=400)

    extract_btn = st.button(
        "Extract Invoice Data",
        type="primary",
        icon=":material/auto_awesome:",
    )
else:
    extract_btn = False
    st.info(
        "**How it works**\n\n"
        "1. Upload an invoice (PDF or image)\n"
        "2. Click **Extract Invoice Data**\n"
        "3. View structured results instantly",
        icon=":material/lightbulb:",
    )

st.subheader("Extraction Results", anchor=False, divider="green")

if uploaded_file is not None and extract_btn:
    logger.info("Extraction triggered for file: %s (mode: %s)", uploaded_file.name, extraction_mode)

    with st.spinner("Extracting invoice data with AI..."):
        try:
            if "Text" in extraction_mode:
                logger.info("Step 1/3: Extracting text from PDF")
                invoice_text = extract_text_from_pdf(file_bytes)

                if not invoice_text.strip():
                    logger.warning("PDF text extraction returned empty — aborting")
                    st.error("Could not extract text from PDF. Try image extraction mode instead.", icon=":material/error:")
                    st.stop()

                logger.info("Step 2/3: Sending extracted text to LLM via BAML (%d chars)", len(invoice_text))
                start = time.perf_counter()
                result = b.ExtractInvoice(invoice_text)
                elapsed = time.perf_counter() - start
                logger.info("Step 3/3: LLM extraction complete in %.3fs", elapsed)
            else:
                logger.info("Step 1/2: Encoding image as base64")
                from baml_py import Image as BamlImage
                img = BamlImage.from_base64(
                    media_type=f"image/{uploaded_file.type.split('/')[-1]}",
                    base64=base64.b64encode(file_bytes).decode(),
                )
                logger.info("Step 1/2: Image encoded — %d bytes base64", len(base64.b64encode(file_bytes)))

                logger.info("Step 2/2: Sending image to LLM via BAML (vision mode)")
                start = time.perf_counter()
                result = b.ExtractInvoiceFromImage(img)
                elapsed = time.perf_counter() - start
                logger.info("Step 2/2: LLM vision extraction complete in %.3fs", elapsed)

            # Log extracted data summary
            logger.info("── Extraction Results ──")
            logger.info("  Invoice #:    %s", result.invoice_number)
            logger.info("  Order ID:     %s", result.order_id)
            logger.info("  PO Number:    %s", result.purchase_order_number)
            logger.info("  Vendor:       %s", result.vendor_name)
            logger.info("  Customer:     %s", result.customer_name)
            logger.info("  Date:         %s", result.invoice_date)
            logger.info("  Total:        %s %s", result.currency, result.total_amount)
            logger.info("  Line items:   %d", len(result.line_items))
            for i, li in enumerate(result.line_items):
                logger.info("    [%d] %s | qty=%s | price=%s | total=%s",
                            i + 1, li.description, li.quantity, li.unit_price, li.total)
            logger.info("── End Results ──")

            # Save to history
            st.session_state.extraction_history.append({
                "filename": uploaded_file.name,
                "result": result,
            })
            logger.info("Result saved to session history (total: %d)", len(st.session_state.extraction_history))

            # ── Display Results ──────────────────────────────
            st.success("Extraction Complete", icon=":material/check_circle:")

            # Key info as a clean markdown table
            total_display = f"{result.currency or ''} {result.total_amount}" if result.total_amount else "—"
            st.markdown(
                f"""
| Invoice # | Order ID | Date | Total |
|---|---|---|---|
| {result.invoice_number or '—'} | {result.order_id or '—'} | {result.invoice_date or '—'} | {total_display} |
"""
            )

            # Tabbed details
            tab_details, tab_items, tab_json = st.tabs([
                ":material/contact_page: Details",
                ":material/inventory_2: Line Items",
                ":material/data_object: JSON",
            ])

            with tab_details:
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown("##### :material/business: Vendor")
                    st.write(f"**Name:** {result.vendor_name or 'N/A'}")
                    st.write(f"**Address:** {format_address(result.vendor_address)}")
                with d2:
                    st.markdown("##### :material/person: Customer")
                    st.write(f"**Name:** {result.customer_name or 'N/A'}")
                    st.write(f"**Address:** {format_address(result.customer_address)}")

                st.divider()
                st.markdown(
                    f"""
| PO Number | Due Date | Payment Terms |
|---|---|---|
| {result.purchase_order_number or '—'} | {result.due_date or '—'} | {result.payment_terms or '—'} |
"""
                )

                if result.notes:
                    st.divider()
                    st.info(f"**Notes:** {result.notes}", icon=":material/sticky_note_2:")

            with tab_items:
                if result.line_items:
                    items_data = []
                    for item in result.line_items:
                        items_data.append({
                            "Description": item.description,
                            "Qty": item.quantity,
                            "Unit Price": item.unit_price,
                            "Total": item.total,
                        })
                    st.dataframe(items_data, use_container_width=True, hide_index=True)

                    st.divider()
                    st.markdown(
                        f"""
| Subtotal | Tax | Total Amount |
|---|---|---|
| {f"{result.subtotal:.2f}" if result.subtotal else '—'} | {f"{result.tax:.2f}" if result.tax else '—'} | {f"{result.currency or ''} {result.total_amount:.2f}" if result.total_amount else '—'} |
"""
                    )
                else:
                    st.info("No line items were found in this invoice.")

            with tab_json:
                json_data = json.dumps(invoice_to_dict(result), indent=2, default=str)
                st.code(json_data, language="json")
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"{Path(uploaded_file.name).stem}_extracted.json",
                    mime="application/json",
                    icon=":material/download:",
                )

        except Exception as e:
            logger.exception("Extraction failed for file: %s", uploaded_file.name)
            st.error(f"Extraction failed: {str(e)}", icon=":material/error:")
            with st.expander("Error Details", icon=":material/search:"):
                st.exception(e)

elif not uploaded_file:
    st.info("Upload a PDF or image above to extract structured invoice data.", icon=":material/upload_file:")
else:
    st.info("Click **Extract Invoice Data** to begin extraction.", icon=":material/touch_app:")
