"""Data models and structures for eazyreport templates and elements."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class HAlign(str, Enum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    JUSTIFY = 'justify'


class VAlign(str, Enum):
    TOP = 'top'
    MIDDLE = 'middle'
    BOTTOM = 'bottom'


class BorderStyle(str, Enum):
    SOLID = 'solid'
    DASHED = 'dashed'
    DOTTED = 'dotted'
    DOUBLE = 'double'
    NONE = 'none'


@dataclass
class PageMargins:
    top: float = 10.0
    right: float = 10.0
    bottom: float = 10.0
    left: float = 10.0

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'PageMargins':
        if not d:
            return cls()
        return cls(
            top=float(d.get('top', 10.0)),
            right=float(d.get('right', 10.0)),
            bottom=float(d.get('bottom', 10.0)),
            left=float(d.get('left', 10.0)),
        )

    def to_dict(self) -> Dict[str, float]:
        return {'top': self.top, 'right': self.right, 'bottom': self.bottom, 'left': self.left}


@dataclass
class Watermark:
    enabled: bool = False
    text: str = 'DRAFT'
    color: str = '#94a3b8'
    fontSize: float = 90.0
    angle: float = -45.0
    opacity: float = 0.18
    image: str = ''
    onTop: bool = False

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'Watermark':
        if not d:
            return cls()
        return cls(
            enabled=bool(d.get('enabled', False)),
            text=str(d.get('text', 'DRAFT')),
            color=str(d.get('color', '#94a3b8')),
            fontSize=float(d.get('fontSize', 90.0)),
            angle=float(d.get('angle', -45.0)),
            opacity=float(d.get('opacity', 0.18)),
            image=str(d.get('image', '')),
            onTop=bool(d.get('onTop', False)),
        )


@dataclass
class TextStyle:
    fontFamily: str = 'Inter'
    fontSize: float = 10.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color: str = '#0f172a'
    lineHeight: float = 1.3
    letterSpacing: float = 0.0
    align: str = 'left'
    vAlign: str = 'top'

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'TextStyle':
        if not d:
            return cls()
        return cls(
            fontFamily=str(d.get('fontFamily', 'Inter')),
            fontSize=float(d.get('fontSize', 10.0)),
            bold=bool(d.get('bold', False)),
            italic=bool(d.get('italic', False)),
            underline=bool(d.get('underline', False)),
            strike=bool(d.get('strike', False)),
            color=str(d.get('color', '#0f172a')),
            lineHeight=float(d.get('lineHeight', 1.3)),
            letterSpacing=float(d.get('letterSpacing', 0.0)),
            align=str(d.get('align', 'left')).lower(),
            vAlign=str(d.get('vAlign', 'top')).lower(),
        )


@dataclass
class BoxStyle:
    background: str = ''
    borderColor: str = '#e2e8f0'
    borderWidth: float = 0.0
    borderStyle: str = 'solid'
    borderRadius: float = 0.0
    borderTop: bool = False
    borderRight: bool = False
    borderBottom: bool = False
    borderLeft: bool = False
    paddingTop: float = 0.0
    paddingRight: float = 0.0
    paddingBottom: float = 0.0
    paddingLeft: float = 0.0

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'BoxStyle':
        if not d:
            return cls()
        # Handle padding as either dict/number or individual fields
        p = d.get('padding')
        pt = pr = pb = pl = 0.0
        if isinstance(p, (int, float)):
            pt = pr = pb = pl = float(p)
        elif isinstance(p, dict):
            pt = float(p.get('top', 0.0))
            pr = float(p.get('right', 0.0))
            pb = float(p.get('bottom', 0.0))
            pl = float(p.get('left', 0.0))

        return cls(
            background=str(d.get('background', '')),
            borderColor=str(d.get('borderColor', '#e2e8f0')),
            borderWidth=float(d.get('borderWidth', 0.0)),
            borderStyle=str(d.get('borderStyle', 'solid')).lower(),
            borderRadius=float(d.get('borderRadius', 0.0)),
            borderTop=bool(d.get('borderTop', False)),
            borderRight=bool(d.get('borderRight', False)),
            borderBottom=bool(d.get('borderBottom', False)),
            borderLeft=bool(d.get('borderLeft', False)),
            paddingTop=float(d.get('paddingTop', pt)),
            paddingRight=float(d.get('paddingRight', pr)),
            paddingBottom=float(d.get('paddingBottom', pb)),
            paddingLeft=float(d.get('paddingLeft', pl)),
        )


@dataclass
class ValueFormat:
    format: str = 'auto'
    decimals: int = 2
    thousands: bool = True
    currency: str = 'USD'
    datePattern: str = 'dd/MM/yyyy'

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'ValueFormat':
        if not d:
            return cls()
        return cls(
            format=str(d.get('format', 'auto')),
            decimals=int(d.get('decimals', 2)),
            thousands=bool(d.get('thousands', True)),
            currency=str(d.get('currency', 'USD')),
            datePattern=str(d.get('datePattern', 'dd/MM/yyyy')),
        )


@dataclass
class LogicRule:
    enabled: bool = True
    property: str = ''
    operator: str = 'equals'
    value: Optional[str] = None
    action: str = 'hide'
    actionValue: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> 'LogicRule':
        if not d:
            return cls()
        return cls(
            enabled=bool(d.get('enabled', True)),
            property=str(d.get('property', '')),
            operator=str(d.get('operator', 'equals')),
            value=str(d.get('value')) if d.get('value') is not None else None,
            action=str(d.get('action', 'hide')),
            actionValue=str(d.get('actionValue')) if d.get('actionValue') is not None else None,
        )


@dataclass
class LayoutElement:
    id: str = ''
    type: str = 'text'
    name: str = ''
    x: float = 0.0
    y: float = 0.0
    w: float = 50.0
    h: float = 10.0
    visibleExpr: str = ''
    locked: bool = False
    style: TextStyle = field(default_factory=TextStyle)
    box: BoxStyle = field(default_factory=BoxStyle)

    # Specific fields
    content: str = ''
    field_name: str = ''
    prefix: str = ''
    suffix: str = ''
    nullText: str = ''
    hideZeros: bool = False
    aggregate: str = 'none'
    dataType: str = 'string'
    autoHeight: bool = False
    minHeight: Optional[float] = None
    maxHeight: Optional[float] = None
    valueFormat: ValueFormat = field(default_factory=ValueFormat)
    rules: List[LogicRule] = field(default_factory=list)

    # Line specific
    orientation: str = 'horizontal'
    strokeWidth: float = 1.0
    strokeColor: str = '#cbd5e1'
    strokeDash: str = 'solid'

    # Image specific
    src: str = ''
    fit: str = 'contain'
    opacity: float = 1.0

    # Barcode specific
    symbology: str = 'code128'
    barcodeValue: str = ''
    showText: bool = True
    barColor: str = '#000000'
    barcodeBackground: str = '#ffffff'
    stretch: bool = True

    # Chart specific
    chartType: str = 'column'
    title: str = ''
    labelsField: str = ''
    valuesField: str = ''
    colors: List[str] = field(default_factory=lambda: [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316'
    ])
    showLegend: bool = True
    showValues: bool = True
    showGrid: bool = True

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'LayoutElement':
        el_type = str(d.get('type', 'text')).lower()
        # Normalise shape to box
        if el_type == 'shape':
            el_type = 'box'

        rules_raw = d.get('rules', [])
        rules = [LogicRule.from_dict(r) for r in rules_raw if isinstance(r, dict)]

        colors = d.get('colors')
        if not isinstance(colors, list) or not colors:
            colors = [
                '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#f97316'
            ]

        # Extract format whether it is nested in valueFormat or top-level
        fmt_dict = d.get('valueFormat')
        if not isinstance(fmt_dict, dict):
            fmt_dict = d

        return cls(
            id=str(d.get('id', '')),
            type=el_type,
            name=str(d.get('name', '')),
            x=float(d.get('x', 0.0)),
            y=float(d.get('y', 0.0)),
            w=float(d.get('w', d.get('width', 50.0))),
            h=float(d.get('h', d.get('height', 10.0))),
            visibleExpr=str(d.get('visibleExpr', '')),
            locked=bool(d.get('locked', False)),
            style=TextStyle.from_dict(d.get('style')),
            box=BoxStyle.from_dict(d.get('box')),
            content=str(d.get('content', '')),
            field_name=str(d.get('path', d.get('field', ''))),
            prefix=str(d.get('prefix', '')),
            suffix=str(d.get('suffix', '')),
            nullText=str(d.get('nullText', '')),
            hideZeros=bool(d.get('hideZeros', False)),
            aggregate=str(d.get('aggregate', 'none')),
            dataType=str(d.get('dataType', 'string')),
            autoHeight=bool(d.get('autoHeight', False)),
            minHeight=float(d['minHeight']) if d.get('minHeight') is not None else None,
            maxHeight=float(d['maxHeight']) if d.get('maxHeight') is not None else None,
            valueFormat=ValueFormat.from_dict(fmt_dict),
            rules=rules,
            orientation=str(d.get('orientation', 'horizontal')),
            strokeWidth=float(d.get('strokeWidth', 1.0)),
            strokeColor=str(d.get('strokeColor', '#cbd5e1')),
            strokeDash=str(d.get('strokeDash', 'solid')),
            src=str(d.get('src', '')),
            fit=str(d.get('fit', 'contain')),
            opacity=float(d.get('opacity', 1.0)),
            symbology=str(d.get('symbology', 'code128')),
            barcodeValue=str(d.get('value', d.get('content', ''))),
            showText=bool(d.get('showText', True)),
            barColor=str(d.get('barColor', '#000000')),
            barcodeBackground=str(d.get('background', '#ffffff')),
            stretch=bool(d.get('stretch', True)),
            chartType=str(d.get('chartType', 'column')),
            title=str(d.get('title', '')),
            labelsField=str(d.get('labelsField', '')),
            valuesField=str(d.get('valuesField', '')),
            colors=colors,
            showLegend=bool(d.get('showLegend', True)),
            showValues=bool(d.get('showValues', True)),
            showGrid=bool(d.get('showGrid', True)),
        )
