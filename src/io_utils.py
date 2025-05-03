import pathlib, docx, fitz
from rich import print

def _read_pdf(path: pathlib.Path) -> str:
    """Read a PDF file and return its text content."""
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)

def _read_docx(path: pathlib.Path) -> str:
    """Read a DOCX file and return its text content."""
    return "\n".join(p.text for p in docx.Document(path).paragraphs)

def load_jd_text(args):
    """Load the job description text from a file or directly from the command line."""
    if args.jd_text:
        return args.jd_text.strip()
    
    path = pathlib.Path(args.jd_file).expanduser()
    if not path.exists():
        print(f"[red]Error: File {path} does not exist.[/red]")
        return None
    
    ext = path.suffix.lower()
    if ext == ".pdf": txt = _read_pdf(path)
    elif ext == ".docx": txt = _read_docx(path)
    else:
        txt = path.read_text(encodind="utf-8")
    print(f"[cyan]Loaded JD ({len(txt.split())} words) from {path}[/]")
    return txt

def load_template(template_path: pathlib.Path) -> list[str]:
    """Load the LaTeX template file and return its content as a list of strings."""
    path = pathlib.Path(template_path).expanduser()
    if not path.exists():
        FileNotFoundError(f"Template file {path} does not exist.")

    lines = path.read_text(encoding = "utf-8").splitlines()
    print(f"[cyan]Loaded template ({len(lines)} lines) from {path}[/]")
    return lines