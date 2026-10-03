"""High-level functional API for generating reports."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .builder import ReportBuilder
from .model.document import LayoutDocument


@dataclass
class PrintOptions:
    sources: Optional[Dict[str, Any]] = None
    base: Optional[Any] = None
    copies: int = 1
    title: Optional[str] = None
    calibration: bool = True


def builder_for(
    template: Union[str, bytes, Dict[str, Any], LayoutDocument],
    data: Any = None,
    params: Optional[Dict[str, Any]] = None,
    options: Optional[PrintOptions] = None,
) -> ReportBuilder:
    """Create and configure a ReportBuilder instance."""
    opts = options or PrintOptions()
    builder = ReportBuilder(template)

    if data is not None:
        if isinstance(data, list):
            builder.records(data)
        else:
            builder.data(data)

    if params:
        builder.params(params)

    if opts.title:
        builder.title(opts.title)

    return builder


def get_report_html(
    template: Union[str, bytes, Dict[str, Any], LayoutDocument],
    data: Any = None,
    params: Optional[Dict[str, Any]] = None,
    options: Optional[PrintOptions] = None,
) -> str:
    """Return the complete filled printable HTML document ready for viewing or printing."""
    return builder_for(template, data, params, options).to_html()


def get_report_pdf(
    template: Union[str, bytes, Dict[str, Any], LayoutDocument],
    data: Any = None,
    params: Optional[Dict[str, Any]] = None,
    options: Optional[PrintOptions] = None,
) -> bytes:
    """Generate raw binary PDF bytes directly for the report."""
    return builder_for(template, data, params, options).to_pdf()


def count_report_pages(
    template: Union[str, bytes, Dict[str, Any], LayoutDocument],
    data: Any = None,
    params: Optional[Dict[str, Any]] = None,
    options: Optional[PrintOptions] = None,
) -> int:
    """Calculate and return exact number of pages generated for the report."""
    return builder_for(template, data, params, options).page_count()
