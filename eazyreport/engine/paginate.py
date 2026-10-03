"""Multi-pass pagination engine for eazyreport."""
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..expressions.engine import eval_condition, eval_template, eval_text, get_path
from ..expressions.format import escape_html
from ..model.document import Band, ChildBand, DataBand, GroupBand, LayoutDocument, LayoutPage
from ..model.types import LayoutElement, PageMargins, Watermark
from .elements import RenderCtx, element_html, measure_element_height

FONT_LINK = (
    'https://fonts.googleapis.com/css2?'
    'family=Inter:wght@400;500;600;700&'
    'family=Merriweather:wght@400;700&'
    'family=Playfair+Display:wght@600;700&'
    'family=Roboto+Mono:wght@400;500&display=swap'
)


@dataclass
class PlacedElementRecord:
    el: LayoutElement
    x: float
    y: float
    w: float
    h: float
    text: str
    rc: RenderCtx


@dataclass
class PlacedBandRecord:
    band: Band
    x: float
    y: float
    width: float
    height: float
    fill: str
    elements: List[PlacedElementRecord] = field(default_factory=list)


@dataclass
class RenderedPage:
    id: str
    width: float
    height: float
    html: str
    placed_bands: List[PlacedBandRecord] = field(default_factory=list)
    watermark: Watermark = field(default_factory=Watermark)
    margins: PageMargins = field(default_factory=PageMargins)


@dataclass
class RenderOptions:
    params: Optional[Dict[str, Any]] = None
    apply_offset: bool = True
    max_pages: int = 2000


@dataclass
class LaidOutBand:
    html: str
    height: float
    elements: List[PlacedElementRecord] = field(default_factory=list)


def n3(v: float) -> str:
    r = round(v, 3)
    return str(int(r)) if r.is_integer() else f"{r:.3f}".rstrip('0').rstrip('.')


def _at(x: float, y: float, inner_html: str) -> str:
    return (
        f'<div style="position:absolute;left:{n3(x)}mm;top:{n3(y)}mm;box-sizing:border-box;">'
        f'{inner_html}</div>'
    )


def layout_band(
    band: Band,
    ctx: Any,
    width: float,
    fill: str = '',
    fixed_height: Optional[float] = None,
) -> Optional[LaidOutBand]:
    """Layout band elements and calculate auto-growing height if required."""
    if band.visibleExpr and not eval_condition(band.visibleExpr, ctx):
        return None

    rc = RenderCtx(ctx=ctx)
    placed_elements: List[PlacedElementRecord] = []
    max_bottom = band.height if fixed_height is None else fixed_height

    # Calculate actual element heights (for autoHeight elements)
    elem_heights: Dict[str, float] = {}
    for el in band.elements:
        eh = measure_element_height(el, rc)
        elem_heights[el.id] = eh
        if band.canGrow and (el.y + eh > max_bottom):
            max_bottom = el.y + eh

    actual_height = fixed_height if fixed_height is not None else max_bottom

    # Generate HTML for elements
    inner_html_parts: List[str] = []
    for el in band.elements:
        eh = elem_heights.get(el.id, el.h)
        html_str = element_html(el, rc, actual_h=eh)
        if html_str:
            inner_html_parts.append(html_str)
            placed_elements.append(
                PlacedElementRecord(
                    el=el,
                    x=el.x,
                    y=el.y,
                    w=el.w,
                    h=eh,
                    text='',
                    rc=rc,
                )
            )

    band_fill = fill or band.fill
    fill_css = f"background:{band_fill};" if band_fill else ""
    band_html = (
        f'<div class="report-band" style="position:relative;width:{n3(width)}mm;'
        f'height:{n3(actual_height)}mm;{fill_css}overflow:hidden;">'
        f'{"".join(inner_html_parts)}</div>'
    )

    return LaidOutBand(html=band_html, height=actual_height, elements=placed_elements)


class _PageAccumulator:
    def __init__(self, page_id: str, width: float, height: float):
        self.page_id = page_id
        self.width = width
        self.height = height
        self.parts: List[str] = []
        self.placed_bands: List[PlacedBandRecord] = []


def _resolve_data_rows(data_band: DataBand, root_data: Any, params: Dict[str, Any]) -> List[Any]:
    """Extract rows for a data band based on its dataset or data path."""
    rows: Any = None
    path = data_band.dataPath or data_band.dataset
    if path:
        if isinstance(root_data, dict):
            rows = get_path(root_data, path)
            if rows is None and path in root_data:
                rows = root_data[path]
        elif isinstance(root_data, list):
            rows = root_data
    elif isinstance(root_data, list):
        rows = root_data
    elif isinstance(root_data, dict):
        # Look for standard keys like 'items', 'rows', 'lines', 'records', 'data'
        for k in ('items', 'rows', 'lines', 'records', 'details', 'data'):
            if k in root_data and isinstance(root_data[k], list):
                rows = root_data[k]
                break
        if rows is None:
            rows = [root_data]

    if not isinstance(rows, list):
        rows = [rows] if rows is not None else []

    out = list(rows)

    # Filter
    if data_band.filterExpr:
        out = [
            r for r in out
            if eval_condition(data_band.filterExpr, {'row': r, 'item': r, 'params': params})
        ]

    # Sort
    if data_band.sortField:
        key_name = data_band.sortField
        reverse = (data_band.sortDir.lower() == 'desc')
        try:
            out.sort(
                key=lambda x: (
                    get_path(x, key_name) is None,
                    get_path(x, key_name),
                ),
                reverse=reverse,
            )
        except Exception:
            pass

    return out


def paginate_report(
    doc: LayoutDocument,
    data: Any = None,
    params: Optional[Dict[str, Any]] = None,
    options: Optional[RenderOptions] = None,
) -> List[RenderedPage]:
    """Execute two-pass report pagination producing rendered pages with HTML and placed geometry."""
    opts = options or RenderOptions()
    report_params = params or opts.params or {}

    root_data = data if data is not None else {}
    if not doc.pages:
        return []

    tpl_page = doc.pages[0]
    pw = tpl_page.width
    ph = tpl_page.height
    margins = tpl_page.margins

    content_w = pw - margins.left - margins.right
    content_h = ph - margins.top - margins.bottom

    footer_h = tpl_page.pageFooter.height if tpl_page.pageFooter else 0.0
    limit_y = content_h - footer_h

    def run_pass(total_pages_count: int) -> Tuple[List[RenderedPage], int]:
        pages: List[RenderedPage] = []
        cur_accum: Optional[_PageAccumulator] = None
        cur_page_idx = 0
        cur_y = 0.0

        def new_page() -> None:
            nonlocal cur_accum, cur_page_idx, cur_y
            cur_page_idx += 1
            cur_accum = _PageAccumulator(
                page_id=f"page-{cur_page_idx}",
                width=pw,
                height=ph,
            )
            cur_y = 0.0

            # Print PageHeader if present
            if tpl_page.pageHeader:
                ph_ctx = {
                    'data': root_data,
                    'params': report_params,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                }
                laid = layout_band(tpl_page.pageHeader, ph_ctx, content_w)
                if laid:
                    bx = margins.left
                    by = margins.top + cur_y
                    cur_accum.parts.append(_at(bx, by, laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=tpl_page.pageHeader,
                            x=bx,
                            y=by,
                            width=content_w,
                            height=laid.height,
                            fill=tpl_page.pageHeader.fill,
                            elements=laid.elements,
                        )
                    )
                    cur_y += laid.height

            # Print ColumnHeader if present
            if tpl_page.columnHeader:
                ch_ctx = {
                    'data': root_data,
                    'params': report_params,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                }
                laid = layout_band(tpl_page.columnHeader, ch_ctx, content_w)
                if laid:
                    bx = margins.left
                    by = margins.top + cur_y
                    cur_accum.parts.append(_at(bx, by, laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=tpl_page.columnHeader,
                            x=bx,
                            y=by,
                            width=content_w,
                            height=laid.height,
                            fill=tpl_page.columnHeader.fill,
                            elements=laid.elements,
                        )
                    )
                    cur_y += laid.height

        def finish_page() -> None:
            nonlocal cur_accum, cur_page_idx
            if not cur_accum:
                return

            # Print PageFooter at bottom
            if tpl_page.pageFooter:
                pf_ctx = {
                    'data': root_data,
                    'params': report_params,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                }
                laid = layout_band(tpl_page.pageFooter, pf_ctx, content_w)
                if laid:
                    bx = margins.left
                    by = ph - margins.bottom - laid.height
                    cur_accum.parts.append(_at(bx, by, laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=tpl_page.pageFooter,
                            x=bx,
                            y=by,
                            width=content_w,
                            height=laid.height,
                            fill=tpl_page.pageFooter.fill,
                            elements=laid.elements,
                        )
                    )

            # Assemble full page HTML
            page_css = (
                f"position:relative;width:{n3(pw)}mm;height:{n3(ph)}mm;"
                f"background:#ffffff;margin:0 auto 15mm auto;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);"
                f"overflow:hidden;page-break-after:always;"
            )
            full_html = f'<div class="report-page" id="{cur_accum.page_id}" style="{page_css}">{"".join(cur_accum.parts)}</div>'

            pages.append(
                RenderedPage(
                    id=cur_accum.page_id,
                    width=pw,
                    height=ph,
                    html=full_html,
                    placed_bands=cur_accum.placed_bands,
                    watermark=tpl_page.watermark,
                    margins=margins,
                )
            )

        new_page()

        # 1. ReportTitle
        if tpl_page.reportTitle:
            rt_ctx = {
                'data': root_data,
                'params': report_params,
                'Page': cur_page_idx,
                'TotalPages': total_pages_count,
            }
            laid = layout_band(tpl_page.reportTitle, rt_ctx, content_w)
            if laid:
                bx = margins.left
                by = margins.top + cur_y
                cur_accum.parts.append(_at(bx, by, laid.html))
                cur_accum.placed_bands.append(
                    PlacedBandRecord(
                        band=tpl_page.reportTitle,
                        x=bx,
                        y=by,
                        width=content_w,
                        height=laid.height,
                        fill=tpl_page.reportTitle.fill,
                        elements=laid.elements,
                    )
                )
                cur_y += laid.height

        # 2. Data Bands
        for db in tpl_page.data:
            rows = _resolve_data_rows(db, root_data, report_params)
            col_count = max(1, db.columnCount)
            col_spacing = db.columnSpacing
            col_w = db.columnWidth if db.columnWidth > 0 else (content_w - (col_count - 1) * col_spacing) / col_count
            alias = db.alias or 'item'

            # Print DataBand Header if present
            if db.header:
                dbh_ctx = {
                    'data': root_data,
                    'params': report_params,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                    '_rows': rows,
                    '_alias': alias,
                }
                if isinstance(root_data, dict):
                    for k, v in root_data.items():
                        if k not in dbh_ctx:
                            dbh_ctx[k] = v
                h_laid = layout_band(db.header, dbh_ctx, content_w)
                if h_laid:
                    if cur_y + h_laid.height > limit_y:
                        finish_page()
                        new_page()
                    bx = margins.left
                    by = margins.top + cur_y
                    cur_accum.parts.append(_at(bx, by, h_laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=db.header,
                            x=bx,
                            y=by,
                            width=content_w,
                            height=h_laid.height,
                            fill=db.header.fill,
                            elements=h_laid.elements,
                        )
                    )
                    cur_y += h_laid.height

            # Track group values
            prev_group_vals = ['__init__'] * len(db.groupHeaders)

            for row_idx, row in enumerate(rows):
                row_ctx = {
                    'row': row,
                    alias: row,
                    'item': row,
                    'data': root_data,
                    'params': report_params,
                    'Row': row_idx + 1,
                    'rowNumber': row_idx + 1,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                    '_rows': rows,
                    '_alias': alias,
                }
                if isinstance(root_data, dict):
                    for rk, rv in root_data.items():
                        if rk not in row_ctx:
                            row_ctx[rk] = rv
                if isinstance(row, dict):
                    for rk, rv in row.items():
                        row_ctx[rk] = rv

                # Check Group Headers
                for g_idx, gh in enumerate(db.groupHeaders):
                    g_val = eval_text(gh.expression, row_ctx) if gh.expression else ''
                    if g_val != prev_group_vals[g_idx]:
                        prev_group_vals[g_idx] = g_val
                        g_laid = layout_band(gh, row_ctx, content_w)
                        if g_laid:
                            if cur_y + g_laid.height > limit_y:
                                finish_page()
                                new_page()
                            bx = margins.left
                            by = margins.top + cur_y
                            cur_accum.parts.append(_at(bx, by, g_laid.html))
                            cur_accum.placed_bands.append(
                                PlacedBandRecord(
                                    band=gh,
                                    x=bx,
                                    y=by,
                                    width=content_w,
                                    height=g_laid.height,
                                    fill=gh.fill,
                                    elements=g_laid.elements,
                                )
                            )
                            cur_y += g_laid.height

                # Layout Data Row
                laid = layout_band(db, row_ctx, col_w)
                if laid:
                    if cur_y + laid.height > limit_y:
                        finish_page()
                        new_page()

                    col_idx = row_idx % col_count if col_count > 1 else 0
                    x_offset = col_idx * (col_w + col_spacing)
                    bx = margins.left + x_offset
                    by = margins.top + cur_y

                    cur_accum.parts.append(_at(bx, by, laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=db,
                            x=bx,
                            y=by,
                            width=col_w,
                            height=laid.height,
                            fill=db.fill,
                            elements=laid.elements,
                        )
                    )

                    # Only advance vertical cursor on the last column or single column
                    if col_count == 1 or col_idx == col_count - 1:
                        cur_y += laid.height

            # Print DataBand Footer if present
            if db.footer:
                dbf_ctx = {
                    'data': root_data,
                    'params': report_params,
                    'Page': cur_page_idx,
                    'TotalPages': total_pages_count,
                    '_rows': rows,
                    '_alias': alias,
                }
                if isinstance(root_data, dict):
                    for k, v in root_data.items():
                        if k not in dbf_ctx:
                            dbf_ctx[k] = v
                f_laid = layout_band(db.footer, dbf_ctx, content_w)
                if f_laid:
                    if cur_y + f_laid.height > limit_y:
                        finish_page()
                        new_page()
                    bx = margins.left
                    by = margins.top + cur_y
                    cur_accum.parts.append(_at(bx, by, f_laid.html))
                    cur_accum.placed_bands.append(
                        PlacedBandRecord(
                            band=db.footer,
                            x=bx,
                            y=by,
                            width=content_w,
                            height=f_laid.height,
                            fill=db.footer.fill,
                            elements=f_laid.elements,
                        )
                    )
                    cur_y += f_laid.height

            # Child Bands (e.g. fillUnusedSpace)
            for cb in db.childBands:
                rem_h = limit_y - cur_y
                if cb.fillUnusedSpace and rem_h > 0:
                    cb_ctx = {
                        'data': root_data,
                        'params': report_params,
                        'Page': cur_page_idx,
                        'TotalPages': total_pages_count,
                    }
                    laid = layout_band(cb, cb_ctx, content_w, fixed_height=rem_h)
                    if laid:
                        bx = margins.left
                        by = margins.top + cur_y
                        cur_accum.parts.append(_at(bx, by, laid.html))
                        cur_accum.placed_bands.append(
                            PlacedBandRecord(
                                band=cb,
                                x=bx,
                                y=by,
                                width=content_w,
                                height=laid.height,
                                fill=cb.fill,
                                elements=laid.elements,
                            )
                        )
                        cur_y += laid.height
                elif not cb.fillUnusedSpace:
                    cb_ctx = {
                        'data': root_data,
                        'params': report_params,
                        'Page': cur_page_idx,
                        'TotalPages': total_pages_count,
                    }
                    laid = layout_band(cb, cb_ctx, content_w)
                    if laid:
                        if cur_y + laid.height > limit_y:
                            finish_page()
                            new_page()
                        bx = margins.left
                        by = margins.top + cur_y
                        cur_accum.parts.append(_at(bx, by, laid.html))
                        cur_accum.placed_bands.append(
                            PlacedBandRecord(
                                band=cb,
                                x=bx,
                                y=by,
                                width=content_w,
                                height=laid.height,
                                fill=cb.fill,
                                elements=laid.elements,
                            )
                        )
                        cur_y += laid.height

        # 3. ReportSummary
        if tpl_page.reportSummary:
            rs_ctx = {
                'data': root_data,
                'params': report_params,
                'Page': cur_page_idx,
                'TotalPages': total_pages_count,
            }
            laid = layout_band(tpl_page.reportSummary, rs_ctx, content_w)
            if laid:
                if cur_y + laid.height > limit_y:
                    finish_page()
                    new_page()
                bx = margins.left
                by = margins.top + cur_y
                cur_accum.parts.append(_at(bx, by, laid.html))
                cur_accum.placed_bands.append(
                    PlacedBandRecord(
                        band=tpl_page.reportSummary,
                        x=bx,
                        y=by,
                        width=content_w,
                        height=laid.height,
                        fill=tpl_page.reportSummary.fill,
                        elements=laid.elements,
                    )
                )
                cur_y += laid.height

        finish_page()
        return pages, cur_page_idx

    # Pass 1: compute total pages
    _, initial_count = run_pass(1)

    # Pass 2: compute final pages with correct TotalPages resolved
    final_pages, _ = run_pass(initial_count)
    return final_pages


def render_html_document(pages: List[RenderedPage], title: str = 'Report') -> str:
    """Wrap rendered pages into a complete standalone HTML document with print styles."""
    pages_html = '\n'.join(p.html for p in pages)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{escape_html(title)}</title>
<link rel="stylesheet" href="{FONT_LINK}"/>
<style>
* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}
body {{
  background: #f1f5f9;
  font-family: 'Inter', sans-serif;
  color: #0f172a;
  padding: 20px 0;
  -webkit-font-smoothing: antialiased;
}}
.report-page {{
  position: relative;
  background: #ffffff;
  margin: 0 auto 20px auto;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
}}
@media print {{
  body {{
    background: transparent;
    padding: 0;
  }}
  .report-page {{
    margin: 0;
    box-shadow: none;
    page-break-after: always;
  }}
  @page {{
    margin: 0;
  }}
}}
</style>
</head>
<body>
{pages_html}
</body>
</html>
"""
