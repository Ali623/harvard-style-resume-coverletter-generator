# Resume & Cover Letter Generator

Generates Aliullah's resume and cover letter as A4 `.docx` and `.pdf` files. Two ways to use it: a Streamlit web UI or CLI scripts.

## Quick start

```bash
pip install python-docx streamlit
streamlit run app.py
```

## Streamlit UI

1. Open the app in your browser
2. Choose **Paste AI Output** in the sidebar (or switch to **Manual Entry**)
3. Paste the complete output from your AI tool — it should contain sections like `2. Tailored Resume` and `3. Tailored Cover Letter`
4. Click **Parse Content**
5. Review and edit each section across the Resume and Cover Letter tabs
6. Enter the company name and role in the sidebar for folder naming
7. Click **Generate .docx & .pdf**
8. Download individual files or the ZIP bundle

## CLI

```bash
# With specific company/role
python generate_resume.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
python generate_coverletter.py --company "Bending Spoons" --role "Graduate AI Software Engineer"

# Using defaults
python generate_resume.py
python generate_coverletter.py
```

Output is written to `Aliullah-<Company>-<Role>/` containing:
- `resume.docx` (and `.pdf` if LibreOffice is installed)
- `coverletter.docx` (and `.pdf`)

## Expected AI output format

**JSON (preferred).** Paste the full JSON object with these top-level keys:

```json
{
  "tailored_resume": {
    "name": "Aliullah",
    "contact": {
      "location": "Nuremberg, Germany",
      "phone": "+49 176 58127708",
      "email": "[aliullah623@gmail.com](mailto:aliullah623@gmail.com)",
      "linkedin": "[https://www.linkedin.com/in/aliullah623](https://...)",
      "github": "[https://github.com/Ali623](https://...)"
    },
    "professional_summary": ["line one", "line two"],
    "education": [
      {
        "institution": "University Name",
        "location": "City, Country",
        "degree": "MSc Artificial Intelligence",
        "grade": "1.6",
        "dates": "April 2023 to March 2026"
      }
    ],
    "experience": [
      {
        "company": "Company Name",
        "location": "City, Country",
        "title": "Job Title",
        "dates": "October 2024 to Present",
        "bullet_points": ["bullet one", "bullet two"]
      }
    ],
    "digital_competencies": [
      {"category": "Programming", "skills": ["Python", "SQL"]}
    ],
    "certifications": ["Cert Name from provider"],
    "projects": [
      {"name": "Project Name", "description": "What it does"}
    ],
    "achievements": ["Achievement description"]
  },
  "cover_letter": {
    "salutation": "Dear Hiring Team,",
    "paragraphs": ["para one", "para two", "para three"],
    "closing": "Sincerely,",
    "signature": "Aliullah"
  }
}
```

Additional top-level keys (`job_description_analysis`, `optimization_notes`, `warnings`, `linkedin_message`) are ignored.

**Free-form text (fallback).** The parser also accepts text with `2. Tailored Resume` and `3. Tailored Cover Letter` section markers.

## Requirements

- Python 3.12+
- `python-docx` and `streamlit` (see `pyproject.toml`)
- LibreOffice (optional, for PDF conversion)
