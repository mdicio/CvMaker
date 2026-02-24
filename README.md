# CV Maker

Write your CV in simple Markdown → get a professionally formatted **PDF** and **DOCX** ready to send.

No design skills needed. No Word template wrestling. Just write, generate, done.

**[🌐 Try the online editor →](https://mdicio.github.io/CvMaker/)**

---

## ✨ Features

- **Markdown in, polished CV out** — write in plain text, get beautiful documents
- **PDF + DOCX** — generate one or both formats in a single command
- **Online editor** — browser-based UI hosted free on GitHub Pages, no install needed
- **Standard markdown links** — `[LinkedIn](https://...)` renders as clickable hyperlinks
- **Flexible sections** — any section name works; use `<!-- chips -->` for tag-style display
- **Multiple templates** — default, compact, and ultra-compact layouts
- **Custom templates** — tweak fonts, colours, margins, and spacing via simple JSON
- **ATS-friendly** — clean structure that applicant tracking systems can parse
- **Desktop GUI included** — Tkinter interface for those who prefer clicking

## 🌐 Online Editor

Use CVMaker directly in your browser — no installation required:

**[https://mdicio.github.io/CvMaker/](https://mdicio.github.io/CvMaker/)**

- Write / paste your markdown on the left
- See a live preview on the right
- Switch templates with the dropdown
- Click **Print / Save PDF** to download

### Host Your Own

1. Fork this repository
2. Go to **Settings → Pages**
3. Set source to **Deploy from a branch**, branch `main`, folder `/docs`
4. Your editor will be live at `https://<username>.github.io/CvMaker/`

## 📦 Installation (CLI / Python)

### Quick Install

```bash
pip install .
```

This gives you a `cvmaker` command you can run from anywhere.

### From Source

```bash
git clone https://github.com/mdicio/CvMaker.git
cd CvMaker
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### System Dependencies

PDF generation uses [WeasyPrint](https://weasyprint.org/), which needs some system libraries:

```bash
# Ubuntu / Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0

# macOS
brew install pango gdk-pixbuf libffi

# Fedora
sudo dnf install pango gdk-pixbuf2
```

> If you only need DOCX output, you can skip this — DOCX generation works without extra dependencies.

## 🚀 Usage

### 1. Write Your CV in Markdown

Create a `.md` file (see [examples/sample_cv.md](examples/sample_cv.md)):

```markdown
# Jane Smith

Full-Stack Developer

**Email:** jane@email.com | **Phone:** +1 555-0123 | [LinkedIn](https://linkedin.com/in/janesmith) | [GitHub](https://github.com/janesmith)

## Summary

Software engineer with 5+ years building scalable web applications.

## Experience

### Lead Engineer | TechCorp | 2021 - Present
- Architected microservices handling 2M+ daily requests
- Led a team of 6 engineers

### Software Engineer | StartupABC | 2018 - 2021
- Built real-time data pipelines processing 500K events/hour

## Education

### M.S. Computer Science | Tech University | 2018

## Skills

- **Languages:** Python, Go, TypeScript
- **Cloud:** AWS, Kubernetes, Terraform

## Certifications
<!-- chips -->
- AWS Solutions Architect | 2023
- CKA | 2022
```

### 2. Generate Your CV

```bash
# Generate both PDF and DOCX (default)
cvmaker resume.md

# PDF only
cvmaker resume.md -f pdf

# Use compact template for a one-page CV
cvmaker resume.md -t compact

# Custom output path
cvmaker resume.md -f pdf -o ~/Documents/my_resume.pdf
```

### 3. Or Use the Desktop GUI

```bash
cvmaker --gui
```

## 📝 Markdown Format

| Syntax | What it becomes |
|--------|-----------------|
| `# Name` | Your name (centred in header) |
| Line after `#` (no pipes) | Subtitle, shown beside name |
| Line with `\|` separators | Contact info row |
| `## Section` | Section heading |
| `### Title \| Org \| 2021 - Present` | Entry with right-aligned date |
| `- Bullet text` | Bullet point |
| `- Item \| 2023` | Bullet with right-aligned date |
| `**bold**` / `*italic*` | Formatting |
| `[text](url)` | Clickable hyperlink |
| `<!-- chips -->` | Place after `##` to render items as tags |

### Date convention

The **last pipe-separated segment** on `###` headings and `- ` list items is treated as a date when it matches a recognised pattern (e.g. `2024`, `2020 - Present`, `Jan 2023`, `01/2024 - 12/2025`). Everything else stays as the title or body text.

### Display hints

Add an HTML comment right after a `## Section` heading to change how its content renders:

```markdown
## Certifications
<!-- chips -->
- AWS Solutions Architect | 2023
- CKA | 2022
```

Currently supported hints: `chips` (horizontal tags). Default is standard list rendering.

## 🎨 Templates

| Template | Description | Best for |
|----------|-------------|----------|
| `default` | Standard layout (11pt, 0.75in margins) | Multi-page CVs |
| `compact` | Tighter spacing (9pt, 0.5in margins) | One-page CVs |
| `compact-narrow` | Minimal margins (8pt, 0.3in margins) | Dense one-page CVs |

```bash
cvmaker --list-templates
cvmaker resume.md -t compact
```

### Custom Templates

Create a JSON file:

```json
{
    "fonts": {
        "name": "Calibri",
        "heading1_size": 24,
        "heading2_size": 14,
        "heading3_size": 12,
        "body_size": 11
    },
    "colors": {
        "heading": "#2c3e50",
        "subheading": "#34495e",
        "body": "#333333",
        "accent": "#3498db"
    },
    "spacing": {
        "section_before": 12,
        "section_after": 6,
        "line_spacing": 1.15
    },
    "margins": {
        "top": 0.75,
        "bottom": 0.75,
        "left": 0.75,
        "right": 0.75
    }
}
```

```bash
cvmaker resume.md -t /path/to/my_template.json
```

## 📁 Project Structure

```
cvmaker/
├── cvmaker/                   # Python package
│   ├── cli.py                 # Command-line interface
│   ├── parser.py              # Markdown → structured data
│   ├── pdf_generator.py       # Structured data → PDF (WeasyPrint)
│   ├── docx_generator.py      # Structured data → DOCX (python-docx)
│   ├── gui.py                 # Tkinter desktop GUI
│   └── templates/             # Built-in style templates
├── docs/
│   └── index.html             # Web editor (GitHub Pages)
├── examples/
│   └── sample_cv.md           # Example CV
├── pyproject.toml
├── LICENSE
└── README.md
```

## 💡 Tips

- **One-page CV?** Use `-t compact` or `-t compact-narrow`
- **Links in your CV** — use `[text](url)` for clickable LinkedIn, GitHub, etc.
- **Chip-style certifications** — add `<!-- chips -->` after the section heading
- **The `|` separator is key** — `### Title | Company | Date` splits into a title with a right-aligned date
- **Any section name works** — Skills, Projects, Publications, Languages, etc.

## 🛠 Troubleshooting

**PDF generation fails?**
→ Install WeasyPrint system dependencies (see [Installation](#-installation-cli--python))

**Fonts look wrong?**
→ The default font is Calibri. On Linux, install `fonts-crosextra-carlito` for a free Calibri-compatible font.

**DOCX only (skip PDF)?**
→ Use `cvmaker resume.md -f docx` — no WeasyPrint needed.

## 📄 License

[MIT](LICENSE)
