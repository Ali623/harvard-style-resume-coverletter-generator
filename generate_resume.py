"""CLI entry point for resume generation.

Usage:
    python generate_resume.py --company "Bending Spoons" --role "Graduate AI Software Engineer"
    python generate_resume.py   # uses defaults
"""

import argparse
import os

from resume_generator.models import DEFAULT_RESUME
from resume_generator.builder import build_resume
from resume_generator.pdf import convert_to_pdf

parser = argparse.ArgumentParser()
parser.add_argument('--company', default='Company')
parser.add_argument('--job-title', default='Role')
args = parser.parse_args()

slug = lambda s: ''.join(c for c in s if c.isalnum() or c == '-').rstrip()
folder = f"{slug(args.company)}-{slug(args.job_title)}"
os.makedirs(folder, exist_ok=True)

docx_path = build_resume(DEFAULT_RESUME, output_dir=folder,
                         company=args.company, job_title=args.job_title)
try:
    pdf_path = convert_to_pdf(docx_path)
    print(f'Written: {pdf_path}')
except Exception as e:
    print(f'PDF conversion failed: {e}')
    print('Make sure LibreOffice is installed.')
