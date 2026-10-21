"""Build `CONTRIBUTION.docx` from `CONTRIBUTION.md`.

`CONTRIBUTION.md` is the single source for the Contribution page's modelling
section. It opens with an editors' note in Chinese that is internal only, so the
build starts at the `## Modeling Contribution` heading and drops everything
above it.

Equations go through pandoc, which turns `$…$` into native Word equation
objects rather than images -- same reason `build_wiki_docx.py` uses it.

The reference document's theme leaves the East Asian typeface empty, which
leaves Word to guess for the Chinese blocks. We patch it to the same pair
`build_script_docx.py` already uses for the Chinese scripts: 宋体 for the body,
with 黑体 available for headings.

Requires pandoc on PATH, or its location in $PANDOC. Without installing it:

    pip download pypandoc_binary --no-deps -d /tmp/pd \
      && python -c "import zipfile,glob; zipfile.ZipFile(glob.glob('/tmp/pd/*.whl')[0]).extractall('/tmp/pd/x')" \
      && chmod +x /tmp/pd/x/pypandoc/files/pandoc \
      && export PANDOC=/tmp/pd/x/pypandoc/files/pandoc

Run from the project root:

    PYTHONPATH=. .venv/bin/python build_contribution_docx.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "CONTRIBUTION.md"
OUTPUT = ROOT / "CONTRIBUTION.docx"
BUILD = ROOT / ".docx-build"
REFERENCE = BUILD / "reference.docx"

#: The heading the published text starts at; everything above it is internal.
START = "## Modeling Contribution"

#: Matches build_script_docx.py's HAN / HAN_BOLD.
HAN = "宋体"
HAN_BOLD = "黑体"

TITLE = "Contribution — Modeling"


def find_pandoc() -> str:
    candidate = os.environ.get("PANDOC") or shutil.which("pandoc")
    if not candidate:
        sys.exit(
            "pandoc not found. Install it, or point $PANDOC at the binary "
            "(see this file's docstring for the no-install route)."
        )
    return candidate


def published_markdown() -> str:
    """The source with the Chinese editors' note removed."""
    text = SOURCE.read_text(encoding="utf-8")
    index = text.find(START)
    if index < 0:
        sys.exit(f"{SOURCE.name}: heading {START!r} not found")
    body = text[index:]
    # The note's trailing rule would otherwise open the document; the title
    # comes from the metadata, so the heading it replaces is simply dropped.
    body = body.replace(START, "", 1).lstrip()
    # On the wiki the three items sit under `## Modeling Contribution`. In the
    # document that heading is the title, so each item moves up a level.
    body = re.sub(r"^### ", "## ", body, flags=re.M)
    return body


def patched_reference(destination: Path) -> Path:
    """`reference.docx` with the theme's empty East Asian typeface filled in."""
    if not REFERENCE.exists():
        sys.exit(f"missing {REFERENCE}")
    source = zipfile.ZipFile(REFERENCE)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "word/theme/theme1.xml":
                theme = data.decode("utf-8")
                # Major (headings) first, then minor (body): the file lists the
                # major font scheme before the minor one.
                theme, count = re.subn(
                    r'<a:ea typeface=""/>',
                    lambda m, box=[HAN_BOLD, HAN]: (
                        f'<a:ea typeface="{box.pop(0)}"/>' if box else m.group(0)
                    ),
                    theme,
                    count=2,
                )
                if count != 2:
                    sys.exit(
                        f"theme1.xml: expected 2 empty <a:ea> typefaces, found {count}"
                    )
                data = theme.encode("utf-8")
            out.writestr(item, data)
    return destination


def main() -> None:
    pandoc = find_pandoc()
    BUILD.mkdir(exist_ok=True)
    prepared = BUILD / "contribution_prepared.md"
    prepared.write_text(published_markdown(), encoding="utf-8")
    reference = patched_reference(BUILD / "contribution_reference.docx")

    subprocess.run(
        [
            pandoc,
            str(prepared),
            # east_asian_line_breaks: a soft wrap between two CJK
            # characters is not a space. Without it every wrapped Chinese line
            # gains a spurious space in Word.
            # -smart: curly quotes are ambiguous-width, so Word renders them in
            # the East Asian font -- full-width, with a visible gap, in the
            # middle of English sentences. The Chinese blocks carry their own
            # typographic quotes in the source, which are unaffected.
            "--from=markdown+east_asian_line_breaks-smart",
            "--to=docx",
            f"--reference-doc={reference}",
            "--standalone",
            f"--metadata=title:{TITLE}",
            f"--output={OUTPUT}",
        ],
        check=True,
        cwd=ROOT,
    )
    size = OUTPUT.stat().st_size
    print(f"{OUTPUT.relative_to(ROOT)}  {size:,} bytes")


if __name__ == "__main__":
    main()
