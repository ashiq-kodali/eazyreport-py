"""Tests for vector SVG charts and barcodes."""
from eazyreport.engine.barcode import barcode_html, barcode_svg
from eazyreport.engine.chart import chart_svg
from eazyreport.model.types import LayoutElement


def test_chart_svg():
    el = LayoutElement(
        id='c1',
        type='chart',
        chartType='column',
        title='Sales Growth',
        w=100.0,
        h=50.0,
    )
    svg = chart_svg(el, ['Q1', 'Q2', 'Q3', 'Q4'], [100, 150, 220, 310])
    assert '<svg' in svg
    assert 'Sales Growth' in svg
    assert '<rect' in svg
    assert 'Q1' in svg


def test_pie_chart_svg():
    el = LayoutElement(
        id='c2',
        type='chart',
        chartType='pie',
        title='Distribution',
        w=80.0,
        h=80.0,
    )
    svg = chart_svg(el, ['North', 'South'], [60, 40])
    assert '<svg' in svg
    assert '<path' in svg or '<circle' in svg


def test_code128_barcode_svg():
    el = LayoutElement(
        id='b1',
        type='barcode',
        symbology='code128',
        w=60.0,
        h=20.0,
        showText=True,
    )
    svg = barcode_svg(el, 'INV-2026-001')
    assert '<svg' in svg
    assert '<rect' in svg
    assert 'INV-2026-001' in svg


def test_qr_code_svg():
    el = LayoutElement(
        id='b2',
        type='barcode',
        symbology='qrcode',
        w=30.0,
        h=30.0,
    )
    svg = barcode_svg(el, 'https://example.com/verify?id=123')
    assert '<svg' in svg
    assert '<rect' in svg
