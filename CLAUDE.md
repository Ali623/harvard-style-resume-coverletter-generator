# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Generates Aliullah's resume and cover letter as `.docx` and `.pdf` on A4. Two interfaces: CLI scripts and a Streamlit web UI.

## Commands

**Streamlit UI:**
```
streamlit run app.py
```

**CLI:**
```
python generate_resume.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
python generate_coverletter.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
```

Output goes to `Aliullah-<Company>-<Role>/` folder containing `resume.docx` and `coverletter.docx` (plus `.pdf` if LibreOffice is installed).

## Dependencies

- Python 3.12 (`.python-version`)
- `python-docx` and `streamlit` (see `pyproject.toml`)
- LibreOffice (optional, for PDF conversion)

## Architecture

```
resume_generator/         # Core package
├── models.py             # Dataclasses: Resume, CoverLetter, Education, Experience, Skill, Project
├── renderer.py           # Shared docx XML helpers + design tokens (Calibri 11pt body, TNR 14pt headings)
├── builder.py            # build_resume() and build_coverletter() — assembles docx from models
├── parser.py             # parse_ai_output() — extracts Resume + CoverLetter from AI job-analysis text
├── validate.py           # Budget class — character-count validation per line type
└── pdf.py                # convert_to_pdf() — LibreOffice headless conversion

app.py                    # Streamlit UI: paste AI output → parse → edit → generate → download
generate_resume.py        # Thin CLI wrapper around resume_generator
generate_coverletter.py   # Thin CLI wrapper around resume_generator
_validate.py              # Backward-compat re-export of Budget
main.py                   # Stub, unused
```

## Data flow (Streamlit UI)

1. User pastes AI-generated job analysis output into text area
2. `parse_ai_output()` splits on "Tailored Resume" / "Tailored Cover Letter" section markers
3. Parsed content populates `Resume` and `CoverLetter` dataclass instances
4. Editable previews shown in tabs
5. On "Generate", `build_resume()` and `build_coverletter()` produce `.docx` files
6. `convert_to_pdf()` attempts PDF conversion via LibreOffice
7. Download buttons for individual files or ZIP bundle

## Design tokens

Resume body: Calibri 11pt, headings: Times New Roman 14pt, name: Times New Roman 22pt.
Cover letter body: Times New Roman 11pt, header/contact: Calibri 10pt, name: Times New Roman 22pt.
Both use A4 with tight margins. Character budgets in `builder.py` enforce single-line bullets.

## Content defaults

`models.py` contains `DEFAULT_RESUME` and `DEFAULT_COVER` with hardcoded fallback content. The Streamlit UI uses these as initial state before parsing.
