<div align="center">

<img src="https://raw.githubusercontent.com/ashiq-kodali/eazyreport-py/main/assets/eazyreport_banner.png" alt="eazyreport Banner" width="100%" />

# eazyreport (Python)

**Ultra-fast, high-precision report generation engine for Python.**  
*Generate pixel-perfect printable HTML, vector SVG charts, barcodes/QR codes, and native vector PDF documents directly from `.rtpl` templates.*

[![PyPI version](https://img.shields.io/pypi/v/eazyreport.svg)](https://pypi.org/project/eazyreport/)
[![CI](https://github.com/ashiq-kodali/eazyreport-py/actions/workflows/ci.yml/badge.svg)](https://github.com/ashiq-kodali/eazyreport-py/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/eazyreport.svg)](https://pypi.org/project/eazyreport/)

</div>

---

## 🌟 Overview

`eazyreport` is an enterprise-grade reporting engine designed for Python developers. It takes visual `.rtpl` report templates and dynamically binds them with runtime JSON data, dictionaries, or database records. With a multi-pass layout engine, `eazyreport` produces **print-ready HTML documents** and **direct vector PDF files** with sub-millisecond execution.

---

## 💼 Real-World Use Cases

| Use Case | Description | Included Features |
| :--- | :--- | :--- |
| 🧾 **Commercial Invoices & Billing** | Multi-item commercial invoices, tax invoices, purchase orders, and sales receipts. | Multi-level footers, auto-calculated sums/averages, tax breakdowns, discount tables, and English cheque words (`numberToWords`). |
| 📦 **Shipping Labels & Waybills** | Logistics waybills, dispatch notes, courier labels, and bills of lading. | Built-in high-precision vector barcodes (`Code 128`, `Code 39`, `EAN-13`) and 2D verification `QR Codes`. |
| 📊 **Financial & Executive Reports** | Balance sheets, P&L statements, quarterly sales summaries, and executive decks. | Built-in vector SVG charts (`column`, `bar`, `line`, `area`, `pie`, `doughnut`) with legends and gridlines. |
| 🏥 **Healthcare & Lab Reports** | Patient summaries, blood test panels, clinical diagnostics, and discharge forms. | Multi-column layouts, conditional highlight rules for critical ranges, and structured section headers. |
| 🏷️ **Inventory & Asset Tags** | Warehouse stock audit sheets, shelf tags, product catalog pages, and asset tags. | Repeated multi-column grid printing, barcode integration, and auto-growing item descriptions. |
| 🎓 **Certificates & Statement of Accounts** | Course completion certificates, diplomas, accreditation passes, and monthly bank statements. | Full-bleed watermark overlays (`DRAFT`, `CONFIDENTIAL`), custom margins, and exact page budget management. |

---

## ⚙️ How It Works

`eazyreport` follows a clear, predictable 4-step pipeline:

```
┌─────────────────────┐      ┌─────────────────────┐
│  .rtpl Template     │  +   │  JSON / Dict Data   │
│  (Visual Layout)    │      │  (Runtime Payload)  │
└──────────┬──────────┘      └──────────┬──────────┘
           │                            │
           └──────────────┬─────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │  Multi-Pass Layout Engine         │
        │  - Two-pass pagination            │
        │  - Resolves [TotalPages] & [Page] │
        │  - Evaluates expressions & logic  │
        │  - Draws vector charts & barcodes │
        │  - Child bands & fillUnusedSpace  │
        └─────────────────┬─────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────────┐   ┌───────────────────────┐
│ Standalone HTML Page  │   │ Direct Vector PDF     │
│ (Printable & Preview) │   │ (Binary Byte Stream)  │
└───────────────────────┘   └───────────────────────┘
```

1. **Template Definition**: Load an `.rtpl` file containing document layout, page dimensions, bands, elements, and styles.
2. **Data Binding**: Inject your application's data (lists of records, master-detail hierarchies, and runtime parameters).
3. **Multi-Pass Layout & Pagination**:
   - **Pass 1**: Calculates content height, line wrapping, band growth, group boundaries, and total page count.
   - **Pass 2**: Resolves `[TotalPages]` and page numbers (`Page 1 of 5`), evaluates conditional styles (`rules`), and calculates aggregates (`sum`, `avg`, `min`, `max`, `count`).
4. **Dual Export**: Emits standalone, responsive HTML ready for browser viewing/printing, or direct vector PDF bytes via ReportLab.

---

## 🎨 How `.rtpl` Templates Are Generated

An **`.rtpl`** (Report Template) file is a clean, structured JSON document that defines the entire visual architecture of a report.

### 1. Visual Drag-and-Drop Designer
Most users generate `.rtpl` files using the visual report designer interface:
- **Visual Band Hierarchy**: Add and arrange bands (`ReportTitle`, `PageHeader`, `Data`, `GroupHeader`, `GroupFooter`, `Child`, `PageFooter`, `ReportSummary`).
- **Interactive Component Palette**: Place text blocks, fields, vector charts, barcodes, lines, and shapes with drag-and-drop coordinates.
- **Visual Styling Inspector**: Configure typography, borders, backgrounds, paddings, and alignment visually.
- **Export**: Save the report as an `.rtpl` file to version control alongside your application code.

### 2. Programmatic Creation in Python
You can also generate or customize `.rtpl` templates dynamically in Python using `eazyreport`'s type-safe data models:

```python
from eazyreport import LayoutDocument, LayoutPage, Band, DataBand, LayoutElement, TextStyle

doc = LayoutDocument(
    title="Invoice Template",
    pages=[
        LayoutPage(
            size="A4",
            orientation="portrait",
            reportTitle=Band(
                height=25.0,
                elements=[
                    LayoutElement(
                        id="title_text",
                        type="text",
                        content="Tax Invoice",
                        style=TextStyle(fontSize=18.0, bold=True),
                        w=100.0,
                        h=12.0,
                    )
                ],
            ),
            data=[
                DataBand(
                    id="items_band",
                    dataPath="items",
                    height=8.0,
                    elements=[
                        LayoutElement(id="item_desc", type="field", field_name="item.description", w=80.0, h=8.0),
                        LayoutElement(id="item_qty", type="field", field_name="item.qty", x=85.0, w=20.0, h=8.0),
                        LayoutElement(id="item_price", type="field", field_name="item.unitPrice", x=110.0, w=30.0, h=8.0),
                    ],
                )
            ],
        )
    ],
)
```

---

## 📦 Installation

```bash
pip install eazyreport
```

Or install with `uv` / `poetry`:
```bash
uv add eazyreport
# or
poetry add eazyreport
```

---

## 🚀 Quickstart

### 1. Generate Printable HTML and Vector PDF

```python
from eazyreport import ReportBuilder

# Initialize builder with template file and data payload
builder = (
    ReportBuilder("test_invoice.rtpl")
    .data({
        "invoiceNumber": "INV-2026-9901",
        "issueDate": "2026-10-02",
        "customer": {
            "name": "Acme Global Logistics",
            "email": "ap@acme.com",
            "address": {"city": "Zurich", "zip": "8001"},
        },
        "items": [
            {"sku": "SRV-01", "description": "Cloud Infrastructure", "qty": 10, "unitPrice": 150.00, "total": 1500.00},
            {"sku": "LIC-02", "description": "Enterprise License", "qty": 2, "unitPrice": 2400.00, "total": 4800.00},
        ],
        "grandTotal": 6300.00,
    })
    .params({"Company": "EazyCorp International"})
)

# 1. Export Standalone HTML (for in-browser preview or web printing)
html_str = builder.to_html()
with open("invoice.html", "w", encoding="utf-8") as f:
    f.write(html_str)

# 2. Export Direct Vector PDF (binary bytes)
pdf_bytes = builder.to_pdf()
with open("invoice.pdf", "wb") as f:
    f.write(pdf_bytes)

# 3. Inspect Pagination
print(f"Total Pages Generated: {builder.page_count()}")
```

### 2. High-Level Functional API

```python
from eazyreport import get_report_html, get_report_pdf, count_report_pages

# One-liner HTML generation
html_doc = get_report_html("template.rtpl", data=data, params=params)

# One-liner PDF generation
pdf_data = get_report_pdf("template.rtpl", data=data, params=params)

# Calculate total page count
pages = count_report_pages("template.rtpl", data=data)
```

---

## 🧩 Built-in Expression Helpers

| Helper | Example Syntax | Purpose |
| :--- | :--- | :--- |
| **`formatCurrency`** | `{{formatCurrency item.total "USD" 2}}` | Formats numeric value as currency ($1,234.50) |
| **`formatNumber`** | `{{formatNumber item.qty 0 true}}` | Formats numbers with thousands separators |
| **`formatDate`** | `{{formatDate issueDate "dd/MM/yyyy"}}` | Custom date formatting tokens |
| **`formatPercent`** | `{{formatPercent discount 1}}` | Converts decimal ratios to percentages (`85.4%`) |
| **`numberToWords`** | `{{numberToWords grandTotal}}` | English words for bank cheques (`One Hundred Twenty-Five and 50/100`) |
| **`sum`** | `{{sum items "total"}}` | Calculates total sum across list |
| **`avg`** | `{{avg items "unitPrice"}}` | Calculates arithmetic mean of field |
| **`count`** | `{{count items}}` | Total count of records |
| **`iif`** | `{{iif (gt qty 10) "Bulk Order" "Standard"}}` | Inline ternary condition |
| **`titlecase`** | `{{titlecase customer.name}}` | Converts text to Title Case |

---

## 🧪 Testing

Run the test suite covering expressions, multi-pass pagination, SVG charts, barcodes, and real commercial invoice templates:

```bash
pytest -v tests
```

---

## 👥 Contributors

- **Ashiq Kodali** ([@ashiq-kodali](https://github.com/ashiq-kodali)) — *Lead Developer & Maintainer*
- **Thamneem** ([@thamneem](https://github.com/thamneem)) — *Contributor*

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
