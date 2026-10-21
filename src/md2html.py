"""A focused Markdown-to-HTML converter for the wiki page.

Why not a library
-----------------
The wiki text puts LaTeX inside table cells and inside emphasis-heavy prose. A
general-purpose converter mangles that: it applies emphasis rules inside
``$...$``, escapes backslashes, and breaks on a ``|`` that belongs to a formula.
This converter handles exactly the subset ``WIKI_DRAFT.md`` uses and treats math
and code as opaque spans that are lifted out *before* anything else runs and put
back *after*, so nothing can rewrite their contents.

Supported: ATX headings (with slug ids), paragraphs, GFM pipe tables, blockquotes,
unordered and ordered lists, fenced code, horizontal rules, images, links,
``**bold**``, ``*em*``, inline code, ``$...$`` and ``$$...$$``.

Deliberately unsupported, because the source does not use them: nested lists,
setext headings, reference links, inline HTML, footnotes.
"""

from __future__ import annotations

import html
import re

#: Sentinel wrapping a lifted span. Chosen to be impossible in Markdown source.
_MARK = "\x00{}\x00"
_MARK_RE = re.compile(r"\x00(\d+)\x00")

_MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.S)
_MATH_INLINE = re.compile(r"(?<![\$\\])\$([^\$\n]+?)\$(?!\$)")
_CODE_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.S | re.M)
_CODE_INLINE = re.compile(r"`([^`\n]+)`")
#: A display equation's number, pulled out and laid out separately.
_TAG = re.compile(r"\\tag\*?\{([^}]*)\}\s*$")

_HEADING = re.compile(r"^(#{1,4})[ \t]+(.*?)[ \t]*#*$")
_HR = re.compile(r"^(?:-{3,}|\*{3,})$")
_TABLE_RULE = re.compile(r"^\|?[ \t]*:?-{1,}:?[ \t]*(\|[ \t]*:?-{1,}:?[ \t]*)*\|?$")
_ULI = re.compile(r"^[-*][ \t]+(.*)$")
_OLI = re.compile(r"^(\d+)\.[ \t]+(.*)$")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_EM = re.compile(r"(?<![\*\w])\*([^\*\n]+?)\*(?![\*\w])")


class _Vault:
    """Conversion state: lifted spans, plus the heading ids issued so far.

    Each span keeps two forms: the HTML to emit, and a plain-text form used for
    heading ids. Without the second one a heading's maths would vanish from its
    slug, so two headings differing only in a formula would collide.

    Ids are also de-duplicated here. The page repeats subheadings like "Model"
    and "Results" in every section by design, and duplicate ids are invalid HTML
    that silently breaks anchor links.
    """

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []
        self.issued: dict[str, int] = {}

    def unique_id(self, ident: str) -> str:
        count = self.issued.get(ident, 0) + 1
        self.issued[ident] = count
        return ident if count == 1 else f"{ident}-{count}"

    def stash(self, rendered: str, plain: str = "") -> str:
        self.items.append((rendered, plain))
        return _MARK.format(len(self.items) - 1)

    def restore(self, text: str) -> str:
        return _MARK_RE.sub(lambda m: self.items[int(m.group(1))][0], text)

    def plain_text(self, text: str) -> str:
        return _MARK_RE.sub(lambda m: self.items[int(m.group(1))][1], text)


def slug(text: str) -> str:
    """Heading id: lowercase, words and hyphens only."""
    plain = _MARK_RE.sub("", text)
    plain = re.sub(r"[`*$\\]|&[a-z]+;", "", plain)
    plain = re.sub(r"[^\w\s-]", "", plain, flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", plain.strip()).lower() or "section"


def _latex_words(latex: str) -> str:
    """The readable part of a formula, for use in a heading id."""
    plain = re.sub(r"\\[a-zA-Z]+|[{}^]", " ", latex)
    return re.sub(r"\s+", " ", plain).strip()


def _lift(text: str, vault: _Vault) -> str:
    """Replace math and code with sentinels, innermost constructs last."""

    def fence(match: re.Match[str]) -> str:
        body = html.escape(match.group(1).rstrip("\n"))
        return vault.stash(f"<pre><code>{body}</code></pre>")

    def math_block(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        # Pull \tag out of the formula and lay it out as a sibling. Left to
        # KaTeX, the number is absolutely positioned against .katex-html, whose
        # width is the column's -- so any formula wider than the column scrolls
        # straight under its own number. As a flex sibling it cannot overlap.
        tag = ""
        tagged = _TAG.search(body)
        if tagged:
            body = _TAG.sub("", body).strip()
            tag = f'<span class="eq-tag">({html.escape(tagged.group(1))})</span>'
        body = html.escape(body, quote=False)
        return vault.stash(f'<div class="eq"><div class="eq-math">$${body}$$</div>{tag}</div>')

    def math_inline(match: re.Match[str]) -> str:
        body = html.escape(match.group(1), quote=False)
        return vault.stash(f"${body}$", _latex_words(match.group(1)))

    def code_inline(match: re.Match[str]) -> str:
        return vault.stash(f"<code>{html.escape(match.group(1))}</code>", match.group(1))

    text = _CODE_FENCE.sub(fence, text)
    text = _MATH_BLOCK.sub(math_block, text)
    text = _MATH_INLINE.sub(math_inline, text)
    text = _CODE_INLINE.sub(code_inline, text)
    return text


def _inline(text: str) -> str:
    """Escape, then apply the inline constructs. Math and code are already out."""
    text = html.escape(text, quote=False)
    text = _IMAGE.sub(lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}">', text)
    text = _LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    text = _BOLD.sub(lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = _EM.sub(lambda m: f"<em>{m.group(1)}</em>", text)
    return text


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _table(lines: list[str]) -> str:
    header = _cells(lines[0])
    rows = [_cells(line) for line in lines[2:]]
    # `tablewrap` is the template's class; cells are nowrap, so without its
    # overflow-x a wide table runs off the page instead of scrolling.
    out = ['<div class="tablewrap">', "<table>", "<thead><tr>"]
    out += [f"<th>{_inline(cell)}</th>" for cell in header]
    out += ["</tr></thead>", "<tbody>"]
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out += ["</tbody>", "</table>", "</div>"]
    return "\n".join(out)


def _starts_block(lines: list[str], i: int) -> bool:
    """True when line ``i`` opens a construct that must not be absorbed lazily."""
    line = lines[i]
    return bool(
        _HEADING.match(line)
        or _HR.match(line.strip())
        or _ULI.match(line)
        or _OLI.match(line)
        or _MARK_RE.fullmatch(line.strip())
        or ("|" in line and i + 1 < len(lines) and _TABLE_RULE.match(lines[i + 1].strip()))
    )


def _blocks(
    lines: list[str],
    headings: list[tuple[int, str, str]] | None,
    vault: _Vault,
) -> str:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # a lifted block (fence or display math) standing alone
        if _MARK_RE.fullmatch(line.strip()):
            out.append(line.strip())
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            body = _inline(heading.group(2))
            ident = vault.unique_id(slug(vault.plain_text(heading.group(2))))
            if headings is not None and level in (1, 2, 3):
                headings.append((level, ident, body))
            out.append(f'<h{level} id="{ident}">{body}</h{level}>')
            i += 1
            continue

        if _HR.match(line.strip()):
            out.append("<hr>")
            i += 1
            continue

        # An image alone on its line becomes a <figure>; the paragraph
        # immediately after it, if there is one, becomes its <figcaption>.
        # The whole paragraph, not one line: a legend that explains everything
        # in its figure runs to several wrapped lines, and taking only the
        # first silently truncated it mid-sentence.
        if _IMAGE.fullmatch(line.strip()):
            match = _IMAGE.fullmatch(line.strip())
            assert match is not None
            img = f'<img src="{match.group(2)}" alt="{match.group(1)}">'
            i += 1
            caption = ""
            start = i
            while i < len(lines) and lines[i].strip() and not _starts_block(lines, i):
                i += 1
            if i > start:
                text = " ".join(l.strip() for l in lines[start:i])
                caption = f"<figcaption>{_inline(text)}</figcaption>"
            out.append(f"<figure>{img}{caption}</figure>")
            continue

        if "|" in line and i + 1 < len(lines) and _TABLE_RULE.match(lines[i + 1].strip()):
            start = i
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                i += 1
            out.append(_table(lines[start:i]))
            continue

        if line.lstrip().startswith(">"):
            inner: list[str] = []
            while i < len(lines) and (lines[i].lstrip().startswith(">") or
                                      (inner and lines[i].strip()
                                       and not _starts_block(lines, i))):
                stripped = lines[i].lstrip()
                inner.append(stripped[1:].lstrip() if stripped.startswith(">") else stripped)
                i += 1
            out.append("<blockquote>" + _blocks(inner, None, vault) + "</blockquote>")
            continue

        if _ULI.match(line) or _OLI.match(line):
            ordered = bool(_OLI.match(line))
            items: list[str] = []
            while i < len(lines):
                match = _OLI.match(lines[i]) if ordered else _ULI.match(lines[i])
                if match:
                    items.append(match.group(2) if ordered else match.group(1))
                    i += 1
                elif lines[i].startswith(("  ", "\t")) and lines[i].strip() and items:
                    items[-1] += " " + lines[i].strip()
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            body = "".join(f"<li>{_inline(item)}</li>" for item in items)
            out.append(f"<{tag}>{body}</{tag}>")
            continue

        para: list[str] = []
        while i < len(lines) and lines[i].strip():
            if _starts_block(lines, i) or lines[i].lstrip().startswith(">"):
                break
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
    return "\n".join(out)


def contents(headings: list[tuple[int, str, str]]) -> str:
    """A two-level table of contents from the h1/h2 headings."""
    out = ['<nav class="contents">', "<h4>Contents</h4>", "<ol>"]
    for level, ident, body in headings:
        if level > 2:
            continue
        css = "" if level == 1 else ' class="sub"'
        out.append(f'<li{css}><a href="#{ident}">{body}</a></li>')
    out += ["</ol>", "</nav>"]
    return "\n".join(out)


def convert(markdown: str) -> tuple[str, str]:
    """Render Markdown, returning ``(body_html, contents_html)``."""
    vault = _Vault()
    lifted = _lift(markdown, vault)
    headings: list[tuple[int, str, str]] = []
    body = _blocks(lifted.split("\n"), headings, vault)
    return vault.restore(body), vault.restore(contents(headings))
