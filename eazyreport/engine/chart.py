"""Pure Python vector SVG chart generator."""
import math
from typing import List, Union

from ..expressions.format import escape_html, format_number
from ..model.types import LayoutElement


def chart_svg(el: LayoutElement, labels: List[str], values: List[Union[int, float]]) -> str:
    """Render a standalone responsive vector chart as SVG. Units inside the SVG are 0.1 mm."""
    w = float(el.w * 10)
    h = float(el.h * 10)
    pt = 3.528  # 1pt in 0.1 mm
    fs = el.style.fontSize * pt
    font = f'font-family="{escape_html(el.style.fontFamily)}, sans-serif" fill="{el.style.color}"'

    def color(i: int) -> str:
        colors = el.colors or ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
        return colors[i % len(colors)]

    parts: List[str] = []
    top = 4.0

    if el.title:
        parts.append(
            f'<text x="{w / 2}" y="{top + fs * 1.1}" text-anchor="middle" font-size="{fs * 1.15}" font-weight="700" {font}>{escape_html(el.title)}</text>'
        )
        top += fs * 1.6

    if not values:
        parts.append(
            f'<text x="{w / 2}" y="{h / 2}" text-anchor="middle" font-size="{fs}" {font}>No data</text>'
        )
        return _wrap(w, h, parts)

    if el.chartType in ('pie', 'doughnut'):
        legend_w = min(w * 0.4, 400.0) if el.showLegend else 0.0
        cx = (w - legend_w) / 2
        cy = top + (h - top) / 2
        r = max(10.0, min((w - legend_w) / 2, (h - top) / 2) - 8)
        total = sum(max(0.0, float(v)) for v in values)
        if total == 0:
            total = 1.0

        a0 = -math.pi / 2
        for i, val in enumerate(values):
            v = float(val)
            a1 = a0 + (max(0.0, v) / total) * math.pi * 2
            large = 1 if (a1 - a0 > math.pi) else 0

            def p(a: float, rr: float) -> str:
                return f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}"

            if len(values) == 1:
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color(i)}"/>')
            else:
                parts.append(
                    f'<path d="M{cx},{cy} L{p(a0, r)} A{r},{r} 0 {large} 1 {p(a1, r)} Z" fill="{color(i)}" stroke="#fff" stroke-width="3"/>'
                )

            if el.showValues and v > 0:
                am = (a0 + a1) / 2
                lr = r * 0.78 if el.chartType == 'doughnut' else r * 0.62
                pct = int(round((v / total) * 100))
                parts.append(
                    f'<text x="{cx + lr * math.cos(am):.2f}" y="{cy + lr * math.sin(am) + fs / 3:.2f}" text-anchor="middle" font-size="{fs * 0.9}" font-family="sans-serif" fill="#fff" font-weight="700">{pct}%</text>'
                )
            a0 = a1

        if el.chartType == 'doughnut':
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r * 0.55:.2f}" fill="#fff"/>')

        if el.showLegend:
            _legend(parts, labels, w - legend_w + 10, top + 10, fs, font, color)

        return _wrap(w, h, parts)

    # Bar (horizontal) vs Column / Line / Area (vertical)
    horizontal = el.chartType == 'bar'
    max_val = max(float(v) for v in values)
    min_val = min(float(v) for v in values)
    chart_max = max(0.0, max_val)
    chart_min = min(0.0, min_val)
    val_range = (chart_max - chart_min) if (chart_max - chart_min != 0) else 1.0

    max_label_len = max(len(l) for l in labels) if labels else 0
    label_space = min(w * 0.3, max_label_len * fs * 0.55 + 10) if horizontal else fs * 1.8
    value_space = fs * 5.0 if horizontal else fs * 5.5

    plot_x = label_space if horizontal else value_space
    plot_y = (top + 6) if horizontal else (top + fs)
    plot_w = (w - label_space - fs * 4) if horizontal else (w - value_space - 10)
    plot_h = (h - top - 12) if horizontal else (h - top - fs - label_space)

    def scale(v: Union[int, float]) -> float:
        return ((float(v) - chart_min) / val_range) * (plot_w if horizontal else plot_h)

    if el.showGrid:
        for i in range(5):
            v = chart_min + (val_range * i) / 4.0
            if horizontal:
                x = plot_x + scale(v)
                parts.append(
                    f'<line x1="{x:.2f}" y1="{plot_y:.2f}" x2="{x:.2f}" y2="{plot_y + plot_h:.2f}" stroke="#e2e8f0" stroke-width="2"/>'
                )
            else:
                y = plot_y + plot_h - scale(v)
                parts.append(
                    f'<line x1="{plot_x:.2f}" y1="{y:.2f}" x2="{plot_x + plot_w:.2f}" y2="{y:.2f}" stroke="#e2e8f0" stroke-width="2"/>'
                )
                fmt_v = format_number(v, 1 if v % 1 != 0 else 0)
                parts.append(
                    f'<text x="{plot_x - 6:.2f}" y="{y + fs / 3:.2f}" text-anchor="end" font-size="{fs * 0.85}" {font}>{fmt_v}</text>'
                )

    n = len(values)
    slot = (plot_h if horizontal else plot_w) / max(1, n)

    if el.chartType in ('line', 'area'):
        pts = []
        for i, val in enumerate(values):
            pts.append((plot_x + slot * (i + 0.5), plot_y + plot_h - scale(val)))

        if el.chartType == 'area':
            base = plot_y + plot_h - scale(0)
            pts_str = ' '.join(f"L{p[0]:.2f},{p[1]:.2f}" for p in pts)
            parts.append(
                f'<path d="M{pts[0][0]:.2f},{base:.2f} {pts_str} L{pts[-1][0]:.2f},{base:.2f} Z" fill="{color(0)}" opacity="0.25"/>'
            )

        poly_pts = ' '.join(f"{p[0]:.2f},{p[1]:.2f}" for p in pts)
        parts.append(
            f'<polyline points="{poly_pts}" fill="none" stroke="{color(0)}" stroke-width="6" stroke-linejoin="round"/>'
        )

        for i, p in enumerate(pts):
            parts.append(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="7" fill="{color(0)}"/>')
            if el.showValues:
                val = values[i]
                fmt_v = format_number(val, 2 if val % 1 != 0 else 0)
                parts.append(
                    f'<text x="{p[0]:.2f}" y="{p[1] - 12:.2f}" text-anchor="middle" font-size="{fs * 0.85}" {font}>{fmt_v}</text>'
                )
    else:
        # Bars or Columns
        for i, val in enumerate(values):
            bar = slot * 0.62
            val_len = abs(scale(val) - scale(0))
            if horizontal:
                y = plot_y + slot * i + (slot - bar) / 2
                x = plot_x + min(scale(0), scale(val))
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{val_len:.2f}" height="{bar:.2f}" fill="{color(i)}" rx="3"/>'
                )
                if el.showValues:
                    fmt_v = format_number(val, 2 if val % 1 != 0 else 0)
                    parts.append(
                        f'<text x="{x + val_len + 6:.2f}" y="{y + bar / 2 + fs / 3:.2f}" font-size="{fs * 0.85}" {font}>{fmt_v}</text>'
                    )
            else:
                x = plot_x + slot * i + (slot - bar) / 2
                y = plot_y + plot_h - max(scale(0), scale(val))
                parts.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar:.2f}" height="{val_len:.2f}" fill="{color(i)}" rx="3"/>'
                )
                if el.showValues:
                    fmt_v = format_number(val, 2 if val % 1 != 0 else 0)
                    parts.append(
                        f'<text x="{x + bar / 2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-size="{fs * 0.85}" {font}>{fmt_v}</text>'
                    )

    for i, lbl in enumerate(labels):
        txt = escape_html(lbl[:17] + '…' if len(lbl) > 18 else lbl)
        if horizontal:
            parts.append(
                f'<text x="{plot_x - 6:.2f}" y="{plot_y + slot * (i + 0.5) + fs / 3:.2f}" text-anchor="end" font-size="{fs * 0.85}" {font}>{txt}</text>'
            )
        else:
            parts.append(
                f'<text x="{plot_x + slot * (i + 0.5):.2f}" y="{plot_y + plot_h + fs * 1.2:.2f}" text-anchor="middle" font-size="{fs * 0.85}" {font}>{txt}</text>'
            )

    axis_line = (
        f'<line x1="{plot_x:.2f}" y1="{plot_y:.2f}" x2="{plot_x:.2f}" y2="{plot_y + plot_h:.2f}" stroke="#94a3b8" stroke-width="2"/>'
        if horizontal
        else f'<line x1="{plot_x:.2f}" y1="{plot_y + plot_h - scale(0):.2f}" x2="{plot_x + plot_w:.2f}" y2="{plot_y + plot_h - scale(0):.2f}" stroke="#94a3b8" stroke-width="2"/>'
    )
    parts.append(axis_line)

    return _wrap(w, h, parts)


def _legend(parts: List[str], labels: List[str], x: float, y: float, fs: float, font: str, color_fn) -> None:
    for i, lbl in enumerate(labels):
        yy = y + i * fs * 1.5
        parts.append(
            f'<rect x="{x:.2f}" y="{yy:.2f}" width="{fs * 0.9:.2f}" height="{fs * 0.9:.2f}" fill="{color_fn(i)}" rx="2"/>'
        )
        parts.append(
            f'<text x="{x + fs * 1.3:.2f}" y="{yy + fs * 0.8:.2f}" font-size="{fs * 0.85}" {font}>{escape_html(lbl)}</text>'
        )


def _wrap(w: float, h: float, parts: List[str]) -> str:
    return (
        f'<svg viewBox="0 0 {w:.2f} {h:.2f}" preserveAspectRatio="none" '
        f'style="display:block;width:100%;height:100%" xmlns="http://www.w3.org/2000/svg">'
        f'{"".join(parts)}</svg>'
    )
