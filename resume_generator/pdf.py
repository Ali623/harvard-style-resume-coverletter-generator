"""PDF conversion. Uses Microsoft Word on Windows, LibreOffice elsewhere."""

import os
import subprocess
import shutil
import sys
from pathlib import Path


def _word_convert_script(docx: str, pdf: str) -> str:
    """Return a self-contained Python script that does Word COM conversion."""
    return f'''
import pythoncom, os, time
from win32com import client as win32

pythoncom.CoInitialize()
word = None
try:
    word = win32.gencache.EnsureDispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0
    word.AutomationSecurity = 1
    doc = word.Documents.Open(
        r"{docx}",
        ConfirmConversions=False,
        ReadOnly=True,
        AddToRecentFiles=False,
        NoEncodingDialog=True,
    )
    time.sleep(0.5)
    doc.ExportAsFixedFormat(
        r"{pdf}",
        ExportFormat=17,
        OpenAfterExport=False,
        OptimizeFor=0,
        Item=0,
        IncludeDocProps=True,
        CreateBookmarks=0,
    )
    doc.Close(SaveChanges=0)
finally:
    if word is not None:
        try:
            word.Quit()
        except Exception:
            pass
    pythoncom.CoUninitialize()
'''


def _convert_via_word(docx_path: str, pdf_path: str) -> None:
    """Windows: spawn a subprocess for Word COM (avoids Streamlit thread issues)."""
    abs_in = os.path.abspath(docx_path)
    abs_out = os.path.abspath(pdf_path)

    script = _word_convert_script(abs_in, abs_out)
    result = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Word conversion failed")


def _find_soffice() -> str | None:
    """Locate the LibreOffice soffice executable."""
    env = os.environ.get('SOFFICE_PATH')
    if env and os.path.isfile(env):
        return env

    if sys.platform == 'win32':
        candidates = [
            os.path.expandvars(r'%ProgramFiles%\LibreOffice\program\soffice.exe'),
            os.path.expandvars(r'%ProgramFiles(x86)%\LibreOffice\program\soffice.exe'),
        ]
    elif sys.platform == 'darwin':
        candidates = ['/Applications/LibreOffice.app/Contents/MacOS/soffice']
    else:
        candidates = ['/usr/bin/soffice', '/usr/local/bin/soffice', '/snap/bin/libreoffice']

    for path in candidates:
        if os.path.isfile(path):
            return path
    return shutil.which('soffice')


def _convert_via_libreoffice(docx_path: str, pdf_path: str) -> None:
    """Fallback: use LibreOffice headless."""
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError("LibreOffice not found.")
    outdir = str(Path(docx_path).parent)
    subprocess.run(
        [soffice, '--headless', '--convert-to', 'pdf', '--outdir', outdir, docx_path],
        check=True, capture_output=True, text=True, timeout=30,
    )


def convert_to_pdf(docx_path: str) -> str:
    """Convert a .docx file to .pdf. Returns the pdf path.

    Uses Microsoft Word on Windows (via subprocess), falls back to LibreOffice.
    """
    pdf_path = str(Path(docx_path).with_suffix('.pdf'))

    # 1. Windows: try Word via subprocess
    if sys.platform == 'win32':
        try:
            _convert_via_word(docx_path, pdf_path)
            return pdf_path
        except Exception:
            pass

    # 2. LibreOffice fallback
    try:
        _convert_via_libreoffice(docx_path, pdf_path)
        return pdf_path
    except Exception:
        pass

    raise RuntimeError(
        "PDF conversion failed. On Windows, install Microsoft Word. "
        "Otherwise, install LibreOffice: https://www.libreoffice.org/download/"
    )
