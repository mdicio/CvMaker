"""Web-based CV builder — Flask server.

Serves a browser UI that lets users build CVs graphically, with live preview
and PDF / DOCX / Markdown export.  The existing markdown-based CLI workflow is
completely unaffected.
"""

import io
import json
import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

from .docx_generator import generate_docx
from .parser import (
    CV,
    ListItem,
    Paragraph,
    Section,
    SubSection,
    TextRun,
    parse_file,
    parse_inline,
)
from .pdf_generator import generate_html, generate_pdf, load_template

# ── Setup ────────────────────────────────────────────────────────────────────

WEB_DIR = Path(__file__).parent / "web"

app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates"


def _list_templates() -> list[dict]:
    td = _templates_dir()
    descriptions = {
        "default": "Standard formatting (11pt, 0.75in margins)",
        "compact": "Compact for one-page CVs (9pt, 0.5in margins)",
        "compact-narrow": "Ultra-compact with minimal margins (8pt, 0.3in margins)",
    }
    result = []
    for f in sorted(td.glob("*.json")):
        tid = f.stem
        result.append(
            {
                "id": tid,
                "name": tid.replace("-", " ").title(),
                "description": descriptions.get(tid, ""),
            }
        )
    return result


def _resolve_template(tmpl_id: str) -> str:
    p = _templates_dir() / f"{tmpl_id}.json"
    return str(p) if p.exists() else str(_templates_dir() / "default.json")


# ── CV ↔ JSON helpers ────────────────────────────────────────────────────────


def _runs_to_md(runs: list[TextRun]) -> str:
    """Convert TextRun list back to a markdown-formatted string."""
    parts: list[str] = []
    for r in runs:
        t = r.text
        if r.url:
            t = f"[{t}]({r.url})"
        elif r.bold and r.italic:
            t = f"***{t}***"
        elif r.bold:
            t = f"**{t}**"
        elif r.italic:
            t = f"*{t}*"
        parts.append(t)
    return "".join(parts)


def cv_to_web(cv: CV) -> dict:
    """CV object → web builder JSON dict."""
    contact_str = _runs_to_md(cv.contact.runs) if cv.contact else ""
    sections: list[dict] = []
    for sec in cv.sections:
        items: list[dict] = []
        for item in sec.content:
            if isinstance(item, SubSection):
                # SubSection.title may be "Title | Org"
                parts = [p.strip() for p in item.title.split(" | ")]
                title = parts[0]
                org = parts[1] if len(parts) > 1 else ""
                sub_items: list[dict] = []
                for si in item.content:
                    if isinstance(si, ListItem):
                        sub_items.append(
                            {
                                "type": "bullet",
                                "text": _runs_to_md(si.runs),
                                "date": si.date or "",
                            }
                        )
                    else:
                        sub_items.append(
                            {"type": "paragraph", "text": _runs_to_md(si.runs)}
                        )
                items.append(
                    {
                        "type": "subsection",
                        "title": title,
                        "org": org,
                        "date": item.date or "",
                        "url": item.url or "",
                        "items": sub_items,
                    }
                )
            elif isinstance(item, ListItem):
                items.append(
                    {
                        "type": "bullet",
                        "text": _runs_to_md(item.runs),
                        "date": item.date or "",
                    }
                )
            else:  # Paragraph
                items.append({"type": "paragraph", "text": _runs_to_md(item.runs)})
        sections.append({"title": sec.title, "display": sec.display, "content": items})
    return {
        "name": cv.name,
        "subtitle": cv.subtitle,
        "contact": contact_str,
        "sections": sections,
    }


def web_to_cv(data: dict) -> CV:
    """Web builder JSON dict → CV object."""
    cv = CV(name=data.get("name", ""), subtitle=data.get("subtitle", ""))
    contact = (data.get("contact") or "").strip()
    if contact:
        cv.contact = Paragraph(runs=parse_inline(contact))

    for sd in data.get("sections", []):
        sec = Section(title=sd.get("title", ""), display=sd.get("display", "default"))
        for item in sd.get("content", []):
            t = item.get("type", "paragraph")
            if t == "subsection":
                title_parts = [item.get("title", "")]
                if (item.get("org") or "").strip():
                    title_parts.append(item["org"].strip())
                sub = SubSection(
                    title=" | ".join(title_parts),
                    date=item.get("date") or None,
                    url=item.get("url") or None,
                )
                for si in item.get("items", []):
                    if si.get("type") == "bullet":
                        sub.content.append(
                            ListItem(
                                runs=parse_inline(si.get("text", "")),
                                date=si.get("date") or None,
                            )
                        )
                    else:
                        sub.content.append(
                            Paragraph(runs=parse_inline(si.get("text", "")))
                        )
                sec.content.append(sub)
            elif t == "bullet":
                sec.content.append(
                    ListItem(
                        runs=parse_inline(item.get("text", "")),
                        date=item.get("date") or None,
                    )
                )
            else:  # paragraph
                sec.content.append(Paragraph(runs=parse_inline(item.get("text", ""))))
        cv.sections.append(sec)
    return cv


def cv_to_markdown(cv: CV) -> str:
    """CV object → markdown string (round-trips with the existing parser)."""
    out: list[str] = [f"# {cv.name}", ""]
    if cv.subtitle:
        out.append(cv.subtitle)
    if cv.contact:
        out.append(_runs_to_md(cv.contact.runs))
    out.append("")
    for sec in cv.sections:
        out.append(f"## {sec.title}")
        if sec.display == "chips":
            out.append("<!-- chips -->")
        for item in sec.content:
            if isinstance(item, SubSection):
                h = [item.title]
                if item.date:
                    h.append(item.date)
                out.append(f"### {' | '.join(h)}")
                for si in item.content:
                    if isinstance(si, ListItem):
                        txt = _runs_to_md(si.runs)
                        if si.date:
                            txt += f" | {si.date}"
                        out.append(f"- {txt}")
                    else:
                        out.append(_runs_to_md(si.runs))
            elif isinstance(item, ListItem):
                txt = _runs_to_md(item.runs)
                if item.date:
                    txt += f" | {item.date}"
                out.append(f"- {txt}")
            else:  # Paragraph
                out.append(_runs_to_md(item.runs))
        out.append("")
    return "\n".join(out)


# ── Routes ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


@app.route("/api/templates")
def api_templates():
    return jsonify(_list_templates())


@app.route("/api/preview", methods=["POST"])
def api_preview():
    data = request.get_json(force=True)
    cv = web_to_cv(data.get("cv", {}))
    tmpl = load_template(_resolve_template(data.get("template", "default")))
    html = generate_html(cv, tmpl)
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/api/export/pdf", methods=["POST"])
def api_export_pdf():
    data = request.get_json(force=True)
    cv = web_to_cv(data.get("cv", {}))
    tmpl_path = _resolve_template(data.get("template", "default"))
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out_path = f.name
    try:
        generate_pdf(cv, out_path, tmpl_path)
        fname = (cv.name or "cv").replace(" ", "_") + ".pdf"
        return send_file(
            out_path,
            as_attachment=True,
            download_name=fname,
            mimetype="application/pdf",
        )
    finally:
        # Flask streams the file; schedule cleanup after response
        pass


@app.route("/api/export/docx", methods=["POST"])
def api_export_docx():
    data = request.get_json(force=True)
    cv = web_to_cv(data.get("cv", {}))
    tmpl_path = _resolve_template(data.get("template", "default"))
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        out_path = f.name
    generate_docx(cv, out_path, tmpl_path)
    fname = (cv.name or "cv").replace(" ", "_") + ".docx"
    return send_file(
        out_path,
        as_attachment=True,
        download_name=fname,
        mimetype=(
            "application/vnd.openxmlformats-officedocument" ".wordprocessingml.document"
        ),
    )


@app.route("/api/export/markdown", methods=["POST"])
def api_export_markdown():
    data = request.get_json(force=True)
    cv = web_to_cv(data.get("cv", {}))
    md = cv_to_markdown(cv)
    fname = (cv.name or "cv").replace(" ", "_") + ".md"
    return send_file(
        io.BytesIO(md.encode("utf-8")),
        as_attachment=True,
        download_name=fname,
        mimetype="text/markdown",
    )


@app.route("/api/import/markdown", methods=["POST"])
def api_import_markdown():
    if "file" in request.files:
        content = request.files["file"].read().decode("utf-8")
    else:
        content = (request.get_json(force=True) or {}).get("markdown", "")

    with tempfile.NamedTemporaryFile(
        suffix=".md", delete=False, mode="w", encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name
    try:
        cv = parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)
    return jsonify(cv_to_web(cv))


# ── Entry point ──────────────────────────────────────────────────────────────


def run_web(host: str = "127.0.0.1", port: int = 5173, debug: bool = False) -> None:
    """Start the web-based CV builder server."""
    import webbrowser

    url = f"http://{host}:{port}"
    print(f"\n  ✦ CV Maker Web Builder")
    print(f"    Open: {url}\n")
    if not debug:
        webbrowser.open(url)
    app.run(host=host, port=port, debug=debug, use_reloader=debug)


if __name__ == "__main__":
    run_web(debug=True)
