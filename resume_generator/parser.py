"""Parse AI-generated output into Resume and CoverLetter models.

Primary format: JSON. Falls back to free-form text parsing for legacy input.
"""

import json
import re
from dataclasses import dataclass

from resume_generator.models import Resume, CoverLetter, Education, Experience, Skill, Project


@dataclass
class ParsedOutput:
    resume: Resume
    cover: CoverLetter
    company: str = ""
    job_title: str = ""


def _clean_md(text: str) -> str:
    """Strip markdown link syntax: [text](url) → text, then clean URL prefixes."""
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = text.replace('https://', '').replace('http://', '').rstrip('/')
    return re.sub(r'^www\.', '', text)


def _parse_resume_json(data: dict) -> Resume:
    r = Resume()
    r.full_name = data.get('name', 'Aliullah')

    contact = data.get('contact', {})
    if contact:
        r.address = contact.get('location', r.address)
        r.phone = _clean_md(contact.get('phone', r.phone))
        r.email = _clean_md(contact.get('email', r.email))
        linkedin = _clean_md(contact.get('linkedin', ''))
        if linkedin:
            r.linkedin = linkedin
        github = _clean_md(contact.get('github', ''))
        if github:
            r.github = github

    summary = data.get('professional_summary', [])
    if isinstance(summary, list):
        r.summary = ' '.join(summary)
    elif isinstance(summary, str):
        r.summary = summary

    for edu in data.get('education', []):
        r.education.append(Education(
            uni=edu.get('institution', ''),
            location=edu.get('location', ''),
            degree=edu.get('degree', ''),
            grade=f", {edu['grade']}" if edu.get('grade') else '',
            dates=edu.get('dates', ''),
        ))

    for exp in data.get('experience', []):
        r.experience.append(Experience(
            company=exp.get('company', ''),
            location=exp.get('location', ''),
            role=exp.get('title', ''),
            dates=exp.get('dates', ''),
            bullets=exp.get('bullet_points', []),
        ))

    for comp in data.get('digital_competencies', []):
        label = comp.get('category', '') + ':'
        value = ', '.join(comp.get('skills', []))
        r.skills.append(Skill(label=label, value=value))

    r.certifications = data.get('certifications', [])

    for proj in data.get('projects', []):
        r.projects.append(Project(
            title=proj.get('name', '') + ': ',
            description=proj.get('description', ''),
        ))

    r.achievements = data.get('achievements', [])

    return r


def _parse_cover_json(data: dict) -> CoverLetter:
    c = CoverLetter()
    c.salutation = data.get('salutation', 'Dear Hiring Team,')
    c.paragraphs = data.get('paragraphs', [])
    sig = data.get('signature', '')
    if sig:
        c.signoff_name = sig

    # Carry over contact from resume if available (the caller merges)
    contact = data.get('contact', {})
    if contact:
        c.address = contact.get('location', c.address)
        c.phone = _clean_md(contact.get('phone', c.phone))
        c.email = _clean_md(contact.get('email', c.email))
        linkedin = _clean_md(contact.get('linkedin', ''))
        if linkedin:
            c.linkedin = linkedin
        github = _clean_md(contact.get('github', ''))
        if github:
            c.github = github

    return c


def parse_ai_output(text: str) -> ParsedOutput:
    """Parse AI output (JSON preferred, free-text fallback) into models."""
    text = text.strip()

    # ── Try JSON first ──
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                data = json.loads(m.group(0))
            except json.JSONDecodeError:
                r, c = _parse_text(text)
                return ParsedOutput(resume=r, cover=c)
        else:
            r, c = _parse_text(text)
            return ParsedOutput(resume=r, cover=c)

    # Extract job-level metadata
    job_details = data.get('job_details', {})
    company = job_details.get('company', '')
    job_title = job_details.get('job_title', '')

    # Extract the two top-level sections
    resume_data = data.get('tailored_resume', data)
    cover_data = data.get('cover_letter', {})

    resume = _parse_resume_json(resume_data)

    # Merge resume contact into cover if cover doesn't have its own
    if 'contact' not in cover_data:
        cover_data['contact'] = resume_data.get('contact', {})

    cover = _parse_cover_json(cover_data)

    # Copy contact from resume to cover
    for attr in ('address', 'phone', 'email', 'linkedin', 'github', 'portfolio',
                 'full_name'):
        rv = getattr(resume, attr)
        cv = getattr(cover, attr)
        if not cv or cv == getattr(CoverLetter(), attr):
            setattr(cover, attr, rv)

    return ParsedOutput(resume=resume, cover=cover, company=company, job_title=job_title)


# ─── Legacy free-text parser (fallback) ─────────────────────────────────────

def _parse_text(text: str) -> ParsedOutput:
    """Fallback: parse free-form text with section markers."""
    resume = Resume()
    cover = CoverLetter()

    resume_m = re.search(r'(?:\d+\.?\s*)?Tailored\s+Resume\b', text, re.IGNORECASE)
    cover_m = re.search(r'(?:\d+\.?\s*)?Tailored\s+Cover\s+Letter\b', text, re.IGNORECASE)

    resume_text = ""
    cover_text = ""

    if resume_m:
        start = resume_m.end()
        end = cover_m.start() if cover_m else len(text)
        resume_text = text[start:end].strip()
    else:
        resume_text = text.strip()

    if cover_m:
        start = cover_m.end()
        next_sec = re.search(r'\n\d+\.\s+', text[start:])
        end = start + next_sec.start() if next_sec else len(text)
        cover_text = text[start:end].strip()

    if resume_text:
        _parse_resume_text(resume_text, resume)
    if cover_text:
        _parse_cover_text(cover_text, cover)

    return ParsedOutput(resume=resume, cover=cover)


# ─── Legacy text parsing helpers (kept for backward compatibility) ───────────

def _parse_resume_text(text: str, resume: Resume) -> None:
    lines = text.strip().split('\n')
    section_headers = ['professional summary', 'education', 'experience',
                       'digital competencies', 'certifications', 'projects',
                       'achievements', 'skills']
    contact_lines = []
    for line in lines:
        stripped = line.strip().lower().rstrip(':')
        if any(stripped == h for h in section_headers):
            break
        contact_lines.append(line.strip())

    if contact_lines:
        name_idx = 0
        for i, cl in enumerate(contact_lines):
            if cl:
                resume.full_name = cl
                name_idx = i
                break
        remaining = contact_lines[name_idx + 1:]
        for cl in remaining:
            if not cl:
                continue
            if '@' in cl and '.' in cl:
                resume.email = cl
            elif cl.startswith('+') or cl.startswith('0'):
                resume.phone = cl
            elif 'linkedin.com' in cl.lower():
                m = re.search(r'linkedin\.com/in/[\w-]+', cl, re.IGNORECASE)
                if m:
                    resume.linkedin = m.group(0)
            elif 'github.com' in cl.lower():
                m = re.search(r'github\.com/[\w.-]+', cl, re.IGNORECASE)
                if m:
                    resume.github = m.group(0)
            else:
                resume.address = cl

    sections = _split_into_sections(text, section_headers)
    for heading, content in sections.items():
        h = heading.lower().rstrip(':')
        if h == 'professional summary':
            resume.summary = ' '.join(content.strip().split('\n')).strip()
        elif h == 'education':
            resume.education = _parse_education_text(content)
        elif h == 'experience':
            resume.experience = _parse_experience_text(content)
        elif h in ('digital competencies', 'skills'):
            resume.skills = _parse_skills_text(content)
        elif h == 'certifications':
            resume.certifications = _parse_list_text(content)
        elif h == 'projects':
            resume.projects = _parse_projects_text(content)
        elif h == 'achievements':
            resume.achievements = _parse_list_text(content)


def _parse_cover_text(text: str, cover: CoverLetter) -> None:
    lines = text.strip().split('\n')
    clean = [l.strip() for l in lines if l.strip()]
    if not clean:
        return

    for i, line in enumerate(clean):
        if line.lower().startswith('dear '):
            cover.salutation = line.rstrip(',') + ','
            clean = clean[i + 1:]
            break

    signoff_idx = len(clean)
    for pat in ['sincerely', 'best regards', 'yours faithfully', 'yours truly',
                'kind regards', 'warm regards']:
        for i, line in enumerate(clean):
            if line.lower().rstrip(',') == pat:
                signoff_idx = i
                break
        if signoff_idx < len(clean):
            break

    body_lines = clean[:signoff_idx]
    signoff_lines = clean[signoff_idx:]

    # Split body on blank lines in original text
    raw_paras = re.split(r'\n\s*\n', text.strip())
    # Filter to only body paragraphs (between salutation and sign-off)
    body_text_start = text.find(clean[0]) if clean else 0
    signoff_start = text.find(signoff_lines[0]) if signoff_lines else len(text)
    body_raw = text[body_text_start:signoff_start]
    raw_paras = re.split(r'\n\s*\n', body_raw.strip())
    cover.paragraphs = [' '.join(p.strip().split('\n')) for p in raw_paras if p.strip()]

    if signoff_lines and len(signoff_lines) >= 2:
        cover.signoff_name = signoff_lines[1].strip()
    for sl in signoff_lines[2:]:
        if '@' in sl:
            cover.signoff_email = sl.strip()
        elif sl.strip().startswith('+'):
            cover.signoff_phone = sl.strip()


# ─── Legacy section parsers ─────────────────────────────────────────────────

def _split_into_sections(text: str, headers: list[str]) -> dict[str, str]:
    escaped = [re.escape(h) for h in headers]
    pattern = r'(?i)(?:(?<=\n)|(?<=^))\s*(' + '|'.join(escaped) + r')\s*:?\s*\n'
    parts = re.split(pattern, text)
    result = {}
    i = 0
    while i < len(parts):
        chunk = parts[i].strip()
        if chunk.lower().rstrip(':') in headers:
            result[chunk] = parts[i + 1] if i + 1 < len(parts) else ""
            i += 2
        else:
            i += 1
    return result


def _parse_education_text(text: str) -> list[Education]:
    entries = []
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    i = 0
    while i < len(lines):
        edu = Education()
        line0 = lines[i]
        if '|' in line0:
            parts = line0.rsplit('|', 1)
            edu.uni = parts[0].strip()
            edu.location = parts[1].strip()
        else:
            edu.uni = line0
        i += 1
        if i < len(lines):
            line1 = lines[i]
            if '|' in line1:
                parts = line1.rsplit('|', 1)
                left = parts[0].strip()
                edu.dates = parts[1].strip()
                grade_m = re.search(r'(,\s*(?:Grade|Note)\s*[\d.]+.*)', left, re.IGNORECASE)
                if grade_m:
                    edu.grade = grade_m.group(1)
                    edu.degree = left[:grade_m.start()].strip()
                else:
                    edu.degree = left
            else:
                edu.degree = line1
            i += 1
        entries.append(edu)
        if i < len(lines) and any(h in lines[i].lower()
            for h in ['experience', 'digital competencies', 'professional']):
            break
    return entries


def _parse_experience_text(text: str) -> list[Experience]:
    entries = []
    current = None
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        lower = line.lower().rstrip(':')
        if lower in ('digital competencies', 'certifications', 'projects',
                      'achievements', 'skills', 'professional summary'):
            break
        if '|' in line and not line.startswith(('-', '•', '*')):
            parts = [p.strip() for p in line.split('|')]
            if current is not None and current.company and not current.role:
                current.role = parts[0]
                if len(parts) >= 2:
                    current.dates = parts[1]
            else:
                if current is not None and current.bullets:
                    entries.append(current)
                current = Experience(company="", location="", role="", dates="")
                current.company = parts[0]
                if len(parts) >= 2:
                    current.location = parts[1]
                if len(parts) >= 3:
                    current.dates = parts[2]
        elif line.startswith(('-', '•', '*')):
            if current is not None:
                current.bullets.append(line.lstrip('-•* ').strip())
    if current is not None and (current.company or current.bullets):
        entries.append(current)
    return entries


def _parse_skills_text(text: str) -> list[Skill]:
    skills = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label, value = line.split(':', 1)
            skills.append(Skill(label=label.strip() + ':', value=value.strip()))
        elif skills:
            skills[-1].value += ', ' + line
        else:
            skills.append(Skill(label="", value=line))
    return skills


def _parse_list_text(text: str) -> list[str]:
    items = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^[\-\•\*\d+\.]\s*', '', line)
        if line:
            items.append(line)
    return items


def _parse_projects_text(text: str) -> list[Project]:
    projects = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        line = re.sub(r'^[\-\•\*\d+\.]\s*', '', line)
        if ':' in line:
            title, desc = line.split(':', 1)
            projects.append(Project(title=title.strip() + ': ', description=desc.strip()))
        else:
            projects.append(Project(title=line, description=""))
    return projects
