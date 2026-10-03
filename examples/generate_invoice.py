"""Example script demonstrating eazyreport usage with a commercial invoice template."""
import os
from eazyreport import ReportBuilder

def main():
    # Path to test_invoice.rtpl
    rtpl_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "test_invoice.rtpl")
    )
    if not os.path.exists(rtpl_path):
        rtpl_path = "test_invoice.rtpl"

    invoice_data = {
        "invoiceNumber": "INV-2026-9901",
        "issueDate": "2026-10-02",
        "dueDate": "2026-11-01",
        "paymentTerms": "Net 30",
        "company": {
            "name": "EazyCorp International",
            "taxId": "EU-987654321",
            "email": "billing@eazycorp.com",
            "phone": "+1 (800) 555-0199",
            "address": {
                "line1": "100 Innovation Way, Suite 400",
                "city": "Zurich",
                "zip": "8001",
            },
        },
        "customer": {
            "name": "Acme Global Logistics",
            "taxId": "US-123456789",
            "email": "ap@acme.com",
            "phone": "+1 (555) 012-3456",
            "address": {
                "line1": "742 Evergreen Terrace",
                "city": "Springfield",
                "zip": "97477",
            },
        },
        "items": [
            {
                "sku": "SRV-001",
                "description": "Cloud Infrastructure Consultation",
                "qty": 10,
                "unitPrice": 150.00,
                "discount": 0.05,
                "taxRate": 0.08,
                "total": 1425.00,
            },
            {
                "sku": "LIC-002",
                "description": "Enterprise Reporting Engine License",
                "qty": 2,
                "unitPrice": 2400.00,
                "discount": 0.10,
                "taxRate": 0.08,
                "total": 4320.00,
            },
            {
                "sku": "SUP-003",
                "description": "24/7 Dedicated Priority Support Tier",
                "qty": 1,
                "unitPrice": 500.00,
                "discount": 0.00,
                "taxRate": 0.08,
                "total": 500.00,
            },
        ],
        "subtotal": 6245.00,
        "taxTotal": 499.60,
        "grandTotal": 6744.60,
        "paid": False,
        "notes": "Thank you for your business! Wire transfer details sent via encrypted email.",
    }

    builder = ReportBuilder(rtpl_path).data(invoice_data).params({"Currency": "USD"})

    print(f"Total Pages Generated: {builder.page_count()}")

    html_out = builder.to_html()
    with open("invoice_output.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print("Generated invoice_output.html successfully.")

    pdf_bytes = builder.to_pdf()
    with open("invoice_output.pdf", "wb") as f:
        f.write(pdf_bytes)
    print(f"Generated invoice_output.pdf successfully ({len(pdf_bytes)} bytes).")

if __name__ == "__main__":
    main()
