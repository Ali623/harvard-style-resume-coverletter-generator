"""Save/load Resume and CoverLetter to JSON for session persistence."""

import json
from dataclasses import asdict
from pathlib import Path
from resume_generator.models import Resume, CoverLetter, Education, Experience, Skill, Project

STATE_FILE = Path(__file__).parent.parent / ".session_state.json"


def save_state(resume: Resume, cover: CoverLetter, company: str = "", job_title: str = "") -> None:
    """Persist current state to disk."""
    data = {
        "resume": asdict(resume),
        "cover": asdict(cover),
        "company": company,
        "job_title": job_title,
    }
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_state() -> dict | None:
    """Load persisted state, or None if not found."""
    if not STATE_FILE.is_file():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def dict_to_resume(d: dict) -> Resume:
    """Reconstruct Resume from dict."""
    r = Resume(
        full_name=d.get("full_name", "Aliullah"),
        address=d.get("address", ""),
        phone=d.get("phone", ""),
        email=d.get("email", ""),
        linkedin=d.get("linkedin", ""),
        github=d.get("github", ""),
        portfolio=d.get("portfolio", ""),
        summary=d.get("summary", ""),
        certifications=d.get("certifications", []),
        achievements=d.get("achievements", []),
    )
    for edu in d.get("education", []):
        r.education.append(Education(**edu))
    for exp in d.get("experience", []):
        exp["role"] = exp.pop("role", exp.get("title", ""))
        exp["bullets"] = exp.pop("bullets", exp.pop("bullet_points", []))
        r.experience.append(Experience(**{k: v for k, v in exp.items() if k in Experience.__dataclass_fields__}))
    for sk in d.get("skills", []):
        r.skills.append(Skill(**sk))
    for proj in d.get("projects", []):
        r.projects.append(Project(**proj))
    return r


def dict_to_cover(d: dict) -> CoverLetter:
    """Reconstruct CoverLetter from dict."""
    c = CoverLetter(
        full_name=d.get("full_name", "Aliullah"),
        address=d.get("address", ""),
        phone=d.get("phone", ""),
        email=d.get("email", ""),
        linkedin=d.get("linkedin", ""),
        github=d.get("github", ""),
        portfolio=d.get("portfolio", ""),
        recipient_name=d.get("recipient_name", ""),
        recipient_city=d.get("recipient_city", ""),
        salutation=d.get("salutation", "Dear Hiring Team,"),
        paragraphs=d.get("paragraphs", []),
        signoff_name=d.get("signoff_name", "Aliullah"),
        signoff_email=d.get("signoff_email", ""),
        signoff_phone=d.get("signoff_phone", ""),
    )
    return c
