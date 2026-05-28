"""DeepSeek API client for AI-powered resume/cover letter generation."""

import json
import os
from pathlib import Path

import requests

# Load .env file
def _load_dotenv():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and val and key not in os.environ:
                os.environ[key] = val

_load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def load_bank(filename: str) -> str:
    """Load a bank file from the banks/ directory."""
    path = Path(__file__).parent.parent / "banks" / filename
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


def build_prompt(job_title: str, company: str, location: str, job_description: str) -> str:
    """Build the full prompt by substituting placeholders."""
    template = load_bank("prompt.txt")
    cv = load_bank("cv.txt")
    cert_bank = load_bank("certifications.txt")
    proj_bank = load_bank("projects.txt")

    return (template
            .replace("{JOB_TITLE}", job_title)
            .replace("{COMPANY}", company)
            .replace("{LOCATION}", location)
            .replace("{JOB_DESCRIPTION}", job_description)
            .replace("{CURRENT_CV}", cv)
            .replace("{CERTIFICATION_BANK}", cert_bank)
            .replace("{PROJECT_BANK}", proj_bank))


def generate(prompt: str) -> str:
    """Send prompt to DeepSeek API and return the raw JSON response text."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not found. Create a .env file in the project root "
            "with: DEEPSEEK_API_KEY=sk-..."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
