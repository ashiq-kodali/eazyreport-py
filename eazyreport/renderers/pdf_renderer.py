"""Native PDF generator for eazyreport using ReportLab."""
import base64
import io
import math
import os
import re
from typing import Any, Dict, List, Optional

from ..engine.barcode import is_two_dimensional
from ..engine.elements import field_text
from ..engine.paginate import RenderedPage
from ..model.types import LayoutElement

MM_TO_PT = 72.0 / 25.4  # ~2.834645669


def parse_color_hex(hex_str: Optional[str], default: str = '#000000') -> str:
    """Normalize hex color string."""
    if not hex_str or hex_str.lower() in ('transparent', 'none', ''):
        return ''
    s = hex_str.strip()
    if s.startswith('#'):
        c = s[1:]
        if len(c) == 3:
            return '#' + ''.join(x * 2 for x in c)
        if len(c) == 6:
            return s
        if len(c) == 8:
            return '#' + c[2:]  # Strip alpha if ARGB
    return s


def resolve_reportlab_font(family: str, bold: bool, italic: bool) -> str:
    """Map web font family and styles to standard PDF 14 fonts."""
    fam = (family or '').lower()
    if 'times' in fam or 'serif' in fam:
        if bold and italic:
            return 'Times-BoldItalic'
        if bold:
            return 'Times-Bold'
        if italic:
            return 'Times-Italic'
        return 'Times-Roman'
    elif 'mono' in fam or 'courier' in fam or 'code' in fam:
        if bold and italic:
            return 'Courier-BoldOblique'
        if bold:
            return 'Courier-Bold'
        if italic:
            return 'Courier-Oblique'
        return 'Courier'
    else:
        # Default to Helvetica
        if bold and italic:
            return 'Helvetica-BoldOblique'
        if bold:
            return 'Helvetica-Bold'
        if italic:
            return 'Helvetica-Oblique'
        return 'Helvetica'


def render_pdf_bytes(pages: List[RenderedPage], title: str = 'Report') -> bytes:
    """Render a list of paginated RenderedPage objects into binary PDF bytes."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    if not pages:
        # Return empty PDF
        c = canvas.Canvas(buffer, pagesize=(595.27, 841.89))
        c.save()
        return buffer.getvalue()

    first_page = pages[0]
    first_w_pt = first_page.width * MM_TO_PT
    first_h_pt = first_page.height * MM_TO_PT

    c = canvas.Canvas(buffer, pagesize=(first_w_pt, first_h_pt))
    c.setTitle(title)

    for page_idx, page in enumerate(pages):
        pw_pt = page.width * MM_TO_PT
        ph_pt = page.height * MM_TO_PT
        c.setPageSize((pw_pt, ph_pt))

        # 1. Draw Watermark under content if not onTop
        if page.watermark and page.watermark.enabled and not page.watermark.onTop:
            _draw_watermark(c, page.watermark, pw_pt, ph_pt)

        # 2. Draw Bands and Elements
        for pb in page.placed_bands:
            band_x_pt = pb.x * MM_TO_PT
            band_y_pt = pb.y * MM_TO_PT
            band_w_pt = pb.width * MM_TO_PT
            band_h_pt = pb.height * MM_TO_PT

            # Draw band fill background if present
            band_fill = parse_color_hex(pb.fill)
            if band_fill:
                c.saveState()
                c.setFillColor(HexColor(band_fill))
                # ReportLab y is inverted: origin at bottom-left
                canvas_band_y = ph_pt - (band_y_pt + band_h_pt)
                c.rect(band_x_pt, canvas_band_y, band_w_pt, band_h_pt, fill=1, stroke=0)
                c.restoreState()

            # Draw elements within the band
            for pe in pb.elements:
                el = pe.el
                el_x_pt = band_x_pt + (pe.x * MM_TO_PT)
                el_y_pt = band_y_pt + (pe.y * MM_TO_PT)
                el_w_pt = pe.w * MM_TO_PT
                el_h_pt = pe.h * MM_TO_PT
                canvas_y = ph_pt - (el_y_pt + el_h_pt)

                # 1. Box / Shape Element
                if el.type in ('box', 'shape'):
                    _draw_box(c, el, el_x_pt, canvas_y, el_w_pt, el_h_pt)

                # 2. Line Element
                elif el.type == 'line':
                    _draw_line(c, el, el_x_pt, canvas_y, el_w_pt, el_h_pt)

                # 3. Image Element
                elif el.type == 'image':
                    _draw_image(c, el, pe.rc, el_x_pt, canvas_y, el_w_pt, el_h_pt)

                # 4. Barcode / QR Code Element
                elif el.type == 'barcode':
                    _draw_barcode(c, el, pe.rc, el_x_pt, canvas_y, el_w_pt, el_h_pt)

                # 5. Text Element
                else:
                    _draw_text(c, el, pe.rc, el_x_pt, canvas_y, el_w_pt, el_h_pt)

        # 3. Draw Watermark over content if onTop
        if page.watermark and page.watermark.enabled and page.watermark.onTop:
            _draw_watermark(c, page.watermark, pw_pt, ph_pt)

        c.showPage()

    c.save()
    return buffer.getvalue()


def _draw_box(c: Any, el: LayoutElement, x: float, y: float, w: float, h: float) -> None:
    from reportlab.lib.colors import HexColor

    b = el.box
    bg = parse_color_hex(b.background)
    border_col = parse_color_hex(b.borderColor)
    border_w = b.borderWidth

    c.saveState()
    if bg:
        c.setFillColor(HexColor(bg))
    else:
        c.setFillColor(HexColor('#ffffff'), alpha=0)

    has_border = border_w > 0 and border_col and (b.borderTop or b.borderRight or b.borderBottom or b.borderLeft)
    if has_border:
        c.setStrokeColor(HexColor(border_col))
        c.setLineWidth(border_w)
    else:
        c.setStrokeColor(HexColor('#000000'), alpha=0)

    r_pt = b.borderRadius * MM_TO_PT
    if r_pt > 0:
        c.roundRect(x, y, w, h, r_pt, fill=1 if bg else 0, stroke=1 if has_border else 0)
    else:
        c.rect(x, y, w, h, fill=1 if bg else 0, stroke=1 if has_border else 0)

    c.restoreState()


def _draw_line(c: Any, el: LayoutElement, x: float, y: float, w: float, h: float) -> None:
    from reportlab.lib.colors import HexColor

    color = parse_color_hex(el.strokeColor, '#cbd5e1')
    lw = el.strokeWidth or 1.0

    c.saveState()
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(lw)

    if el.orientation == 'vertical':
        c.line(x, y, x, y + h)
    else:
        c.line(x, y + h, x + w, y + h)

    c.restoreState()


def _draw_image(c: Any, el: LayoutElement, rc: Any, x: float, y: float, w: float, h: float) -> None:
    from reportlab.lib.utils import ImageReader

    src = el.src
    if not src:
        return

    try:
        if src.startswith('data:image'):
            # Base64 image
            idx = src.find('base64,')
            if idx != -1:
                img_data = base64.b64decode(src[idx + 7:])
                img_reader = ImageReader(io.BytesIO(img_data))
                c.drawImage(img_reader, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
        elif os.path.exists(src):
            c.drawImage(src, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass


def _draw_barcode(c: Any, el: LayoutElement, rc: Any, x: float, y: float, w: float, h: float) -> None:
    from reportlab.lib.colors import HexColor

    val = el.barcodeValue or el.content or '12345678'
    bar_col = parse_color_hex(el.barColor, '#000000')
    bg_col = parse_color_hex(el.barcodeBackground, '#ffffff')

    # Draw background
    if bg_col:
        c.saveState()
        c.setFillColor(HexColor(bg_col))
        c.rect(x, y, w, h, fill=1, stroke=0)
        c.restoreState()

    if is_two_dimensional(el.symbology):
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=1,
            )
            qr.add_data(val)
            qr.make(fit=True)
            matrix = qr.get_matrix()
            rows = len(matrix)
            cols = len(matrix[0]) if rows > 0 else 1

            cell_w = w / cols
            cell_h = h / rows
            c.saveState()
            c.setFillColor(HexColor(bar_col))
            for r_idx, row in enumerate(matrix):
                for c_idx, cell in enumerate(row):
                    if cell:
                        cx = x + (c_idx * cell_w)
                        cy = y + ((rows - 1 - r_idx) * cell_h)
                        c.rect(cx, cy, cell_w, cell_h, fill=1, stroke=0)
            c.restoreState()
        except Exception:
            pass
    else:
        # Simple 1D barcode simulation in PDF canvas
        from ..engine.barcode import _encode_code128
        pattern = _encode_code128(val)
        total_modules = sum(int(d) for d in pattern)
        if total_modules <= 0:
            return

        c.saveState()
        c.setFillColor(HexColor(bar_col))
        mod_w = w / total_modules
        curr_x = x
        is_bar = True
        bar_h = h * 0.8 if el.showText else h

        for digit in pattern:
            w_block = int(digit) * mod_w
            if is_bar:
                c.rect(curr_x, y + (h - bar_h), w_block, bar_h, fill=1, stroke=0)
            curr_x += w_block
            is_bar = not is_bar

        if el.showText:
            c.setFont('Courier', 7)
            c.drawCentredString(x + w / 2, y + 2, val)

        c.restoreState()


def _draw_text(c: Any, el: LayoutElement, rc: Any, x: float, y: float, w: float, h: float) -> None:
    from reportlab.lib.colors import HexColor

    txt = field_text(el, rc)
    if not txt:
        return

    s = el.style
    b = el.box

    # Box background & borders
    _draw_box(c, el, x, y, w, h)

    font_name = resolve_reportlab_font(s.fontFamily, s.bold, s.italic)
    font_size_pt = s.fontSize * rc.font_scale
    color = parse_color_hex(s.color, '#0f172a')

    c.saveState()
    c.setFont(font_name, font_size_pt)
    c.setFillColor(HexColor(color))

    pad_l = b.paddingLeft * MM_TO_PT
    pad_r = b.paddingRight * MM_TO_PT
    pad_t = b.paddingTop * MM_TO_PT
    pad_b = b.paddingBottom * MM_TO_PT

    avail_w = max(1.0, w - pad_l - pad_r)
    lines = txt.split('\n')
    line_h_pt = font_size_pt * s.lineHeight
    total_txt_h = len(lines) * line_h_pt

    # Vertical alignment
    if s.vAlign == 'middle':
        start_y = y + (h - total_txt_h) / 2 + (len(lines) - 1) * line_h_pt
    elif s.vAlign == 'bottom':
        start_y = y + pad_b + (len(lines) - 1) * line_h_pt
    else:  # top
        start_y = y + h - pad_t - font_size_pt

    curr_y = start_y
    for line in lines:
        if s.align == 'center':
            draw_x = x + pad_l + (avail_w / 2)
            c.drawCentredString(draw_x, curr_y, line)
        elif s.align == 'right':
            draw_x = x + w - pad_r
            c.drawRightString(draw_x, curr_y, line)
        else:
            draw_x = x + pad_l
            c.drawString(draw_x, curr_y, line)

        curr_y -= line_h_pt

    c.restoreState()


def _draw_watermark(c: Any, wm: Any, pw: float, ph: float) -> None:
    from reportlab.lib.colors import HexColor

    if not wm.text:
        return

    c.saveState()
    c.translate(pw / 2, ph / 2)
    c.rotate(wm.angle)

    color_hex = parse_color_hex(wm.color, '#94a3b8')
    c.setFillColor(HexColor(color_hex), alpha=wm.opacity)
    c.setFont('Helvetica-Bold', wm.fontSize)
    c.drawCentredString(0, -wm.fontSize / 3, wm.text)
    c.restoreState()
