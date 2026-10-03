"""Document and Band models for eazyreport."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .types import LayoutElement, PageMargins, Watermark


@dataclass
class Band:
    id: str = ''
    type: str = 'band'
    name: str = ''
    height: float = 20.0
    canGrow: bool = False
    canShrink: bool = False
    visibleExpr: str = ''
    fill: str = ''
    startNewPage: bool = False
    printOnFirstPage: bool = True
    printOnLastPage: bool = True
    repeatOnEveryPage: bool = False
    elements: List[LayoutElement] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional['Band']:
        if not d or not isinstance(d, dict):
            return None
        raw_elements = d.get('elements', [])
        elements = [LayoutElement.from_dict(el) for el in raw_elements if isinstance(el, dict)]
        return cls(
            id=str(d.get('id', '')),
            type=str(d.get('type', 'band')),
            name=str(d.get('name', '')),
            height=float(d.get('height', 20.0)),
            canGrow=bool(d.get('canGrow', False)),
            canShrink=bool(d.get('canShrink', False)),
            visibleExpr=str(d.get('visibleExpr', '')),
            fill=str(d.get('fill', '')),
            startNewPage=bool(d.get('startNewPage', False)),
            printOnFirstPage=bool(d.get('printOnFirstPage', True)),
            printOnLastPage=bool(d.get('printOnLastPage', True)),
            repeatOnEveryPage=bool(d.get('repeatOnEveryPage', False)),
            elements=elements,
        )


@dataclass
class GroupBand(Band):
    expression: str = ''
    resetPageNumber: bool = False
    keepTogether: bool = False

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional['GroupBand']:
        if not d or not isinstance(d, dict):
            return None
        b = Band.from_dict(d)
        if not b:
            return None
        return cls(
            id=b.id,
            type=b.type,
            name=b.name,
            height=b.height,
            canGrow=b.canGrow,
            canShrink=b.canShrink,
            visibleExpr=b.visibleExpr,
            fill=b.fill,
            startNewPage=b.startNewPage,
            printOnFirstPage=b.printOnFirstPage,
            printOnLastPage=b.printOnLastPage,
            repeatOnEveryPage=b.repeatOnEveryPage,
            elements=b.elements,
            expression=str(d.get('expression', '')),
            resetPageNumber=bool(d.get('resetPageNumber', False)),
            keepTogether=bool(d.get('keepTogether', False)),
        )


@dataclass
class ChildBand(Band):
    keepWithParent: bool = False
    fillUnusedSpace: bool = False

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional['ChildBand']:
        if not d or not isinstance(d, dict):
            return None
        b = Band.from_dict(d)
        if not b:
            return None
        return cls(
            id=b.id,
            type=b.type,
            name=b.name,
            height=b.height,
            canGrow=b.canGrow,
            canShrink=b.canShrink,
            visibleExpr=b.visibleExpr,
            fill=b.fill,
            startNewPage=b.startNewPage,
            printOnFirstPage=b.printOnFirstPage,
            printOnLastPage=b.printOnLastPage,
            repeatOnEveryPage=b.repeatOnEveryPage,
            elements=b.elements,
            keepWithParent=bool(d.get('keepWithParent', False)),
            fillUnusedSpace=bool(d.get('fillUnusedSpace', False)),
        )


@dataclass
class DataBand(Band):
    dataset: str = ''
    dataPath: str = ''
    alias: str = 'item'
    filterExpr: str = ''
    sortField: str = ''
    sortDir: str = 'asc'
    keepWithNext: bool = False
    keepTogether: bool = False
    fillUnusedSpace: bool = False
    columnCount: int = 1
    columnSpacing: float = 0.0
    columnWidth: float = 0.0
    header: Optional[Band] = None
    footer: Optional[Band] = None
    groupHeaders: List[GroupBand] = field(default_factory=list)
    groupFooters: List[GroupBand] = field(default_factory=list)
    childBands: List[ChildBand] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional['DataBand']:
        if not d or not isinstance(d, dict):
            return None
        b = Band.from_dict(d)
        if not b:
            return None

        gh = [
            GroupBand.from_dict(g)
            for g in d.get('groupHeaders', [])
            if isinstance(g, dict) and GroupBand.from_dict(g)
        ]
        gf = [
            GroupBand.from_dict(g)
            for g in d.get('groupFooters', [])
            if isinstance(g, dict) and GroupBand.from_dict(g)
        ]
        cb = [
            ChildBand.from_dict(c)
            for c in d.get('childBands', d.get('children', []))
            if isinstance(c, dict) and ChildBand.from_dict(c)
        ]

        dp = str(d.get('dataPath', d.get('arrayPath', d.get('dataset', ''))))

        return cls(
            id=b.id,
            type=b.type or 'data',
            name=b.name,
            height=b.height,
            canGrow=b.canGrow,
            canShrink=b.canShrink,
            visibleExpr=b.visibleExpr,
            fill=b.fill,
            startNewPage=b.startNewPage,
            printOnFirstPage=b.printOnFirstPage,
            printOnLastPage=b.printOnLastPage,
            repeatOnEveryPage=b.repeatOnEveryPage,
            elements=b.elements,
            dataset=dp,
            dataPath=dp,
            alias=str(d.get('alias', 'item')),
            filterExpr=str(d.get('filterExpr', '')),
            sortField=str(d.get('sortField', '')),
            sortDir=str(d.get('sortDir', 'asc')),
            keepWithNext=bool(d.get('keepWithNext', False)),
            keepTogether=bool(d.get('keepTogether', False)),
            fillUnusedSpace=bool(d.get('fillUnusedSpace', False)),
            columnCount=int(d.get('columnCount', 1)),
            columnSpacing=float(d.get('columnSpacing', 0.0)),
            columnWidth=float(d.get('columnWidth', 0.0)),
            header=Band.from_dict(d.get('header')),
            footer=Band.from_dict(d.get('footer')),
            groupHeaders=gh,
            groupFooters=gf,
            childBands=cb,
        )


@dataclass
class LayoutPage:
    id: str = ''
    name: str = 'Page1'
    size: str = 'A4'
    orientation: str = 'portrait'
    width: float = 210.0
    height: float = 297.0
    margins: PageMargins = field(default_factory=PageMargins)
    printOffsetX: float = 0.0
    printOffsetY: float = 0.0
    watermark: Watermark = field(default_factory=Watermark)

    reportTitle: Optional[Band] = None
    reportSummary: Optional[Band] = None
    pageHeader: Optional[Band] = None
    pageFooter: Optional[Band] = None
    columnHeader: Optional[Band] = None
    columnFooter: Optional[Band] = None
    header: Optional[Band] = None
    footer: Optional[Band] = None
    overlay: Optional[Band] = None
    data: List[DataBand] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'LayoutPage':
        size = str(d.get('size', 'A4'))
        orientation = str(d.get('orientation', 'portrait'))
        w = float(d.get('width', 210.0 if orientation == 'portrait' else 297.0))
        h = float(d.get('height', 297.0 if orientation == 'portrait' else 210.0))

        raw_data = d.get('dataBands', d.get('data', []))
        data_bands: List[DataBand] = []
        if isinstance(raw_data, list):
            for item in raw_data:
                db = DataBand.from_dict(item)
                if db:
                    data_bands.append(db)
        elif isinstance(raw_data, dict):
            db = DataBand.from_dict(raw_data)
            if db:
                data_bands.append(db)

        return cls(
            id=str(d.get('id', '')),
            name=str(d.get('name', 'Page1')),
            size=size,
            orientation=orientation,
            width=w,
            height=h,
            margins=PageMargins.from_dict(d.get('margins')),
            printOffsetX=float(d.get('printOffsetX', 0.0)),
            printOffsetY=float(d.get('printOffsetY', 0.0)),
            watermark=Watermark.from_dict(d.get('watermark')),
            reportTitle=Band.from_dict(d.get('reportTitle')),
            reportSummary=Band.from_dict(d.get('reportSummary')),
            pageHeader=Band.from_dict(d.get('pageHeader')),
            pageFooter=Band.from_dict(d.get('pageFooter')),
            columnHeader=Band.from_dict(d.get('columnHeader')),
            columnFooter=Band.from_dict(d.get('columnFooter')),
            header=Band.from_dict(d.get('header')),
            footer=Band.from_dict(d.get('footer')),
            overlay=Band.from_dict(d.get('overlay')),
            data=data_bands,
        )


@dataclass
class LayoutDocument:
    format: str = 'report-designer-layout'
    version: int = 2
    title: str = ''
    author: str = ''
    description: str = ''
    pages: List[LayoutPage] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'LayoutDocument':
        raw_pages = d.get('pages', [])
        pages = [LayoutPage.from_dict(p) for p in raw_pages if isinstance(p, dict)]
        if not pages:
            pages = [LayoutPage()]

        return cls(
            format=str(d.get('format', 'report-designer-layout')),
            version=int(d.get('version', 2)),
            title=str(d.get('title', '')),
            author=str(d.get('author', '')),
            description=str(d.get('description', '')),
            pages=pages,
        )
