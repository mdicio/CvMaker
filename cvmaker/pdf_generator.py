"""PDF generator — creates styled PDF from parsed CV data using WeasyPrint."""

import json
from pathlib import Path

from weasyprint import HTML

from .parser import CV, Section, SubSection, Paragraph, ListItem, TextRun


def load_template(path: str | None = None) -> dict:
    """Load a JSON styling template."""
    if path is None:
        path = Path(__file__).parent / "templates" / "default.json"
    with open(path) as f:
        return json.load(f)


# ── HTML helpers ────────────────────────────────────────────────────────────


def _esc(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs_to_html(runs: list[TextRun]) -> str:
    """Convert a list of *TextRun* objects to an HTML fragment."""
    parts: list[str] = []
    for r in runs:
        t = _esc(r.text)
        if r.url:
            t = f'<a href="{_esc(r.url)}">{t}</a>'
        if r.bold and r.italic:
            t = f"<strong><em>{t}</em></strong>"
        elif r.bold:
            t = f"<strong>{t}</strong>"
        elif r.italic:
            t = f"<em>{t}</em>"
        parts.append(t)
    return "".join(parts)


# ── Full HTML document ──────────────────────────────────────────────────────


def generate_html(cv: CV, template: dict) -> str:
    """Build a complete HTML document from parsed *cv* and *template*."""
    c = template["colors"]
    f = template["fonts"]
    m = template["margins"]
    s = template["spacing"]
    h = template.get("header", {})
    title_sz = f.get("title_size", f["heading2_size"])

    css = f"""
    @page {{
        size: letter;
        margin: {m['top']}in {m['right']}in {m['bottom']}in {m['left']}in;
    }}
    body {{
        font-family: {f['name']}, Arial, sans-serif;
        font-size: {f['body_size']}pt;
        color: {c['body']};
        line-height: {s['line_spacing']};
        margin: 0; padding: 0;
    }}
    a {{ color: {c['accent']}; text-decoration: none; font-weight: 700; }}
    .header {{
        border: {h.get('border_width', 1)}px solid {h.get('border_color', c['accent'])};
        background: {h.get('background', 'rgba(52,152,219,0.08)')};
        padding: {h.get('padding', s['section_after'])}px;
        margin-bottom: {h.get('gap', s['section_after'] * 2)}px;
        text-align: center;
        border-radius: {h.get('radius', 8)}px;
    }}
    .name-line {{
        display: flex; justify-content: center; align-items: baseline;
        flex-wrap: wrap; gap: 8px;
        margin: 0 0 {s['section_after'] // 3}px 0;
    }}
    .name-text {{
        font-size: {f['heading1_size']}pt; color: {c['heading']}; font-weight: 700;
    }}
    .name-title {{
        font-size: {title_sz}pt; color: {c['heading']}; font-weight: 600;
    }}
    .name-sep {{ color: {c['body']}; font-weight: 500; }}
    h1 {{
        font-size: {f['heading1_size']}pt; color: {c['heading']};
        margin: 0 0 {s['section_after'] // 3}px 0; font-weight: bold;
    }}
    .contact {{
        margin-top: 2px; font-size: {f['body_size']}pt;
    }}
    h2 {{
        font-size: {f['heading2_size']}pt; color: {c['heading']};
        margin: {s['section_before']}px 0 {s['section_after']}px 0;
        font-weight: bold; border-bottom: 2px solid {c['accent']}; padding-bottom: 2px;
    }}
    .entry {{
        margin: {s['section_after'] // 2}px 0 {s['section_after']}px 0;
    }}
    .entry-header, .line-flex {{
        display: flex; justify-content: space-between; gap: 12px;
        align-items: baseline; margin-bottom: {s['section_after'] // 3}px;
    }}
    .entry-title {{
        font-size: {f['heading3_size']}pt; color: {c['subheading']};
        font-weight: bold; flex: 1 1 auto;
    }}
    .date {{
        font-size: {f['body_size']}pt; color: {c['body']};
        white-space: nowrap; font-style: italic;
    }}
    .chips {{
        list-style: none; padding: 0;
        margin: {s['section_after'] // 2}px 0;
        display: flex; flex-wrap: wrap; gap: 6px 10px;
    }}
    .chip {{
        display: inline-block; padding: 4px 10px; border-radius: 12px;
        border: 1px solid {c['accent']}; background: {c['accent']}1a;
        color: {c['heading']}; font-weight: 600; white-space: nowrap;
    }}
    .chip .date {{ margin-left: 6px; }}
    .flex-text {{ flex: 1 1 auto; }}
    p {{ margin: {s['section_after'] // 3}px 0; }}
    ul {{ margin: {s['section_after'] // 2}px 0; padding-left: 18px; }}
    li {{ margin: 0; list-style-position: outside; }}
    """

    out: list[str] = [f"<html><head><style>{css}</style></head><body>"]

    # ── Header ──────────────────────────────────────────────────────────
    if cv.name:
        out.append('<div class="header">')
        if cv.subtitle:
            out.append(
                '<div class="name-line">'
                f'<span class="name-text">{_esc(cv.name)}</span>'
                '<span class="name-sep">|</span>'
                f'<span class="name-title">{_esc(cv.subtitle)}</span>'
                "</div>"
            )
        else:
            out.append(f"<h1>{_esc(cv.name)}</h1>")
        if cv.contact:
            out.append(f'<div class="contact">{runs_to_html(cv.contact.runs)}</div>')
        out.append("</div>")

    # ── Sections ────────────────────────────────────────────────────────
    for sec in cv.sections:
        out.append(f"<h2>{_esc(sec.title)}</h2>")
        if sec.display == "chips":
            _render_chips(sec, out)
        else:
            _render_default(sec, out)

    out.append("</body></html>")
    return "".join(out)


# ── Section renderers ──────────────────────────────────────────────────────


def _render_default(sec: Section, out: list[str]) -> None:
    """Render a section with the standard layout."""
    for item in sec.content:
        if isinstance(item, SubSection):
            _render_subsection(item, out)
        elif isinstance(item, Paragraph):
            _render_para(item, out)
        elif isinstance(item, ListItem):
            _render_item(item, out, wrap=True)


def _render_chips(sec: Section, out: list[str]) -> None:
    """Render list items as horizontal chip / badge elements."""
    chips: list[str] = []
    for item in sec.content:
        if isinstance(item, ListItem):
            body = runs_to_html(item.runs)
            date_html = (
                f' <span class="date">{_esc(item.date)}</span>' if item.date else ""
            )
            chips.append(f'<li class="chip">{body}{date_html}</li>')
        else:
            # Flush accumulated chips before non-list content
            if chips:
                out.append(f'<ul class="chips">{"".join(chips)}</ul>')
                chips.clear()
            if isinstance(item, SubSection):
                _render_subsection(item, out)
            elif isinstance(item, Paragraph):
                _render_para(item, out)
    if chips:
        out.append(f'<ul class="chips">{"".join(chips)}</ul>')


def _render_subsection(sub: SubSection, out: list[str]) -> None:
    """Render an H3 subsection."""
    out.append('<div class="entry"><div class="entry-header">')
    title_html = (
        f'<a href="{_esc(sub.url)}">{_esc(sub.title)}</a>'
        if sub.url
        else _esc(sub.title)
    )
    out.append(f'<div class="entry-title">{title_html}</div>')
    if sub.date:
        out.append(f'<div class="date">{_esc(sub.date)}</div>')
    out.append("</div>")

    li_buf: list[str] = []
    for item in sub.content:
        if isinstance(item, ListItem):
            _render_item(item, li_buf, wrap=False)
        else:
            if li_buf:
                out.append(f'<ul>{"".join(li_buf)}</ul>')
                li_buf.clear()
            if isinstance(item, Paragraph):
                _render_para(item, out)
    if li_buf:
        out.append(f'<ul>{"".join(li_buf)}</ul>')
    out.append("</div>")


def _render_para(para: Paragraph, out: list[str]) -> None:
    """Render a paragraph with optional right-aligned date."""
    if para.date:
        out.append(
            f'<p class="line-flex">'
            f'<span class="flex-text">{runs_to_html(para.runs)}</span>'
            f'<span class="date">{_esc(para.date)}</span></p>'
        )
    else:
        out.append(f"<p>{runs_to_html(para.runs)}</p>")


def _render_item(item: ListItem, out: list[str], *, wrap: bool) -> None:
    """Render a single bullet-point item."""
    if item.date:
        inner = (
            f'<li class="line-flex">'
            f'<span class="flex-text">{runs_to_html(item.runs)}</span>'
            f'<span class="date">{_esc(item.date)}</span></li>'
        )
    else:
        inner = f"<li>{runs_to_html(item.runs)}</li>"
    out.append(f"<ul>{inner}</ul>" if wrap else inner)


# ── Public API ──────────────────────────────────────────────────────────────


def generate_pdf(cv: CV, output_path: str, template_path: str | None = None) -> str:
    """Generate a PDF file and return the output path."""
    template = load_template(template_path)
    html_string = generate_html(cv, template)
    HTML(string=html_string).write_pdf(output_path)
    return output_path
