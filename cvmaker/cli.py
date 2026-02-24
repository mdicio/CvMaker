"""Command-line interface for CV Maker."""

import argparse
import sys
from pathlib import Path

from .parser import parse_file
from .docx_generator import generate_docx
from .pdf_generator import generate_pdf


def get_templates_dir() -> Path:
    """Get the templates directory path."""
    return Path(__file__).parent / "templates"


def list_templates() -> list[str]:
    """List available templates."""
    templates_dir = get_templates_dir()
    if not templates_dir.exists():
        return []
    return [f.stem for f in templates_dir.glob("*.json")]


def main(args: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cvmaker",
        description="Convert markdown CVs to DOCX and PDF formats.",
        epilog="Examples:\n"
        "  cvmaker resume.md                    Generate both DOCX and PDF\n"
        "  cvmaker resume.md -t compact         Use compact template (one-page)\n"
        "  cvmaker resume.md -f pdf             Generate PDF only\n"
        "  cvmaker --list-templates             Show available templates\n"
        "  cvmaker --gui                        Launch graphical interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", nargs="?", help="Input markdown file")

    parser.add_argument(
        "-o", "--output", help="Output file path (used when generating single format)"
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["docx", "pdf", "both"],
        default="both",
        help="Output format: docx, pdf, or both (default: both)",
    )

    parser.add_argument(
        "-t",
        "--template",
        help='Template name (e.g., "compact") or path to custom JSON template',
    )

    parser.add_argument(
        "--list-templates", action="store_true", help="List available templates"
    )

    parser.add_argument("--gui", action="store_true", help="Launch graphical interface")

    parsed_args = parser.parse_args(args)

    # List templates if requested
    if parsed_args.list_templates:
        templates = list_templates()
        if templates:
            print("Available templates:")
            descriptions = {
                "default": "Standard formatting (11pt, 0.75in margins)",
                "compact": "Compact for one-page CVs (9pt, 0.5in margins)",
                "compact-narrow": "Ultra-compact with minimal margins (8pt, 0.3in margins)",
            }
            for t in sorted(templates):
                desc = descriptions.get(t, "")
                print(f"  {t:20} {desc}")
        else:
            print("No templates found.")
        return 0

    # Launch GUI if requested
    if parsed_args.gui:
        from .gui import run_gui

        run_gui()
        return 0

    # Validate input
    if not parsed_args.input:
        parser.error("Input file is required (or use --gui for graphical interface)")

    input_path = Path(parsed_args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    if not input_path.suffix.lower() in [".md", ".markdown", ".txt"]:
        print(f"Warning: Input file may not be markdown: {input_path}", file=sys.stderr)

    # Parse the CV
    try:
        cv = parse_file(str(input_path))
    except Exception as e:
        print(f"Error parsing input file: {e}", file=sys.stderr)
        return 1

    # Determine output format and path
    output_formats = []
    output_dir = input_path.parent
    output_base = input_path.stem

    if parsed_args.format == "both":
        output_formats = ["docx", "pdf"]
    elif parsed_args.format:
        output_formats = [parsed_args.format]
    elif parsed_args.output:
        ext = Path(parsed_args.output).suffix.lower()
        if ext == ".docx":
            output_formats = ["docx"]
        elif ext == ".pdf":
            output_formats = ["pdf"]
        else:
            print(f"Error: Unknown output format: {ext}", file=sys.stderr)
            return 1
    else:
        output_formats = ["docx", "pdf"]

    # Resolve template path
    template_path = None
    if parsed_args.template:
        # Check if it's a template name or a path
        if Path(parsed_args.template).exists():
            template_path = parsed_args.template
        else:
            # Try to find it in templates directory
            templates_dir = get_templates_dir()
            template_file = templates_dir / f"{parsed_args.template}.json"
            if template_file.exists():
                template_path = str(template_file)
            else:
                print(
                    f"Error: Template not found: {parsed_args.template}",
                    file=sys.stderr,
                )
                print(
                    f"Use --list-templates to see available templates.", file=sys.stderr
                )
                return 1

    # Generate output files

    for fmt in output_formats:
        if parsed_args.output and len(output_formats) == 1:
            output_path = parsed_args.output
        else:
            output_path = str(output_dir / f"{output_base}.{fmt}")

        try:
            if fmt == "docx":
                generate_docx(cv, output_path, template_path)
                print(f"Generated: {output_path}")
            elif fmt == "pdf":
                generate_pdf(cv, output_path, template_path)
                print(f"Generated: {output_path}")
        except Exception as e:
            print(f"Error generating {fmt.upper()}: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
