# Parse command line arguments
import argparse
from io_utils import load_jd_text, load_template
from path_utils import prepare_output_dir

def build_parser():
    p = argparse.ArgumentParser(progdescription="resume-tailor", description="Automate LaTeX reume tailoring for a Job Description.")
    p.add_argument("--jd-file", help="Path to JD .txt/.pdf/.docx")
    p.add_argument("--jd-text", help="Paste JD string directly (mutually exclusive)")
    p.add_argument("--role",    required=True, help="Role title")
    p.add_argument("--company", required=True, help="Company name")
    p.add_argument("--agent",   choices=["chatgpt","gemini"], default="chatgpt")
    p.add_argument("--template",default="templates/base_resume.tex",
                    help="Path to base LaTeX resume")

    return p

def main():
    args = build_parser().parse_args()

    # 1) Load JD text (pdf/txt/docx or direct string)
    job_description = load_jd_text(args)

    # 2) Load template into list[str]
    template_lines = load_template(args.template)

    # Prepare /Company/Role/ directory
    out_dir = prepare_output_dir(args.company, args.role)
    print(f"[cyan]Output directory: {out_dir}[/]")

if __name__ == "__main__":
    main()
 