"""Engine package for layout, rules, charts, barcodes, and pagination."""
from .barcode import barcode_html, barcode_svg, is_two_dimensional
from .chart import chart_svg
from .elements import (
    RenderCtx,
    box_css,
    element_html,
    field_text,
    font_family_css,
    measure_element_height,
    stroke_css,
    text_css,
)
from .logic import RuleEvaluationResult, check_condition, evaluate_rule, resolve_property_value
from .paginate import (
    LaidOutBand,
    PlacedBandRecord,
    PlacedElementRecord,
    RenderedPage,
    RenderOptions,
    paginate_report,
    render_html_document,
)

__all__ = [
    'barcode_html',
    'barcode_svg',
    'is_two_dimensional',
    'chart_svg',
    'RenderCtx',
    'text_css',
    'stroke_css',
    'box_css',
    'font_family_css',
    'field_text',
    'measure_element_height',
    'element_html',
    'RuleEvaluationResult',
    'check_condition',
    'evaluate_rule',
    'resolve_property_value',
    'LaidOutBand',
    'PlacedBandRecord',
    'PlacedElementRecord',
    'RenderedPage',
    'RenderOptions',
    'paginate_report',
    'render_html_document',
]
