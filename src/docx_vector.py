"""Attach SVG masters to the raster images already inside a .docx.

Word 2016+ (and current WPS) render a picture from an ``asvg:svgBlip``
extension on the ``a:blip`` element and fall back to the raster in
``r:embed`` when they cannot. Neither python-docx nor pandoc writes both
halves for us: python-docx embeds the PNG only, and pandoc writes the SVG
half but needs ``rsvg-convert`` on PATH to produce the fallback, which this
machine does not have.

So the builds keep embedding the 300 dpi PNG -- which is what every reader,
old Word included, is guaranteed to see -- and this module walks the finished
file afterwards and adds the vector half beside it. A figure then scales and
prints as vector, with the raster as the fallback rather than the content.

    attach_svg(Path("Engineering.docx"), {png_path: svg_path, ...})

The embedded rasters are matched to the files on disk by content hash, not by
name: pandoc renames the media it embeds after the relationship id, so a name
match would find nothing. A document that does not carry a given figure simply
skips it.
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path
from lxml import etree

#: The extension list entry Word looks for, and the namespace it lives in.
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
IMAGE_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
)

DOCUMENT = "word/document.xml"
DOC_RELS = "word/_rels/document.xml.rels"
CONTENT_TYPES = "[Content_Types].xml"


#: Parsed and reserialised with lxml rather than ElementTree, which emits only
#: the namespace declarations it still sees in use. pandoc's document.xml
#: declares a dozen and names several of them in ``mc:Ignorable``; dropping
#: those declarations leaves the attribute pointing at prefixes that no longer
#: exist, and both LibreOffice and Word then refuse to open the file.


def _qn(uri: str, tag: str) -> str:
    return f"{{{uri}}}{tag}"


def attach_svg(docx_path: Path, pairs: dict[Path, Path]) -> list[str]:
    """Add an SVG master beside every embedded raster listed in `pairs`.

    `pairs` maps a PNG on disk to its SVG master. Returns the stems that were
    attached, so a caller can report, or fail, when a figure it expected to
    find was not in the document.
    """
    by_digest = {
        hashlib.sha256(png.read_bytes()).hexdigest(): svg
        for png, svg in pairs.items()
        if png.exists()
    }

    with zipfile.ZipFile(docx_path) as source:
        items = {name: source.read(name) for name in source.namelist()}

    rels = etree.fromstring(items[DOC_RELS])
    raster_by_rid = {}
    taken = set()
    for rel in rels:
        rid = rel.get("Id")
        taken.add(rid)
        if rel.get("Type") == IMAGE_REL:
            raster_by_rid[rid] = f"word/{rel.get('Target')}"

    # One new relationship and one new part per figure actually present.
    svg_rid_by_raster_rid: dict[str, str] = {}
    attached: list[str] = []
    for rid, member in raster_by_rid.items():
        payload = items.get(member)
        if payload is None:
            continue
        svg = by_digest.get(hashlib.sha256(payload).hexdigest())
        if svg is None:
            continue
        stem = svg.stem
        index = len(attached) + 1
        svg_rid = f"rIdSvg{index}"
        while svg_rid in taken:
            index += 1
            svg_rid = f"rIdSvg{index}"
        taken.add(svg_rid)
        target = f"media/{stem}.svg"
        etree.SubElement(
            rels,
            _qn(PR_NS, "Relationship"),
            {"Id": svg_rid, "Type": IMAGE_REL, "Target": target},
        )
        items[f"word/{target}"] = svg.read_bytes()
        svg_rid_by_raster_rid[rid] = svg_rid
        attached.append(stem)

    if not attached:
        return []

    document = etree.fromstring(items[DOCUMENT])
    for blip in document.iter(_qn(A_NS, "blip")):
        svg_rid = svg_rid_by_raster_rid.get(blip.get(_qn(R_NS, "embed")))
        if svg_rid is None:
            continue
        ext_lst = blip.find(_qn(A_NS, "extLst"))
        if ext_lst is None:
            ext_lst = etree.SubElement(blip, _qn(A_NS, "extLst"))
        if any(ext.get("uri") == SVG_EXT_URI for ext in ext_lst):
            continue
        ext = etree.SubElement(ext_lst, _qn(A_NS, "ext"), {"uri": SVG_EXT_URI})
        etree.SubElement(
            ext, _qn(SVG_NS, "svgBlip"), {_qn(R_NS, "embed"): svg_rid},
            nsmap={"asvg": SVG_NS},
        )

    types = etree.fromstring(items[CONTENT_TYPES])
    known = {
        default.get("Extension", "").lower()
        for default in types.findall(_qn(CT_NS, "Default"))
    }
    if "svg" not in known:
        # A Default goes before any Override, which is where lxml puts a new
        # child anyway only if nothing follows it; insert explicitly.
        types.insert(len(types.findall(_qn(CT_NS, "Default"))),
                     etree.Element(_qn(CT_NS, "Default"),
                                   {"Extension": "svg",
                                    "ContentType": "image/svg+xml"}))

    serialise = lambda tree: etree.tostring(
        tree, xml_declaration=True, encoding="UTF-8", standalone=True
    )
    items[DOC_RELS] = serialise(rels)
    items[DOCUMENT] = serialise(document)
    items[CONTENT_TYPES] = serialise(types)

    temporary = docx_path.with_suffix(".svg-attached.docx")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as out:
        for name, payload in items.items():
            out.writestr(name, payload)
    shutil.move(temporary, docx_path)
    return attached


def vector_pairs(figures: Path, vectors: Path | None = None) -> dict[Path, Path]:
    """Every PNG under `figures` (one level deep) that has an SVG master."""
    vectors = vectors or figures / "vector"
    pairs: dict[Path, Path] = {}
    for svg in sorted(vectors.glob("*.svg")):
        for png in (figures / f"{svg.stem}.png", figures / "video" / f"{svg.stem}.png"):
            if png.exists():
                pairs[png] = svg
    return pairs
