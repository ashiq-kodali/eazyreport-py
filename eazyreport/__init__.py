"""eazyreport-py: Ultra-fast, zero-JS report generation engine for Python.

Pure Python implementation of .rtpl templates, Handlebars expressions, FastReport
conditional formatting, SVG charts, barcodes/QR codes, HTML printing, and native vector PDF.
"""

# API & Builder
from .api import PrintOptions, builder_for, count_report_pages, get_report_html, get_report_pdf
from .builder import ReportBuilder

# Engine & Rendering
from .engine.barcode import barcode_html, barcode_svg
from .engine.chart import chart_svg
from .engine.elements import RenderCtx, box_css, element_html, field_text, stroke_css, text_css
from .engine.logic import RuleEvaluationResult, check_condition, evaluate_rule, resolve_property_value
from .engine.paginate import (
    LaidOutBand,
    PlacedBandRecord,
    PlacedElementRecord,
    RenderedPage,
    RenderOptions,
    paginate_report,
    render_html_document,
)

# Expressions & Formatting
from .expressions.engine import (
    EXPRESSION_HELPERS,
    eval_condition,
    eval_template,
    eval_text,
    eval_value,
    get_path,
)
from .expressions.format import (
    escape_html,
    format_currency,
    format_date_pattern,
    format_number,
    format_value,
    to_date,
)
from .expressions.number_to_words import number_to_words

# Models & Normalization
from .model.document import Band, ChildBand, DataBand, GroupBand, LayoutDocument, LayoutPage
from .model.normalize import load_template, normalize_document
from .model.types import (
    BorderStyle,
    BoxStyle,
    HAlign,
    LayoutElement,
    LogicRule,
    PageMargins,
    TextStyle,
    VAlign,
    ValueFormat,
    Watermark,
)
from .renderers.pdf_renderer import render_pdf_bytes

__version__ = '1.0.0'
__author__ = 'Ashiq Kodali'

__all__ = [
    # API
    'ReportBuilder',
    'builder_for',
    'get_report_html',
    'get_report_pdf',
    'count_report_pages',
    'PrintOptions',
    'load_template',
    'normalize_document',

    # Engine
    'paginate_report',
    'render_html_document',
    'render_pdf_bytes',
    'RenderedPage',
    'RenderOptions',
    'PlacedBandRecord',
    'PlacedElementRecord',
    'LaidOutBand',
    'chart_svg',
    'barcode_html',
    'barcode_svg',
    'element_html',
    'field_text',
    'text_css',
    'box_css',
    'stroke_css',
    'RenderCtx',
    'evaluate_rule',
    'check_condition',
    'resolve_property_value',
    'RuleEvaluationResult',

    # Expressions
    'eval_template',
    'eval_text',
    'eval_condition',
    'eval_value',
    'get_path',
    'EXPRESSION_HELPERS',
    'format_currency',
    'format_number',
    'format_date_pattern',
    'format_value',
    'escape_html',
    'to_date',
    'number_to_words',

    # Models
    'LayoutDocument',
    'LayoutPage',
    'Band',
    'DataBand',
    'GroupBand',
    'ChildBand',
    'LayoutElement',
    'TextStyle',
    'BoxStyle',
    'ValueFormat',
    'LogicRule',
    'PageMargins',
    'Watermark',
    'HAlign',
    'VAlign',
    'BorderStyle',
]
