# CV Maker

Write your CV in simple Markdown → get a professionally formatted **PDF** and **DOCX** ready to send.

No design skills needed. No Word template wrestling. Just write, generate, done.

---

## ✨ Features

- **Markdown in, polished CV out** — write in plain text, get beautiful documents
- **PDF + DOCX** — generate one or both formats in a single command
- **Google Docs compatible** — DOCX files open and edit perfectly in Google Docs
- **Multiple templates** — default, compact (one-page), and ultra-compact layouts
- **Custom templates** — tweak fonts, colors, margins, and spacing via simple JSON
- **ATS-friendly** — clean structure that applicant tracking systems can parse
- **GUI included** — graphical interface for those who prefer clicking over typing

## 📦 Installation

### Quick Install (recommended)

```bash
pip install .
```

This gives you a `cvmaker` command you can run from anywhere.

### From Source (development)

```bash
git clone https://github.com/yourusername/cvmaker.git
cd cvmaker
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
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

Create a `.md` file (see [examples/sample_cv.md](examples/sample_cv.md) for a full example):

```markdown
# Jane Smith

**Email:** jane@email.com | **LinkedIn:** linkedin.com/in/janesmith

## Summary

Software engineer with 5+ years of experience in full-stack development.

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
```

### 2. Generate Your CV

```bash
# Generate both PDF and DOCX (default)
cvmaker resume.md

# PDF only
cvmaker resume.md -f pdf

# DOCX only
cvmaker resume.md -f docx

# Use compact template for a one-page CV
cvmaker resume.md -t compact

# Custom output path
cvmaker resume.md -f pdf -o ~/Documents/my_resume.pdf
```

Output files are saved next to the input file by default.

### 3. Or Use the GUI

```bash
cvmaker --gui
```

Browse for your file, pick a format, click Generate.

## 📝 Markdown Format Guide

| Syntax | What It Becomes |
|--------|-----------------|
| `# Name` | Your name (centered in header) |
| `## Section` | Section title (Experience, Education, etc.) |
| `### Title \| Company \| 2021 - Present` | Entry with right-aligned date |
| `- Bullet point` | Bullet point |
| `**bold**` | **Bold text** |
| `*italic*` | *Italic text* |

**Dates**: Put the date as the last pipe-separated item on an `###` line — it gets right-aligned automatically:

```markdown
### Software Engineer | Google | 2020 - Present
```

## 🎨 Templates

| Template | Description | Best For |
|----------|-------------|----------|
| `default` | Standard layout (11pt, 0.75in margins) | Multi-page CVs |
| `compact` | Tighter spacing (9pt, 0.5in margins) | One-page CVs |
| `compact-narrow` | Minimal margins (8pt, 0.3in margins) | Dense one-page CVs |

```bash
# List available templates
cvmaker --list-templates

# Use a template
cvmaker resume.md -t compact
```

### Custom Templates

Create a JSON file with your preferred styling:

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

Use it with:

```bash
cvmaker resume.md -t /path/to/my_template.json
```

## 📁 Project Structure

```
cvmaker/
├── cvmaker/                   # Python package
│   ├── cli.py                 # Command-line interface
│   ├── parser.py              # Markdown → structured data
│   ├── pdf_generator.py       # Structured data → PDF
│   ├── docx_generator.py      # Structured data → DOCX
│   ├── gui.py                 # Tkinter GUI
│   └── templates/             # Built-in style templates
│       ├── default.json
│       ├── compact.json
│       └── compact-narrow.json
├── examples/
│   └── sample_cv.md           # Example CV to get started
├── pyproject.toml             # Package configuration
├── LICENSE                    # MIT License
└── README.md
```

## 💡 Tips

- **One-page CV?** Use `-t compact` or `-t compact-narrow`
- **Keep it concise**: 3–4 bullet points per role works best
- **Any section name works**: Skills, Projects, Certifications, Languages — the parser handles them all
- **The `|` separator is key**: `### Title | Company | Date` splits into a title with a right-aligned date

## 🛠 Troubleshooting

**PDF generation fails?**
→ Install WeasyPrint system dependencies (see [Installation](#-installation))

**Fonts look wrong?**
→ The default font is Calibri. If unavailable, it falls back to Arial / sans-serif. Install `fonts-crosextra-carlito` for a free Calibri-compatible font on Linux.

**DOCX only (skip PDF)?**
→ Use `cvmaker resume.md -f docx` — no WeasyPrint needed.

## 📄 License

[MIT](LICENSE)
