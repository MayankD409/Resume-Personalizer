"""Utility functions for reading job descriptions and LaTeX templates."""
import pathlib, docx, fitz
from rich import print

def _read_pdf(path: pathlib.Path) -> str:
    """Read a PDF file and return its text content."""
    doc = fitz.open(path) # Fitz is a library for PDF manipulation
    return "\n".join(page.get_text() for page in doc) # seperate text on each page with newlines

def _read_docx(path: pathlib.Path) -> str:
    """Read a DOCX file and return its text content."""
    return "\n".join(p.text for p in docx.Document(path).paragraphs) # seperate text on each paragraph with newlines

def load_jd_text(path_or_args):
    """Load the job description text from a file or directly from the command line."""
    # Check if we're dealing with an args object or a direct path
    if hasattr(path_or_args, 'jd_text') and path_or_args.jd_text:
        return path_or_args.jd_text.strip()
    
    # Either a path string or args.jd_file
    file_path = path_or_args
    if hasattr(path_or_args, 'jd_file'):
        file_path = path_or_args.jd_file
    
    path = pathlib.Path(file_path).expanduser()
    if not path.exists():
        print(f"[red]Error: File {path} does not exist.[/red]")
        return None
    
    ext = path.suffix.lower()
    if ext == ".pdf": txt = _read_pdf(path)
    elif ext == ".docx": txt = _read_docx(path)
    else:
        txt = path.read_text(encoding="utf-8")
    print(f"[cyan]Loaded JD ({len(txt.split())} words) from {path}[/]")
    return txt

def load_template(template_path: pathlib.Path) -> list[str]:
    """Load the LaTeX template file and return its content as a list of strings."""
    path = pathlib.Path(template_path).expanduser()
    if not path.exists():
        FileNotFoundError(f"Template file {path} does not exist.")

    lines = path.read_text(encoding = "utf-8").splitlines() # splitlines returns a list of lines
    print(f"[cyan]Loaded template ({len(lines)} lines) from {path}[/]")
    return lines