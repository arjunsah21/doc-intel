// Invoice data extraction schema and function
// Uses BAML to extract structured invoice data from text/images via LLM

class Address {
  street string?
  city string?
  state string?
  zip string?
  country string?
}

class LineItem {
  description string
  quantity int?
  unit_price float?
  total float?
}

class InvoiceData {
  invoice_number string?
  order_id string?
  purchase_order_number string?
  invoice_date string?
  due_date string?
  vendor_name string?
  vendor_address Address?
  customer_name string?
  customer_address Address?
  line_items LineItem[]
  subtotal float?
  tax float?
  total_amount float?
  currency string?
  payment_terms string?
  notes string?
}

function ExtractInvoice(invoice_text: string) -> InvoiceData {
  client Gemini
  prompt #"
    You are an expert invoice data extraction system.
    
    Carefully extract ALL invoice information from the following text.
    If a field is not present in the invoice, leave it as null.
    For line items, extract every individual product/service listed.
    For dates, use the format YYYY-MM-DD when possible.
    For currency, use ISO 4217 codes (e.g., USD, EUR, INR).

    INVOICE TEXT:
    ---
    {{ invoice_text }}
    ---

    {{ ctx.output_format }}
  "#
}

function ExtractInvoiceFromImage(invoice_image: image) -> InvoiceData {
  client Gemini
  prompt #"
    You are an expert invoice data extraction system.
    
    Carefully examine the invoice image below and extract ALL invoice information.
    If a field is not present in the invoice, leave it as null.
    For line items, extract every individual product/service listed.
    For dates, use the format YYYY-MM-DD when possible.
    For currency, use ISO 4217 codes (e.g., USD, EUR, INR).

    {{ invoice_image }}

    {{ ctx.output_format }}
  "#
}
