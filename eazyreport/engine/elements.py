"""Visual element evaluation, styling, and HTML rendering."""
import math
import re
from dataclasses import dataclass
from typing import Any, List, Optional

from ..expressions.engine import eval_condition, eval_template, eval_text, get_path
from ..expressions.format import escape_html, format_value
from ..model.types import BoxStyle, LayoutElement, TextStyle
from .barcode import barcode_html
from .chart import chart_svg
from .logic import evaluate_rule

PT_TO_MM = 25.4 / 72.0


@dataclass
class RenderCtx:
    ctx: Any
    mode: str = 'data'
    blank_value: bool = False
    auto_height: bool = False
    font_scale: float = 1.0
    script_override_text: Optional[str] = None
    script_override_color: Optional[str] = None
    script_override_background: Optional[str] = None


def n3(v: float) -> str:
    """Format floating point numbers to max 3 decimal places without trailing zeros."""
    r = round(v, 3)
    return str(int(r)) if r.is_integer() else f"{r:.3f}".rstrip('0').rstrip('.')


def font_family_css(family: str) -> str:
    clean = (family or 'Inter').replace("'", "")
    mono = bool(re.search(r'mono|courier', family, re.IGNORECASE))
    serif = bool(re.search(r'times|georgia|merriweather|playfair', family, re.IGNORECASE))
    fallback = 'monospace' if mono else ('serif' if serif else 'sans-serif')
    return f"'{clean}', {fallback}"


def text_css(s: TextStyle, scale: float = 1.0) -> str:
    deco = []
    if s.underline:
        deco.append('underline')
    if s.strike:
        deco.append('line-through')

    parts = [
        f"font-family:{font_family_css(s.fontFamily)}",
        f"font-size:{n3(s.fontSize * scale)}pt",
        f"font-weight:{700 if s.bold else 400}",
        f"font-style:{'italic' if s.italic else 'normal'}",
        f"color:{s.color}",
        f"line-height:{n3(s.lineHeight)}",
    ]
    if deco:
        parts.append(f"text-decoration:{' '.join(deco)}")
    if s.letterSpacing > 0:
        parts.append(f"letter-spacing:{n3(s.letterSpacing)}pt")

    return ';'.join(parts)


def stroke_css(b: BoxStyle) -> List[str]:
    if b.borderWidth <= 0 or b.borderStyle == 'none':
        return []
    stroke = f"{n3(b.borderWidth)}pt {b.borderStyle} {b.borderColor}"
    res = []
    if b.borderTop:
        res.append(f"border-top:{stroke}")
    if b.borderRight:
        res.append(f"border-right:{stroke}")
    if b.borderBottom:
        res.append(f"border-bottom:{stroke}")
    if b.borderLeft:
        res.append(f"border-left:{stroke}")
    return res


def box_css(b: BoxStyle, with_padding: bool = True) -> str:
    parts = []
    if b.background:
        parts.append(f"background:{b.background}")
    parts.extend(stroke_css(b))
    if b.borderRadius > 0:
        parts.append(f"border-radius:{n3(b.borderRadius)}mm")
    if with_padding:
        parts.append(
            f"padding:{n3(b.paddingTop)}mm {n3(b.paddingRight)}mm {n3(b.paddingBottom)}mm {n3(b.paddingLeft)}mm"
        )
    return ';'.join(parts)


def _row_value(row: Any, path: str, alias: str = 'item') -> Any:
    clean_p = path
    if clean_p.startswith(f"{alias}."):
        clean_p = clean_p[len(alias) + 1:]
    elif clean_p.startswith("item."):
        clean_p = clean_p[5:]
    val = get_path(row, clean_p)
    if val is None and isinstance(row, dict):
        val = row.get(clean_p)
    return val


def aggregate(kind: str, rows: List[Any], path: str, alias: str = 'item') -> Union[int, float]:
    """Calculate aggregate function across rows."""
    if kind == 'count':
        return len(rows)
    vals = []
    for r in rows:
        v = _row_value(r, path, alias)
        if v is not None and v != '':
            try:
                vals.append(float(v))
            except (ValueError, TypeError):
                pass
    if not vals:
        return 0

    if kind == 'sum':
        s = sum(vals)
        return int(s) if s.is_integer() else s
    if kind == 'avg':
        a = sum(vals) / len(vals)
        return int(a) if a.is_integer() else a
    if kind == 'min':
        m = min(vals)
        return int(m) if m.is_integer() else m
    if kind == 'max':
        m = max(vals)
        return int(m) if m.is_integer() else m
    return 0


def field_text(el: LayoutElement, rc: RenderCtx) -> str:
    """Evaluate raw text content or bound field for an element."""
    if rc.script_override_text is not None:
        return rc.script_override_text

    raw_val: Any = None
    if el.aggregate and el.aggregate != 'none':
        rows = rc.ctx.get('_rows', []) if isinstance(rc.ctx, dict) else []
        alias = rc.ctx.get('_alias', 'item') if isinstance(rc.ctx, dict) else 'item'
        raw_val = aggregate(el.aggregate, rows, el.field_name, alias)
    elif el.field_name:
        raw_val = get_path(rc.ctx, el.field_name)
        if raw_val is None and isinstance(rc.ctx, dict):
            row_obj = rc.ctx.get('row', rc.ctx.get('item'))
            if row_obj:
                raw_val = _row_value(row_obj, el.field_name)
            if raw_val is None and 'data' in rc.ctx:
                raw_val = get_path(rc.ctx['data'], el.field_name)
    elif el.content:
        raw_val = eval_text(el.content, rc.ctx)

    if raw_val is None or raw_val == '':
        return el.nullText

    if el.hideZeros:
        try:
            if float(raw_val) == 0:
                return ''
        except (ValueError, TypeError):
            pass

    # Format the value
    fmt_spec = {
        'format': el.valueFormat.format,
        'decimals': el.valueFormat.decimals,
        'thousands': el.valueFormat.thousands,
        'currency': el.valueFormat.currency,
        'datePattern': el.valueFormat.datePattern,
    }
    formatted = format_value(raw_val, fmt_spec, el.dataType)
    return f"{el.prefix}{formatted}{el.suffix}"


def measure_element_height(el: LayoutElement, rc: RenderCtx) -> float:
    """Estimate the rendered height in millimeters for an element."""
    if not el.autoHeight:
        return el.h

    txt = field_text(el, rc)
    if not txt:
        return el.h

    # Approximate characters per line based on width and font size
    # 1pt = 0.352778 mm. Average character width ~ 0.5 * font_size
    char_w_mm = (el.style.fontSize * PT_TO_MM) * 0.52
    available_w_mm = max(5.0, el.w - (el.box.paddingLeft + el.box.paddingRight))
    chars_per_line = max(1, int(available_w_mm / char_w_mm))

    lines = 0
    for para in txt.split('\n'):
        line_len = len(para)
        lines += max(1, math.ceil(line_len / chars_per_line))

    line_h_mm = (el.style.fontSize * PT_TO_MM) * el.style.lineHeight
    padding_h_mm = el.box.paddingTop + el.box.paddingBottom
    total_h = (lines * line_h_mm) + padding_h_mm

    if el.minHeight is not None:
        total_h = max(total_h, el.minHeight)
    if el.maxHeight is not None:
        total_h = min(total_h, el.maxHeight)

    return max(el.h, total_h)


def element_html(el: LayoutElement, rc: RenderCtx, actual_h: Optional[float] = None) -> str:
    """Generate HTML snippet for an element positioned inside a band."""
    # Check visibleExpr
    if el.visibleExpr and not eval_condition(el.visibleExpr, rc.ctx):
        return ''

    # Evaluate FastReport logic rules
    override_bg = rc.script_override_background
    override_color = rc.script_override_color
    override_weight = None
    override_style = None
    override_val = None

    for rule in el.rules:
        res = evaluate_rule(rule, rc.ctx)
        if res.triggered:
            if res.action == 'hide':
                return ''
            elif res.action == 'background':
                override_bg = res.action_value or '#ffe4e6'
            elif res.action == 'text_color':
                override_color = res.action_value or '#e11d48'
            elif res.action == 'font_weight':
                override_weight = res.action_value
            elif res.action == 'font_style':
                override_style = res.action_value
            elif res.action == 'value':
                override_val = res.action_value

    h_mm = actual_h if actual_h is not None else el.h
    base_style = [
        'position:absolute',
        f"left:{n3(el.x)}mm",
        f"top:{n3(el.y)}mm",
        f"width:{n3(el.w)}mm",
        f"height:{n3(h_mm)}mm",
        'box-sizing:border-box',
    ]

    # Handle Box / Shape
    if el.type in ('box', 'shape'):
        b = el.box
        if override_bg:
            b = BoxStyle(
                background=override_bg,
                borderColor=b.borderColor,
                borderWidth=b.borderWidth,
                borderStyle=b.borderStyle,
                borderRadius=b.borderRadius,
                borderTop=b.borderTop,
                borderRight=b.borderRight,
                borderBottom=b.borderBottom,
                borderLeft=b.borderLeft,
                paddingTop=b.paddingTop,
                paddingRight=b.paddingRight,
                paddingBottom=b.paddingBottom,
                paddingLeft=b.paddingLeft,
            )
        b_css = box_css(b, with_padding=True)
        css_str = ';'.join(base_style + ([b_css] if b_css else []))
        return f'<div class="report-box" style="{css_str}"></div>'

    # Handle Line
    if el.type == 'line':
        color = el.strokeColor or '#000000'
        w_pt = el.strokeWidth or 1.0
        dash = el.strokeDash or 'solid'
        line_parts = base_style.copy()
        if el.orientation == 'vertical':
            line_parts.append(f"border-left:{n3(w_pt)}pt {dash} {color}")
            line_parts.append('width:0mm')
        else:
            line_parts.append(f"border-top:{n3(w_pt)}pt {dash} {color}")
            line_parts.append('height:0mm')
        return f'<div class="report-line" style="{";".join(line_parts)}"></div>'

    # Handle Image
    if el.type == 'image':
        src = el.src
        if src.startswith('{{'):
            src = eval_text(src, rc.ctx)
        fit = el.fit or 'contain'
        opacity = el.opacity if el.opacity is not None else 1.0
        img_css = ';'.join(base_style + [f"opacity:{n3(opacity)}"])
        return (
            f'<div class="report-image" style="{img_css}">'
            f'<img src="{escape_html(src)}" style="width:100%;height:100%;object-fit:{fit};display:block;"/>'
            f'</div>'
        )

    # Handle Barcode / QR Code
    if el.type == 'barcode':
        val = el.barcodeValue or el.content
        if val.startswith('{{'):
            val = eval_text(val, rc.ctx)
        elif el.field_name:
            val = str(get_path(rc.ctx, el.field_name) or '')
        b_html = barcode_html(el, val)
        return f'<div class="report-barcode-el" style="{";".join(base_style)}">{b_html}</div>'

    # Handle Chart
    if el.type == 'chart':
        raw_labels = get_path(rc.ctx, el.labelsField) if el.labelsField else []
        raw_values = get_path(rc.ctx, el.valuesField) if el.valuesField else []
        labels = [str(x) for x in raw_labels] if isinstance(raw_labels, list) else []
        values = [float(x) for x in raw_values] if isinstance(raw_values, list) else []
        svg = chart_svg(el, labels, values)
        return f'<div class="report-chart-el" style="{";".join(base_style)}">{svg}</div>'

    # Default: Text Element
    t_style = el.style
    if override_color:
        t_style = TextStyle(
            fontFamily=t_style.fontFamily,
            fontSize=t_style.fontSize,
            bold=t_style.bold if override_weight is None else override_weight == 'bold',
            italic=t_style.italic if override_style is None else override_style == 'italic',
            underline=t_style.underline,
            strike=t_style.strike,
            color=override_color,
            lineHeight=t_style.lineHeight,
            letterSpacing=t_style.letterSpacing,
            align=t_style.align,
            vAlign=t_style.vAlign,
        )

    b_style = el.box
    if override_bg:
        b_style = BoxStyle(
            background=override_bg,
            borderColor=b_style.borderColor,
            borderWidth=b_style.borderWidth,
            borderStyle=b_style.borderStyle,
            borderRadius=b_style.borderRadius,
            borderTop=b_style.borderTop,
            borderRight=b_style.borderRight,
            borderBottom=b_style.borderBottom,
            borderLeft=b_style.borderLeft,
            paddingTop=b_style.paddingTop,
            paddingRight=b_style.paddingRight,
            paddingBottom=b_style.paddingBottom,
            paddingLeft=b_style.paddingLeft,
        )

    # Vertical alignment flex container
    v_align_css = {
        'top': 'flex-start',
        'middle': 'center',
        'bottom': 'flex-end',
    }.get(t_style.vAlign, 'flex-start')

    txt = override_val if override_val is not None else field_text(el, rc)
    t_css = text_css(t_style, rc.font_scale)
    b_css = box_css(b_style, with_padding=True)

    elem_styles = base_style + [
        t_css,
        b_css,
        f"text-align:{t_style.align}",
        'display:flex',
        'flex-direction:column',
        f"justify-content:{v_align_css}",
        'overflow:hidden',
        'word-break:break-word',
    ]

    # Convert newlines to <br/>
    html_content = '<br/>'.join(escape_html(line) for line in txt.split('\n'))

    return f'<div class="report-text" style="{";".join(filter(None, elem_styles))}">{html_content}</div>'
