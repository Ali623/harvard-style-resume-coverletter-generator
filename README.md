# Resume & Cover Letter Generator

Generates A4 resumes and cover letters as `.docx` and `.pdf` files. Two interfaces: a Streamlit web UI or CLI scripts. Fill in your details and generate tailored applications for any role.

## Setup

### With uv (recommended)

```bash
# Create venv and install dependencies in one step
uv sync

# Activate the venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install Playwright browsers (needed for job scraping)
playwright install chromium
```

### With standard venv

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install python-docx streamlit requests python-dotenv playwright
# Windows only:
pip install pywin32
# Install Playwright browsers (needed for job scraping)
playwright install chromium
```

### Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `DEEPSEEK_API_KEY` | API key for DeepSeek (AI content generation) |
| `LINKEDIN_EMAIL` | LinkedIn account email (for job scraping) |
| `LINKEDIN_PASSWORD` | LinkedIn account password |
| `XING_EMAIL` | XING account email (for job scraping) |
| `XING_PASSWORD` | XING account password |

### Run

```bash
# Streamlit web UI
streamlit run app.py

# Or use CLI
python generate_resume.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
python generate_coverletter.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
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

Output is written to `<Company>-<Role>/` containing:
- `resume.docx` (and `.pdf` if LibreOffice is installed)
- `coverletter.docx` (and `.pdf`)

## Expected AI output format

**JSON (preferred).** Paste the full JSON object with these top-level keys:

```json
{
  "tailored_resume": {
    "name": "Your Name",
    "contact": {
      "location": "City, Country",
      "phone": "+1 234 567890",
      "email": "your.email@example.com",
      "linkedin": "linkedin.com/in/yourprofile",
      "github": "github.com/yourusername"
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
    "signature": "Your Name"
  }
}
```

Additional top-level keys (`job_description_analysis`, `optimization_notes`, `warnings`, `linkedin_message`) are ignored.

**Free-form text (fallback).** The parser also accepts text with `2. Tailored Resume` and `3. Tailored Cover Letter` section markers.

## Requirements

- Python 3.12+
- `python-docx` and `streamlit` (see `pyproject.toml`)
- LibreOffice (optional, for PDF conversion)
