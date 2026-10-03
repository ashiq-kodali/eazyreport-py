"""Fluent ReportBuilder API for building and rendering eazyreport documents."""
from typing import Any, Dict, List, Optional, Union

from .engine.paginate import RenderedPage, RenderOptions, paginate_report, render_html_document
from .model.document import LayoutDocument
from .model.normalize import load_template
from .renderers.pdf_renderer import render_pdf_bytes


class ReportBuilder:
    """Fluent report builder for binding datasets and parameters to an RTPL template."""

    def __init__(self, template: Union[str, bytes, Dict[str, Any], LayoutDocument]):
        self._doc: LayoutDocument = load_template(template)
        self._data: Any = {}
        self._params: Dict[str, Any] = {}
        self._title: str = self._doc.title or 'Report'
        self._options: RenderOptions = RenderOptions()
        self._cached_pages: Optional[List[RenderedPage]] = None

    def data(self, data: Any) -> 'ReportBuilder':
        """Set primary data object or list of records."""
        self._data = data
        self._cached_pages = None
        return self

    def records(self, records: List[Any]) -> 'ReportBuilder':
        """Set records list."""
        self._data = records
        self._cached_pages = None
        return self

    def params(self, params: Dict[str, Any]) -> 'ReportBuilder':
        """Set report runtime parameters."""
        self._params.update(params)
        self._cached_pages = None
        return self

    def title(self, title: str) -> 'ReportBuilder':
        """Set report window / document title."""
        self._title = title
        return self

    def options(self, options: RenderOptions) -> 'ReportBuilder':
        """Set pagination options."""
        self._options = options
        self._cached_pages = None
        return self

    def pages(self) -> List[RenderedPage]:
        """Execute pagination and return list of rendered pages."""
        if self._cached_pages is None:
            self._cached_pages = paginate_report(
                doc=self._doc,
                data=self._data,
                params=self._params,
                options=self._options,
            )
        return self._cached_pages

    def page_count(self) -> int:
        """Calculate and return total number of generated pages."""
        return len(self.pages())

    def to_html(self) -> str:
        """Render complete printable HTML document."""
        return render_html_document(self.pages(), title=self._title)

    def to_pdf(self) -> bytes:
        """Render vector PDF and return binary bytes."""
        return render_pdf_bytes(self.pages(), title=self._title)
