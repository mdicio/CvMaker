"""Markdown CV parser - converts markdown to structured CV data."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TextRun:
    """A run of text with formatting."""

    text: str
    bold: bool = False
    italic: bool = False


@dataclass
class ListItem:
    """A bullet point item."""

    runs: list[TextRun] = field(default_factory=list)
    date: Optional[str] = None
    url: Optional[str] = None


@dataclass
class Paragraph:
    """A paragraph of text."""

    runs: list[TextRun] = field(default_factory=list)
    date: Optional[str] = None
    url: Optional[str] = None


@dataclass
class SubSection:
    """A subsection within a section (H3)."""

    title: str
    date: Optional[str] = None
    url: Optional[str] = None
    content: list[Paragraph | ListItem] = field(default_factory=list)


@dataclass
class Section:
    """A main section of the CV (H2)."""

    title: str
    content: list[Paragraph | ListItem | SubSection] = field(default_factory=list)


@dataclass
class CV:
    """Parsed CV structure."""

    name: str = ""
    primary_title: str = ""
    contact_line: Optional[Paragraph] = None
    sections: list[Section] = field(default_factory=list)


def parse_inline_formatting(text: str) -> list[TextRun]:
    """Parse inline markdown formatting (bold, italic) into TextRuns."""
    runs = []

    # Pattern to match **bold**, *italic*, ***bold italic***
    pattern = r"(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|([^*]+))"

    for match in re.finditer(pattern, text):
        if match.group(2):  # ***bold italic***
            runs.append(TextRun(text=match.group(2), bold=True, italic=True))
        elif match.group(3):  # **bold**
            runs.append(TextRun(text=match.group(3), bold=True))
        elif match.group(4):  # *italic*
            runs.append(TextRun(text=match.group(4), italic=True))
        elif match.group(5):  # plain text
            if match.group(5):
                runs.append(TextRun(text=match.group(5)))

    # Filter out empty runs
    runs = [r for r in runs if r.text]

    return runs if runs else [TextRun(text=text)]


def _looks_like_date(text: str) -> bool:
    """Heuristically detect if a string is a date or date range."""
    return bool(
        re.search(r"(\d{4}|\d{1,2}/\d{4}|present|Present|current|Current)", text)
    )


def _split_title_and_date(text: str) -> tuple[str, Optional[str]]:
    """Split a subsection heading into title and date when possible."""
    parts = [p.strip() for p in text.split("|") if p.strip()]

    if len(parts) >= 2 and _looks_like_date(parts[-1]):
        title = " | ".join(parts[:-1])
        return title, parts[-1]

    # Fallback for trailing date in parentheses/brackets
    paren_match = re.match(r"^(.*?)[\[(](.+?)[\])}]\s*$", text)
    if paren_match and _looks_like_date(paren_match.group(2)):
        return paren_match.group(1).strip(), paren_match.group(2).strip()

    return text, None


def _looks_like_url(text: str) -> bool:
    return bool(re.match(r"(https?://|www\.)", text)) or "." in text and "/" in text


def _extract_url(text: str) -> str:
    """Extract the most URL-looking token from a text segment."""
    # Strip markdown bold/italic markers
    cleaned = text.replace("**", "").replace("*", "")
    # Find URL-like tokens
    candidates = re.findall(
        r"(https?://\S+|www\.\S+|[\w.-]+\.[\w.-]+/\S+|[\w.-]+\.[\w.-]+)", cleaned
    )
    if candidates:
        return candidates[-1].rstrip(".,;")
    return cleaned.strip()


def _looks_like_contact(text: str) -> bool:
    """Heuristically detect if a line is contact info."""
    lowered = text.lower()
    if "|" in text:
        return True
    return any(
        key in lowered
        for key in (
            "email",
            "@",
            "linkedin",
            "github",
            "gitlab",
            "phone",
            "tel",
            "location",
        )
    )


def _split_body_meta(text: str) -> tuple[str, Optional[str], Optional[str]]:
    """Split body text and trailing date/url after pipes.

    Priority: last pipe part that looks like URL becomes url; remaining last part that
    looks like date becomes date. Body is the rest joined with pipes.
    """
    parts = [p.strip() for p in text.split("|") if p.strip()]

    url = None
    date = None

    if parts and _looks_like_url(parts[-1]):
        part = parts.pop()
        url = _extract_url(part)
        residual = part.replace(url, "").strip().strip("|,")
        if residual:
            parts.append(residual)

    if parts and _looks_like_date(parts[-1]):
        date = parts.pop()

    body = " | ".join(parts) if parts else text
    return body, date, url


def parse_markdown(markdown_text: str) -> CV:
    """Parse markdown CV text into structured CV data."""
    cv = CV()
    lines = markdown_text.strip().split("\n")

    current_section: Optional[Section] = None
    current_subsection: Optional[SubSection] = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # H1 - Name
        if stripped.startswith("# ") and not stripped.startswith("## "):
            cv.name = stripped[2:].strip()
            i += 1
            continue

        # H2 - Section
        if stripped.startswith("## ") and not stripped.startswith("### "):
            # Save current section
            if current_subsection and current_section:
                current_section.content.append(current_subsection)
                current_subsection = None
            if current_section:
                cv.sections.append(current_section)

            current_section = Section(title=stripped[3:].strip())
            i += 1
            continue

        # H3 - Subsection
        if stripped.startswith("### "):
            if current_subsection and current_section:
                current_section.content.append(current_subsection)
            title, date, url = _split_body_meta(stripped[4:].strip())
            current_subsection = SubSection(title=title, date=date, url=url)
            i += 1
            continue

        # List item
        if stripped.startswith("- ") or stripped.startswith("* "):
            item_text = stripped[2:]
            body_text, date, url = _split_body_meta(item_text)
            runs = parse_inline_formatting(body_text)
            list_item = ListItem(runs=runs, date=date, url=url)

            if current_subsection:
                current_subsection.content.append(list_item)
            elif current_section:
                current_section.content.append(list_item)
            i += 1
            continue

        # Regular paragraph
        para_text, date, url = _split_body_meta(stripped)
        runs = parse_inline_formatting(para_text)
        para = Paragraph(runs=runs, date=date, url=url)

        # If no section yet, the first non-contact line after the name is the primary title;
        # contact info follows.
        if not current_section and cv.name:
            if not cv.primary_title and not _looks_like_contact(para_text):
                cv.primary_title = para_text
                i += 1
                continue
            if not cv.contact_line and _looks_like_contact(para_text):
                cv.contact_line = para
                i += 1
                continue

        if current_subsection:
            current_subsection.content.append(para)
        elif current_section:
            current_section.content.append(para)

        i += 1

    # Save final section/subsection
    if current_subsection and current_section:
        current_section.content.append(current_subsection)
    if current_section:
        cv.sections.append(current_section)

    return cv


def parse_file(filepath: str) -> CV:
    """Parse a markdown file into CV structure."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_markdown(content)
