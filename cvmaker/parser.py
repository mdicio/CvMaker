"""Markdown CV parser — converts markdown to structured CV data.

Format conventions
------------------
- ``# Name``                → CV holder's name
- First line after name     → subtitle (if no ``|``) or contact info (if ``|``)
- Second line after name    → contact info
- ``## Section``            → major section heading
- ``### Title | Org | Date``→ subsection; last pipe-part is date if it looks datelike
- ``- bullet text | Date``  → list item with optional trailing date
- ``[text](url)``           → standard markdown link (rendered as hyperlink)
- ``<!-- chips -->``         → display hint placed after ``##`` to render items as tags
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ─────────────────────────────────────────────────────────


@dataclass
class TextRun:
    """A run of text with optional formatting and link."""

    text: str
    bold: bool = False
    italic: bool = False
    url: Optional[str] = None


@dataclass
class ListItem:
    """A bullet point item."""

    runs: list[TextRun] = field(default_factory=list)
    date: Optional[str] = None


@dataclass
class Paragraph:
    """A paragraph of text."""

    runs: list[TextRun] = field(default_factory=list)
    date: Optional[str] = None


@dataclass
class SubSection:
    """A subsection within a section (H3)."""

    title: str
    date: Optional[str] = None
    url: Optional[str] = None
    content: list[Paragraph | ListItem] = field(default_factory=list)


@dataclass
class Section:
    """A main section of the CV (H2).

    *display* controls rendering style:
    - ``"default"`` – standard list / paragraph rendering
    - ``"chips"``   – horizontal tag / badge rendering
    """

    title: str
    display: str = "default"
    content: list[Paragraph | ListItem | SubSection] = field(default_factory=list)


@dataclass
class CV:
    """Parsed CV structure."""

    name: str = ""
    subtitle: str = ""
    contact: Optional[Paragraph] = None
    sections: list[Section] = field(default_factory=list)


# ── Date detection ──────────────────────────────────────────────────────────

_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\.?"
_YEAR = r"\d{4}"
_MY = rf"(?:{_MONTH}\s+)?{_YEAR}"
_MMYY = r"\d{1,2}/\d{4}"
_END = rf"(?:present|current|{_MY}|{_MMYY})"
_DATE_RE = re.compile(
    rf"^\s*(?:{_MY}(?:\s*[-–—]\s*{_END})?|{_MMYY}(?:\s*[-–—]\s*{_END})?)\s*$",
    re.IGNORECASE,
)


def _is_date(text: str) -> bool:
    """Return True when *text* looks like a date or date range."""
    return bool(_DATE_RE.match(text))


def _split_date(text: str) -> tuple[str, Optional[str]]:
    """Split a trailing date off pipe-separated text.

    Only the *last* pipe-separated segment is considered; it is extracted as a
    date only when it matches a recognised date pattern.  The remaining parts
    are re-joined with ``|``.
    """
    parts = [p.strip() for p in text.split("|")]
    if len(parts) >= 2 and _is_date(parts[-1]):
        return " | ".join(parts[:-1]), parts[-1]
    return text, None


# ── Inline formatting ──────────────────────────────────────────────────────

_INLINE_RE = re.compile(
    r"\[([^\]]+)\]\(([^)]+)\)"  # [text](url)
    r"|\*\*\*(.+?)\*\*\*"  # ***bold italic***
    r"|\*\*(.+?)\*\*"  # **bold**
    r"|\*(.+?)\*"  # *italic*
    r"|([^[*]+)"  # plain text
)


def parse_inline(text: str) -> list[TextRun]:
    """Parse inline markdown: ``**bold**``, ``*italic*``, ``[link](url)``."""
    runs: list[TextRun] = []
    for m in _INLINE_RE.finditer(text):
        if m.group(1) is not None:  # link
            runs.append(TextRun(text=m.group(1), url=m.group(2)))
        elif m.group(3):  # bold-italic
            runs.append(TextRun(text=m.group(3), bold=True, italic=True))
        elif m.group(4):  # bold
            runs.append(TextRun(text=m.group(4), bold=True))
        elif m.group(5):  # italic
            runs.append(TextRun(text=m.group(5), italic=True))
        elif m.group(6):  # plain
            runs.append(TextRun(text=m.group(6)))
    return [r for r in runs if r.text] or [TextRun(text=text)]


# ── Header processing ──────────────────────────────────────────────────────


def _process_header(cv: CV, lines: list[str]) -> None:
    """Populate *cv.subtitle* and *cv.contact* from lines between H1 and H2.

    Rules (simple, position-based):
    - If there is exactly one line and it contains ``|`` → contact info.
    - If there is exactly one line without ``|`` → subtitle.
    - If there are two or more lines → first is subtitle, second is contact.
    """
    if not lines:
        return
    if len(lines) == 1:
        if "|" in lines[0]:
            cv.contact = Paragraph(runs=parse_inline(lines[0]))
        else:
            cv.subtitle = lines[0]
    else:
        cv.subtitle = lines[0]
        cv.contact = Paragraph(runs=parse_inline(lines[1]))


# ── Main parser ─────────────────────────────────────────────────────────────


def parse_markdown(text: str) -> CV:
    """Parse markdown text into a structured :class:`CV`."""
    cv = CV()
    lines = text.strip().split("\n")

    current_section: Optional[Section] = None
    current_subsection: Optional[SubSection] = None
    header_lines: list[str] = []
    header_done = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        # HTML comment → display hint  (e.g. <!-- chips -->)
        hint = re.match(r"^<!--\s*(\w+)\s*-->$", stripped)
        if hint and current_section:
            current_section.display = hint.group(1)
            continue

        # H1 — name
        if stripped.startswith("# ") and not stripped.startswith("## "):
            cv.name = stripped[2:].strip()
            continue

        # H2 — section
        if stripped.startswith("## ") and not stripped.startswith("### "):
            if not header_done:
                _process_header(cv, header_lines)
                header_done = True
            if current_subsection and current_section:
                current_section.content.append(current_subsection)
                current_subsection = None
            if current_section:
                cv.sections.append(current_section)
            current_section = Section(title=stripped[3:].strip())
            continue

        # H3 — subsection
        if stripped.startswith("### "):
            if current_subsection and current_section:
                current_section.content.append(current_subsection)
            raw_title = stripped[4:].strip()
            # Extract a leading markdown link from the title
            url = None
            link_m = re.match(r"\[([^\]]+)\]\(([^)]+)\)(.*)", raw_title)
            if link_m:
                raw_title = link_m.group(1) + link_m.group(3)
                url = link_m.group(2)
            title, date = _split_date(raw_title)
            current_subsection = SubSection(title=title, date=date, url=url)
            continue

        # Lines before the first H2 belong to the header
        if not header_done and cv.name:
            header_lines.append(stripped)
            continue

        # List item
        if stripped.startswith("- ") or stripped.startswith("* "):
            body, date = _split_date(stripped[2:])
            item = ListItem(runs=parse_inline(body), date=date)
            if current_subsection:
                current_subsection.content.append(item)
            elif current_section:
                current_section.content.append(item)
            continue

        # Paragraph
        body, date = _split_date(stripped)
        para = Paragraph(runs=parse_inline(body), date=date)
        if current_subsection:
            current_subsection.content.append(para)
        elif current_section:
            current_section.content.append(para)

    # Flush remaining structures
    if not header_done:
        _process_header(cv, header_lines)
    if current_subsection and current_section:
        current_section.content.append(current_subsection)
    if current_section:
        cv.sections.append(current_section)

    return cv


def parse_file(filepath: str) -> CV:
    """Parse a markdown file into a :class:`CV` structure."""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_markdown(f.read())
