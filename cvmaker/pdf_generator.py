"""PDF generator - creates PDF documents from parsed CV data."""

import json
import re
from pathlib import Path

from weasyprint import HTML, CSS

from .parser import CV, Section, SubSection, Paragraph, ListItem, TextRun


def load_template(template_path: str | None = None) -> dict:
    """Load styling template."""
    if template_path is None:
        template_path = Path(__file__).parent / "templates" / "default.json"

    with open(template_path, "r") as f:
        return json.load(f)


def runs_to_html(runs: list[TextRun]) -> str:
    """Convert text runs to HTML with formatting."""
    html_parts = []
    for run in runs:
        text = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if run.bold and run.italic:
            html_parts.append(f"<strong><em>{text}</em></strong>")
        elif run.bold:
            html_parts.append(f"<strong>{text}</strong>")
        elif run.italic:
            html_parts.append(f"<em>{text}</em>")
        else:
            html_parts.append(text)
    return "".join(html_parts)


def generate_html(cv: CV, template: dict) -> str:
    """Generate HTML from parsed CV data."""
    colors = template["colors"]
    fonts = template["fonts"]
    title_size = fonts.get(
        "title_size", fonts.get("heading2_size", fonts["heading1_size"])
    )
    margins = template["margins"]
    spacing = template["spacing"]

    css = f"""
    @page {{
        size: letter;
        margin: {margins['top']}in {margins['right']}in {margins['bottom']}in {margins['left']}in;
    }}
    body {{
        font-family: {fonts['name']}, Arial, sans-serif;
        font-size: {fonts['body_size']}pt;
        color: {colors['body']};
        line-height: {spacing['line_spacing']};
        margin: 0;
        padding: 0;
    }}
    .header {{
        border: {template.get('header', {}).get('border_width', 1)}px solid {template.get('header', {}).get('border_color', colors['accent'])};
        background: {template.get('header', {}).get('background', 'rgba(52, 152, 219, 0.08)')};
        padding: {template.get('header', {}).get('padding', spacing['section_after'])}px;
        margin-bottom: {template.get('header', {}).get('gap', spacing['section_after'] * 2)}px;
        text-align: center;
        border-radius: {template.get('header', {}).get('radius', 8)}px;
    }}
    h1 {{
        font-size: {fonts['heading1_size']}pt;
        color: {colors['heading']};
        margin: 0 0 {spacing['section_after'] // 3}px 0;
        font-weight: bold;
    }}
    .name-line {{
        display: flex;
        justify-content: center;
        align-items: baseline;
        flex-wrap: wrap;
        gap: 8px;
        margin: 0 0 {spacing['section_after'] // 3}px 0;
    }}
    .name-text {{
        font-size: {fonts['heading1_size']}pt;
        color: {colors['heading']};
        font-weight: 700;
    }}
    .name-title {{
        font-size: {title_size}pt;
        color: {colors['heading']};
        font-weight: 600;
    }}
    .name-separator {{
        color: {colors['body']};
        font-weight: 500;
    }}
    .contact {{
        margin-top: 2px;
        font-size: {fonts['body_size']}pt;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        justify-content: center;
    }}
    .contact-chunk {{
        display: inline-flex;
        white-space: nowrap;
        gap: 3px;
        align-items: baseline;
    }}
    .contact-url {{
        font-size: {fonts['body_size']}pt;
        color: {colors['accent']};
        font-weight: 700;
        text-decoration: none;
    }}
    h2 {{
        font-size: {fonts['heading2_size']}pt;
        color: {colors['heading']};
        margin: {spacing['section_before']}px 0 {spacing['section_after']}px 0;
        font-weight: bold;
        border-bottom: 2px solid {colors['accent']};
        padding-bottom: 2px;
    }}
    .entry {{
        margin: {spacing['section_after'] // 2}px 0 {spacing['section_after']}px 0;
    }}
    .entry-header,
    .para-line,
    .item-line {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
        margin-bottom: {spacing['section_after'] // 3}px;
    }}
    .entry-url,
    .para-url,
    .item-url {{
        font-size: {fonts['body_size']}pt;
        color: {colors['accent']};
        white-space: nowrap;
        flex: 0 0 auto;
        font-weight: 700;
        text-decoration: none;
    }}
    .entry-title {{
        font-size: {fonts['heading3_size']}pt;
        color: {colors['subheading']};
        font-weight: bold;
        flex: 1 1 auto;
    }}
    .entry-date,
    .para-date,
    .item-date {{
        font-size: {fonts['body_size']}pt;
        color: {colors['body']};
        white-space: nowrap;
        flex: 0 0 auto;
        font-style: italic;
    }}
    .cert-list {{
        list-style: none;
        padding-left: 0;
        margin: {spacing['section_after'] // 2}px 0 {spacing['section_after']}px 0;
        display: flex;
        flex-wrap: wrap;
        gap: 6px 10px;
    }}
    .cert-chip {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        border: 1px solid {colors['accent']};
        background: {colors['accent']}1a;
        color: {colors['heading']};
        font-weight: 600;
        white-space: nowrap;
    }}
    .cert-chip-date {{
        font-style: italic;
        color: {colors['body']};
        margin-left: 6px;
    }}
    .cert-chip-url {{
        color: {colors['accent']};
        font-weight: 700;
        margin-left: 6px;
        text-decoration: none;
        white-space: nowrap;
    }}
    .para-text,
    .item-text {{
        flex: 1 1 auto;
    }}
    p {{
        margin: {spacing['section_after'] // 3}px 0;
    }}
    ul {{
        margin: {spacing['section_after'] // 2}px 0;
        padding-left: 18px;
    }}
    li {{
        margin: 0;
        list-style-position: outside;
    }}
    """

    html_parts = [f"<html><head><style>{css}</style></head><body>"]

    # Header block
    if cv.name or cv.contact_line:
        html_parts.append('<div class="header">')
        if cv.name and cv.primary_title:
            html_parts.append(
                "<div class='name-line'>"
                f"<span class='name-text'>{cv.name}</span>"
                f"<span class='name-separator'>|</span>"
                f"<span class='name-title'>{cv.primary_title}</span>"
                "</div>"
            )
        elif cv.name:
            html_parts.append(f"<h1>{cv.name}</h1>")
        if cv.contact_line:
            contact_html = runs_to_html(cv.contact_line.runs)
            chunks = [c.strip() for c in contact_html.split("|") if c.strip()]

            url_pattern = re.compile(
                r"(https?://\S+|www\.\S+|[\w.-]+\.[\w.-]+/\S+|[\w.-]+\.[\w.-]+)"
            )

            highlighted: list[str] = []
            for c in chunks:
                chunk_html = c
                low = c.lower()
                if "linkedin" in low or "github" in low:
                    match = url_pattern.search(c)
                    if match:
                        url_text = match.group(0).rstrip(".,;")
                        chunk_html = c.replace(
                            url_text, f"<span class='contact-url'>{url_text}</span>", 1
                        )
                highlighted.append(f"<span class='contact-chunk'>{chunk_html}</span>")

            if getattr(cv.contact_line, "url", None):
                last_low = chunks[-1].lower() if chunks else ""
                last_has_url = bool(chunks and url_pattern.search(chunks[-1]))
                if highlighted:
                    if (
                        "linkedin" in last_low or "github" in last_low
                    ) and not last_has_url:
                        highlighted[-1] = highlighted[-1].replace(
                            "</span>",
                            f" <span class='contact-url'>{cv.contact_line.url}</span></span>",
                            1,
                        )
                else:
                    # Only apply accent if we know it's a github/linkedin URL
                    if (
                        "linkedin" in cv.contact_line.url.lower()
                        or "github" in cv.contact_line.url.lower()
                    ):
                        highlighted = [
                            f"<span class='contact-chunk contact-url'>{cv.contact_line.url}</span>"
                        ]
                    else:
                        highlighted = [
                            f"<span class='contact-chunk'>{cv.contact_line.url}</span>"
                        ]

            html_parts.append(f"<div class='contact'>{' '.join(highlighted)}</div>")
        html_parts.append("</div>")

    # Sections
    for section in cv.sections:
        html_parts.append(_section_to_html(section))

    html_parts.append("</body></html>")
    return "".join(html_parts)


def _section_to_html(section: Section) -> str:
    """Convert a section to HTML."""
    title_lower = section.title.strip().lower()
    html_parts = [f"<h2>{section.title}</h2>"]

    # Render Certifications section as chip-style list
    if "certification" in title_lower:
        chips: list[str] = []
        for item in section.content:
            if isinstance(item, ListItem):
                text_html = runs_to_html(item.runs)
                extras = []
                if item.date:
                    extras.append(f'<span class="cert-chip-date">{item.date}</span>')
                if item.url:
                    extras.append(f'<span class="cert-chip-url">{item.url}</span>')
                chip_body = text_html
                if extras:
                    chip_body = f"{chip_body} {' '.join(extras)}"
                chips.append(f'<li class="cert-chip">{chip_body}</li>')
            elif isinstance(item, Paragraph):
                html_parts.append(_paragraph_to_html(item))
            elif isinstance(item, SubSection):
                html_parts.append(_subsection_to_html(item))
        if chips:
            html_parts.append(f'<ul class="cert-list">{"".join(chips)}</ul>')
        return "".join(html_parts)

    # Default rendering
    for item in section.content:
        if isinstance(item, SubSection):
            html_parts.append(_subsection_to_html(item))
        elif isinstance(item, Paragraph):
            html_parts.append(_paragraph_to_html(item))
        elif isinstance(item, ListItem):
            html_parts.append(_listitem_to_html(item))

    return "".join(html_parts)


def _subsection_to_html(subsection: SubSection) -> str:
    """Convert a subsection to HTML."""
    html_parts = ['<div class="entry">']
    html_parts.append('<div class="entry-header">')
    html_parts.append(f'<div class="entry-title">{subsection.title}</div>')
    if subsection.date:
        html_parts.append(f'<div class="entry-date">{subsection.date}</div>')
    if getattr(subsection, "url", None):
        html_parts.append(f'<div class="entry-url">{subsection.url}</div>')
    html_parts.append("</div>")

    # Collect consecutive list items
    current_list = []

    for item in subsection.content:
        if isinstance(item, ListItem):
            if item.date or item.url:
                right_parts = []
                if item.date:
                    right_parts.append(f'<span class="item-date">{item.date}</span>')
                if item.url:
                    right_parts.append(f'<span class="item-url">{item.url}</span>')
                right_html = " ".join(right_parts)
                current_list.append(
                    f'<li class="item-line"><span class="item-text">{runs_to_html(item.runs)}</span>'
                    f"{right_html}</li>"
                )
            else:
                current_list.append(f"<li>{runs_to_html(item.runs)}</li>")
        else:
            # Flush any pending list
            if current_list:
                html_parts.append(f'<ul>{"".join(current_list)}</ul>')
                current_list = []

            if isinstance(item, Paragraph):
                html_parts.append(_paragraph_to_html(item))

    # Flush remaining list items
    if current_list:
        html_parts.append(f'<ul>{"".join(current_list)}</ul>')

    html_parts.append("</div>")
    return "".join(html_parts)


def _paragraph_to_html(para: Paragraph) -> str:
    """Convert a paragraph to HTML with optional right-aligned date."""
    if para.date or para.url:
        right_parts = []
        if para.date:
            right_parts.append(f'<span class="para-date">{para.date}</span>')
        if para.url:
            right_parts.append(f'<span class="para-url">{para.url}</span>')
        right_html = " ".join(right_parts)
        return (
            '<p class="para-line">'
            f'<span class="para-text">{runs_to_html(para.runs)}</span>'
            f"{right_html}"
            "</p>"
        )
    return f"<p>{runs_to_html(para.runs)}</p>"


def _listitem_to_html(item: ListItem) -> str:
    """Convert a list item to HTML with optional right-aligned date."""
    if item.date or item.url:
        right_parts = []
        if item.date:
            right_parts.append(f'<span class="item-date">{item.date}</span>')
        if item.url:
            right_parts.append(f'<span class="item-url">{item.url}</span>')
        right_html = " ".join(right_parts)
        return (
            '<ul><li class="item-line">'
            f'<span class="item-text">{runs_to_html(item.runs)}</span>'
            f"{right_html}"
            "</li></ul>"
        )
    return f"<ul><li>{runs_to_html(item.runs)}</li></ul>"


def generate_pdf(cv: CV, output_path: str, template_path: str | None = None) -> str:
    """Generate a PDF file from parsed CV data."""
    template = load_template(template_path)
    html_content = generate_html(cv, template)

    html = HTML(string=html_content)
    html.write_pdf(output_path)

    return output_path
