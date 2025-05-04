# Resume Tailor

An AI-powered tool to automatically tailor your resume for specific job descriptions.

## Overview

Resume Tailor uses a two-pass LLM (Large Language Model) approach to customize your LaTeX resume for specific job descriptions:

1. **Pass 1: Project Selection** - Analyzes your resume and the job description to determine which projects to include/exclude
2. **Pass 2: Bullet Point & Skills Optimization** - Rewrites bullet points and reorders skills to better match the job requirements

The tool provides interactive review of changes, keyword analysis, and professional resume optimization aligned with the role you're applying for.

## Features

- **Smart Project Selection**: Automatically selects the most relevant projects from your resume based on job requirements
- **Bullet Point Optimization**: Rewrites bullet points to be more impactful, achievement-focused, and keyword-rich
- **Skills Section Reordering**: Highlights the most relevant skills for the position
- **Keyword Analysis**: Analyzes how well your resume matches the job description and suggests improvements
- **Interactive Mode**: Review changes with colorized diffs and selectively apply modifications
- **Resume Metrics**: Get quantitative feedback on your resume's match to the job description
- **Role-Specific Guidance**: Tailors format and content based on the specific role you're applying for

## Installation

### Prerequisites

- Python 3.8+ 
- LaTeX installation (for compiling the final resume)
- OpenAI or Google API key (for accessing AI models)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resume-tailor.git
   cd resume-tailor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install the required spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. Set up your API key:
   ```bash
   # For OpenAI (GPT-4)
   export OPENAI_API_KEY=your_api_key_here
   
   # For Google (Gemini)
   export GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

```bash
python -m src.cli --jd-file path/to/job_description.pdf --role "Software Engineer" --company "Tech Corp" --template path/to/resume.tex
```

### Full Command-Line Options

```
usage: resume-tailor [-h] [--jd-file JD_FILE] [--jd-text JD_TEXT] --role ROLE --company COMPANY [--template TEMPLATE]
                     [--mode MODE] [--output OUTPUT] [--debug] [--model MODEL] [--keyword-analysis] [--no-color]

Automate LaTeX resume tailoring for a Job Description.

options:
  -h, --help            show this help message and exit
  --jd-file JD_FILE     Path to JD .txt/.pdf/.docx
  --jd-text JD_TEXT     Paste JD string directly (mutually exclusive)
  --role ROLE           Job role being applied for
  --company COMPANY     Company name
  --template TEMPLATE   Path to template .tex file (default: templates/resume_template.tex)
  --mode MODE           Output mode ('interactive', 'auto', 'preview') (default: interactive)
  --output OUTPUT       Output path for the tailored resume (default: output)
  --debug               Enable debug logging
  --model MODEL         AI model to use (default: gpt-4o)
  --keyword-analysis    Enable keyword matching analysis
  --no-color            Disable colored output
```

### Example Workflow

1. **Prepare your LaTeX resume template** with project blocks that can be toggled on/off
2. **Save the job description** as a PDF, DOCX, or TXT file
3. **Run the tool** with appropriate arguments
4. **Review the changes** in interactive mode
5. **Compile the final LaTeX file** to produce your tailored PDF resume

## LaTeX Resume Format

Your LaTeX resume should follow certain conventions to work best with this tool:

1. **Project blocks** should be defined with clear start/end markers
2. **Skills section** should start with `\textbf{Languages:}`
3. **Bullet points** should be well-formatted for easy identification

Example project block format:
```latex
% PROJECT-START: Project Title
\textbf{Project Title} \hfill \textit{Technologies Used} \\
Some description here with bullet points:
\begin{itemize}
    \item Accomplished X resulting in Y improvement
    \item Implemented Z technology to solve problem A
\end{itemize}
% PROJECT-END
```

## How It Works

The tool uses a two-pass approach:

1. **First LLM Pass**:
   - Analyzes your resume and the job description
   - Selects the most relevant projects
   - Returns a JSON list of projects to include/exclude

2. **Second LLM Pass**:
   - After applying project selection, reviews the updated resume
   - Rewrites bullet points to be more impactful and relevant
   - Reorders skills to prioritize those most relevant to the job

3. **Interactive Review**:
   - Shows a diff of proposed changes
   - Allows you to selectively apply specific changes
   - Provides keyword matching analysis

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors who have helped shape this project
- Special thanks to the developers of the libraries this tool depends on 