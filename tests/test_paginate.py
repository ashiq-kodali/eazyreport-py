"""Tests for pagination and PDF generation."""
import os

from eazyreport.api import builder_for, count_report_pages, get_report_html, get_report_pdf
from eazyreport.builder import ReportBuilder
from eazyreport.model.document import Band, DataBand, LayoutDocument, LayoutPage
from eazyreport.model.types import LayoutElement, PageMargins, TextStyle


def _create_sample_doc():
    return LayoutDocument(
        title='Sample Report',
        pages=[
            LayoutPage(
                width=210.0,
                height=297.0,
                margins=PageMargins(top=10, right=10, bottom=10, left=10),
                reportTitle=Band(
                    id='rt',
                    height=20.0,
                    elements=[
                        LayoutElement(
                            id='t1',
                            type='text',
                            content='Invoice Summary',
                            style=TextStyle(fontSize=16.0, bold=True),
                            w=100.0,
                            h=10.0,
                        )
                    ],
                ),
                data=[
                    DataBand(
                        id='db',
                        height=10.0,
                        elements=[
                            LayoutElement(
                                id='item_name',
                                type='text',
                                content='{{item.name}}',
                                w=80.0,
                                h=8.0,
                            ),
                            LayoutElement(
                                id='item_price',
                                type='text',
                                content='{{formatCurrency item.price "USD" 2}}',
                                x=90.0,
                                w=40.0,
                                h=8.0,
                            ),
                        ],
                    )
                ],
                pageFooter=Band(
                    id='pf',
                    height=10.0,
                    elements=[
                        LayoutElement(
                            id='page_no',
                            type='text',
                            content='Page {{Page}} of {{TotalPages}}',
                            w=50.0,
                            h=8.0,
                        )
                    ],
                ),
            )
        ],
    )


def test_pagination_and_html():
    doc = _create_sample_doc()
    items = [{'name': f"Item {i}", 'price': i * 10.5} for i in range(1, 10)]

    builder = ReportBuilder(doc).data({'items': items})
    pages = builder.pages()
    assert len(pages) == 1

    html = builder.to_html()
    assert 'Invoice Summary' in html
    assert 'Item 1' in html
    assert 'Item 9' in html
    assert 'Page 1 of 1' in html


def test_pdf_generation():
    doc = _create_sample_doc()
    items = [{'name': f"Item {i}", 'price': i * 10.5} for i in range(1, 5)]

    pdf_bytes = ReportBuilder(doc).data({'items': items}).to_pdf()
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b'%PDF-')


def test_real_rtpl_invoice():
    rtpl_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'test_invoice.rtpl')
    )
    assert os.path.exists(rtpl_path)

    invoice_data = {
        'invoiceNumber': 'INV-2026-9901',
        'issueDate': '2026-10-02',
        'dueDate': '2026-11-01',
        'paymentTerms': 'Net 30',
        'company': {
            'name': 'EazyCorp International',
            'taxId': 'EU-987654321',
            'email': 'billing@eazycorp.com',
            'phone': '+1 (800) 555-0199',
            'address': {'line1': '100 Innovation Way, Suite 400', 'city': 'Zurich', 'zip': '8001'},
        },
        'customer': {
            'name': 'Acme Global Logistics',
            'taxId': 'US-123456789',
            'email': 'ap@acme.com',
            'phone': '+1 (555) 012-3456',
            'address': {'line1': '742 Evergreen Terrace', 'city': 'Springfield', 'zip': '97477'},
        },
        'items': [
            {'sku': 'SRV-001', 'description': 'Cloud Infrastructure Consultation', 'qty': 10, 'unitPrice': 150.00, 'discount': 0.05, 'taxRate': 0.08, 'total': 1425.00},
            {'sku': 'LIC-002', 'description': 'Enterprise Reporting Engine License', 'qty': 2, 'unitPrice': 2400.00, 'discount': 0.10, 'taxRate': 0.08, 'total': 4320.00},
            {'sku': 'SUP-003', 'description': '24/7 Dedicated Priority Support Tier', 'qty': 1, 'unitPrice': 500.00, 'discount': 0.00, 'taxRate': 0.08, 'total': 500.00},
        ],
        'subtotal': 6245.00,
        'taxTotal': 499.60,
        'grandTotal': 6744.60,
        'paid': False,
        'notes': 'Thank you for your business! Wire transfer details sent via encrypted email.',
    }

    builder = builder_for(rtpl_path, data=invoice_data)
    pages = builder.pages()
    assert len(pages) >= 1

    html = builder.to_html()
    assert 'Commercial Invoice' in html or 'INV-2026-9901' in html
    assert 'Cloud Infrastructure' in html

    pdf_bytes = builder.to_pdf()
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b'%PDF-')
