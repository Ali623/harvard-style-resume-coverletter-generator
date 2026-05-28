"""Streamlit UI for resume + cover letter generation from AI job-analysis output.

Usage:
    streamlit run app.py
"""

import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

from resume_generator.models import (
    Resume, CoverLetter, Education, Experience, Skill, Project,
    DEFAULT_RESUME, DEFAULT_COVER,
)
from resume_generator.builder import build_resume, build_coverletter
from resume_generator.parser import parse_ai_output
from resume_generator.pdf import convert_to_pdf
from resume_generator.persist import save_state, load_state, dict_to_resume, dict_to_cover

st.set_page_config(page_title="Resume & Cover Letter Generator", layout="wide")
st.title("Resume & Cover Letter Generator")

# ─── Session State ───────────────────────────────────────────────────────────

for key, default in [
    ("resume", DEFAULT_RESUME),
    ("cover", DEFAULT_COVER),
    ("parsed", False),
    ("generated", False),
    ("output_dir", ""),
    ("_company", ""),
    ("_job_title", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Auto-restore previous session
if not st.session_state.parsed:
    saved = load_state()
    if saved:
        try:
            st.session_state.resume = dict_to_resume(saved["resume"])
            st.session_state.cover = dict_to_cover(saved["cover"])
            if saved.get("company"):
                st.session_state._company = saved["company"]
            if saved.get("job_title"):
                st.session_state._job_title = saved["job_title"]
            st.session_state.parsed = True
        except Exception:
            pass


def _set_company(val: str):
    """Safely set company backing key, resetting widget so value= takes effect."""
    st.session_state._company = val
    st.session_state.pop("cfg_company", None)

def _set_job_title(val: str):
    st.session_state._job_title = val
    st.session_state.pop("cfg_role", None)

# ─── PDF Preview ────────────────────────────────────────────────────────────

def _get_file_server():
    """Start or return a lightweight HTTP file server for the output directory."""
    import threading
    import http.server

    if "_file_server" not in st.session_state:
        st.session_state._file_server = None
        st.session_state._file_server_port = None

    if st.session_state._file_server is not None:
        return st.session_state._file_server_port

    # Find a free port and start serving the parent of the output dir
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    import functools
    # Serve from filesystem root so any save directory is reachable
    root = "C:\\" if os.name == "nt" else "/"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    st.session_state._file_server = server
    st.session_state._file_server_port = port
    return port


def _pdf_link(filepath: str, label: str) -> None:
    """Show a link to open a PDF in a new browser tab."""
    if not os.path.isfile(filepath):
        st.warning(f"PDF not ready: {os.path.basename(filepath)}")
        return
    port = _get_file_server()
    # Server root is C:\ so path is everything after the drive letter
    abs_path = os.path.abspath(filepath).replace("\\", "/")
    if abs_path[1:3] == ":/":
        abs_path = abs_path[2:]  # strip "C:" prefix
    url = f"http://127.0.0.1:{port}{abs_path}"
    st.markdown(
        f'<a href="{url}" target="_blank" style="display:inline-block;padding:6px 16px;'
        f'background:#4CAF50;color:#fff;border-radius:4px;text-decoration:none;margin:4px;">'
        f'Open {label} in new tab</a>',
        unsafe_allow_html=True,
    )


# ─── Sidebar: Input Method ───────────────────────────────────────────────────

st.sidebar.header("Configuration")

st.sidebar.subheader("Output naming")
company = st.sidebar.text_input("Company",
                                value=st.session_state._company,
                                key="cfg_company",
                                help="Auto-filled from parsed JSON or AI Generate.")
role = st.sidebar.text_input("Job Title",
                              value=st.session_state._job_title,
                              key="cfg_role",
                              help="Auto-filled from parsed JSON or AI Generate.")

st.sidebar.subheader("Save location")
default_dir = r"C:\Users\HP\OneDrive\resume\Harverd resume\full_time"
save_dir = st.sidebar.text_input("Output directory", value=default_dir, key="save_dir")
if not save_dir:
    save_dir = tempfile.gettempdir()

st.sidebar.caption("Files: Aliullah-Resume.docx / Aliullah-CoverLetter.docx")

st.sidebar.subheader("Input method")
input_method = st.sidebar.radio(
    "Choose how to provide content:",
    ["Paste AI Output", "AI Generate", "Scrape Jobs", "Manual Entry"],
    help="Paste pre-generated JSON, generate via DeepSeek API, scrape job boards, or fill in fields manually.",
)

st.sidebar.divider()
if st.sidebar.button("New / Reset", type="secondary", use_container_width=True):
    for key in ["resume", "cover", "parsed", "generated", "output_dir", "cfg_company", "cfg_role", "_company", "_job_title", "save_dir", "scraped_jobs"]:
        if key in st.session_state:
            del st.session_state[key]
    from resume_generator.persist import STATE_FILE
    if STATE_FILE.is_file():
        STATE_FILE.unlink()
    st.rerun()

# ─── AI Output Parsing ───────────────────────────────────────────────────────

if input_method == "Paste AI Output":
    st.header("Step 1: Paste AI-Generated Content")
    st.caption("Paste the JSON output from your AI tool. Free-form text with section markers is also supported as fallback.")

    ai_text = st.text_area(
        "AI Output",
        height=400,
        placeholder='Paste JSON here: {"tailored_resume": {...}, "cover_letter": {...}}',
        key="ai_text",
    )

    if st.button("Parse Content", type="primary"):
        if ai_text.strip():
            with st.spinner("Parsing..."):
                try:
                    parsed = parse_ai_output(ai_text)
                    st.session_state.resume = parsed.resume
                    st.session_state.cover = parsed.cover
                    if parsed.company:
                        _set_company(parsed.company)
                    if parsed.job_title:
                        _set_job_title(parsed.job_title)
                    st.session_state.parsed = True
                    st.session_state.generated = False
                    save_state(parsed.resume, parsed.cover,
                               st.session_state.get("_company", ""),
                               st.session_state.get("_job_title", ""))
                    st.success("Parsed successfully! Review and edit below, then generate.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Parsing error: {e}")
        else:
            st.warning("Please paste some content first.")

elif input_method == "AI Generate":
    st.header("Step 1: Enter Job Details")
    st.caption("Fill in the job details below. The app will generate a tailored resume and cover letter using DeepSeek AI.")

    col1, col2 = st.columns(2)
    with col1:
        ai_job_title = st.text_input("Job Title", placeholder="Machine Learning Software Engineer", key="ai_job_title")
        ai_company = st.text_input("Company", placeholder="Applied Intuition", key="ai_company")
    with col2:
        ai_location = st.text_input("Location", placeholder="Germany", key="ai_location")

    ai_job_desc = st.text_area(
        "Job Description",
        height=250,
        placeholder="Paste the full job description here...",
        key="ai_job_desc",
    )

    if st.button("Generate with AI", type="primary"):
        if not ai_job_title or not ai_job_desc:
            st.warning("Please provide at least the Job Title and Job Description.")
        else:
            with st.spinner("Calling DeepSeek API... This may take up to 60 seconds."):
                try:
                    from resume_generator.deepseek import build_prompt, generate as ai_generate
                    prompt = build_prompt(ai_job_title, ai_company, ai_location, ai_job_desc)
                    raw = ai_generate(prompt)
                    parsed = parse_ai_output(raw)

                    st.session_state.resume = parsed.resume
                    st.session_state.cover = parsed.cover
                    _set_company(parsed.company or ai_company)
                    _set_job_title(parsed.job_title or ai_job_title)

                    st.session_state.parsed = True
                    st.session_state.generated = False
                    save_state(parsed.resume, parsed.cover,
                               st.session_state.get("_company", ""),
                               st.session_state.get("_job_title", ""))
                    st.success("AI generation complete! Review and edit below, then generate documents.")
                    st.rerun()
                except Exception as e:
                    st.error(f"AI generation failed: {e}")
                    st.info("Make sure you have a valid DEEPSEEK_API_KEY in your .env file.")

elif input_method == "Scrape Jobs":
    st.header("Step 1: Search Job Boards")
    st.caption("Search LinkedIn, XING, and StepStone for jobs. Results appear in a table with one-click generation buttons.")

    # Init scraper session state
    if "scraped_jobs" not in st.session_state:
        st.session_state.scraped_jobs = []

    col1, col2, col3 = st.columns(3)
    with col1:
        scraper_title = st.text_input("Job Title", placeholder="Machine Learning Engineer", key="scr_title")
        scraper_location = st.text_input("Location", placeholder="Germany", key="scr_loc")
    with col2:
        scraper_hours = st.selectbox("Posted within", [24, 72, 168, 720], format_func=lambda h: f"Past {h}h" if h < 168 else f"Past {h//24}d" if h < 720 else "Past 30d", key="scr_hours")
        scraper_count = st.number_input("Jobs per board", 3, 25, 10, key="scr_count",
                                         help="Number of jobs to fetch from each selected job board.")
    with col3:
        scraper_boards = st.multiselect("Job Boards", ["LinkedIn", "XING", "StepStone"], default=["LinkedIn", "XING", "StepStone"], key="scr_boards")

    if st.button("Search Jobs", type="primary", key="scr_btn"):
        if not scraper_title or not scraper_boards:
            st.warning("Please provide a job title and select at least one job board.")
        else:
            with st.spinner(f"Scraping {', '.join(scraper_boards)}... This may take a minute."):
                try:
                    from resume_generator.scraper import scrape_jobs
                    jobs = scrape_jobs(scraper_title, scraper_location, scraper_hours, scraper_count, scraper_boards)
                    st.session_state.scraped_jobs = jobs
                    st.success(f"Found {len(jobs)} jobs!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Scraping failed: {e}")
                    st.info("Make sure Playwright is installed (pip install playwright && playwright install chromium).")

    # Show results table
    jobs = st.session_state.scraped_jobs
    if jobs:
        st.header(f"Results ({len(jobs)} jobs)")
        for i, job in enumerate(jobs, 1):
            desc_preview = (job.description[:300] + "...") if len(job.description) > 300 else job.description
            with st.expander(f"{i}. {job.title} — {job.company} ({job.job_board})", expanded=(i == 1)):
                cols = st.columns([2, 1, 1, 1])
                cols[0].markdown(f"**Location:** {job.location or 'N/A'}")
                cols[1].markdown(f"**Posted:** {job.date_posted or 'N/A'}")
                if job.job_link:
                    cols[2].markdown(f"[Open Job]({job.job_link})", unsafe_allow_html=True)

                if job.description:
                    st.text_area("Job Description", job.description, height=150, key=f"scr_desc_{i}", disabled=True)

                if st.button(f"Generate Resume & Cover Letter for this job", key=f"scr_gen_{i}"):
                    with st.spinner("Calling DeepSeek API..."):
                        try:
                            from resume_generator.deepseek import build_prompt, generate as ai_generate
                            prompt = build_prompt(job.title, job.company, job.location, job.description)
                            raw = ai_generate(prompt)
                            parsed = parse_ai_output(raw)

                            st.session_state.resume = parsed.resume
                            st.session_state.cover = parsed.cover
                            gen_company = parsed.company or job.company
                            gen_role = parsed.job_title or job.title
                            _set_company(gen_company)
                            _set_job_title(gen_role)
                            st.session_state.resume = parsed.resume
                            st.session_state.cover = parsed.cover
                            st.session_state.parsed = True
                            st.session_state.generated = False

                            # Generate docs immediately
                            import shutil
                            slug = lambda s: ''.join(c for c in s if c.isalnum() or c == '-').rstrip()
                            folder_name = f"Aliullah-{slug(gen_company)}-{slug(gen_role)}"
                            save_dir_val = st.session_state.get("save_dir", tempfile.gettempdir())
                            if not save_dir_val:
                                save_dir_val = tempfile.gettempdir()
                            output_dir = os.path.join(save_dir_val, folder_name)
                            if os.path.isdir(output_dir):
                                shutil.rmtree(output_dir)
                            os.makedirs(output_dir, exist_ok=True)

                            resume_path = build_resume(parsed.resume, output_dir, company=gen_company, job_title=gen_role)
                            cover_path = build_coverletter(parsed.cover, output_dir, company=gen_company, job_title=gen_role)
                            try:
                                convert_to_pdf(resume_path)
                                convert_to_pdf(cover_path)
                            except Exception:
                                pass

                            save_state(parsed.resume, parsed.cover, gen_company, gen_role)
                            st.session_state.output_dir = output_dir
                            st.session_state.generated = True
                            st.success(f"Saved to `{output_dir}`")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Generation failed: {e}")

else:
    st.session_state.parsed = True
    st.session_state.generated = False

# ─── Editable Preview ────────────────────────────────────────────────────────

if st.session_state.parsed:
    st.header("Step 2: Review & Edit Content")
    tab1, tab2 = st.tabs(["Resume", "Cover Letter"])

    with tab1:
        r = st.session_state.resume

        st.subheader("Contact Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            r.full_name = st.text_input("Full Name", r.full_name, key="r_name")
            r.email = st.text_input("Email", r.email, key="r_email")
            r.linkedin = st.text_input("LinkedIn", r.linkedin, key="r_linkedin")
        with col2:
            r.phone = st.text_input("Phone", r.phone, key="r_phone")
            r.github = st.text_input("GitHub", r.github, key="r_github")
        with col3:
            r.address = st.text_input("Address", r.address, key="r_address")
            r.portfolio = st.text_input("Portfolio", r.portfolio, key="r_portfolio")

        st.subheader("Professional Summary")
        r.summary = st.text_area("Summary", r.summary, height=80, key="r_summary")

        st.subheader("Education")
        edu_count = st.number_input("Entries", 0, 10, len(r.education), key="edu_n")
        while len(r.education) < edu_count:
            r.education.append(Education())
        r.education = r.education[:edu_count]
        for i, edu in enumerate(r.education):
            cols = st.columns([3, 2, 3, 2, 2])
            edu.uni = cols[0].text_input("University", edu.uni, key=f"edu_uni_{i}")
            edu.location = cols[1].text_input("Location", edu.location, key=f"edu_loc_{i}")
            edu.degree = cols[2].text_input("Degree", edu.degree, key=f"edu_deg_{i}")
            edu.grade = cols[3].text_input("Grade", edu.grade, key=f"edu_grade_{i}")
            edu.dates = cols[4].text_input("Dates", edu.dates, key=f"edu_dates_{i}")

        st.subheader("Experience")
        exp_count = st.number_input("Entries", 0, 10, len(r.experience), key="exp_n")
        while len(r.experience) < exp_count:
            r.experience.append(Experience(company="", location="", role="", dates=""))
        r.experience = r.experience[:exp_count]
        for i, exp in enumerate(r.experience):
            with st.expander(f"{exp.company or f'Experience {i+1}'}", expanded=(i == 0)):
                cols = st.columns([3, 2, 3, 2])
                exp.company = cols[0].text_input("Company", exp.company, key=f"exp_co_{i}")
                exp.location = cols[1].text_input("Location", exp.location, key=f"exp_loc_{i}")
                exp.role = cols[2].text_input("Role", exp.role, key=f"exp_role_{i}")
                exp.dates = cols[3].text_input("Dates", exp.dates, key=f"exp_dates_{i}")

                bl_text = "\n".join(exp.bullets)
                new_bl = st.text_area("Bullets (one per line)", bl_text, height=120, key=f"exp_bl_{i}")
                exp.bullets = [b.strip() for b in new_bl.split("\n") if b.strip()]

        st.subheader("Digital Competencies")
        sk_count = st.number_input("Skill rows", 0, 15, len(r.skills), key="sk_n")
        while len(r.skills) < sk_count:
            r.skills.append(Skill("", ""))
        r.skills = r.skills[:sk_count]
        for i, sk in enumerate(r.skills):
            cols = st.columns([1, 3])
            sk.label = cols[0].text_input("Label", sk.label, key=f"sk_label_{i}")
            sk.value = cols[1].text_input("Value", sk.value, key=f"sk_value_{i}")

        st.subheader("Certifications")
        cert_text = "\n".join(r.certifications)
        new_cert = st.text_area("One per line", cert_text, height=80, key="r_certs")
        r.certifications = [c.strip() for c in new_cert.split("\n") if c.strip()]

        st.subheader("Projects")
        proj_count = st.number_input("Entries", 0, 10, len(r.projects), key="proj_n")
        while len(r.projects) < proj_count:
            r.projects.append(Project("", ""))
        r.projects = r.projects[:proj_count]
        for i, proj in enumerate(r.projects):
            cols = st.columns([1, 2])
            proj.title = cols[0].text_input("Title", proj.title, key=f"proj_t_{i}")
            proj.description = cols[1].text_input("Description", proj.description, key=f"proj_d_{i}")

        st.subheader("Achievements")
        ach_text = "\n".join(r.achievements)
        new_ach = st.text_area("One per line", ach_text, height=80, key="r_ach")
        r.achievements = [a.strip() for a in new_ach.split("\n") if a.strip()]

    with tab2:
        c = st.session_state.cover

        st.subheader("Contact (shared with resume)")
        col1, col2, col3 = st.columns(3)
        with col1:
            c.full_name = st.text_input("Full Name", c.full_name, key="c_name")
            c.email = st.text_input("Email", c.email, key="c_email")
            c.linkedin = st.text_input("LinkedIn", c.linkedin, key="c_linkedin")
        with col2:
            c.phone = st.text_input("Phone", c.phone, key="c_phone")
            c.github = st.text_input("GitHub", c.github, key="c_github")
        with col3:
            c.address = st.text_input("Address", c.address, key="c_address")
            c.portfolio = st.text_input("Portfolio", c.portfolio, key="c_portfolio")

        st.subheader("Recipient")
        col1, col2 = st.columns(2)
        c.recipient_name = col1.text_input("Recipient Name", c.recipient_name, key="c_recip")
        c.recipient_city = col2.text_input("Recipient City", c.recipient_city, key="c_city")
        c.salutation = st.text_input("Salutation", c.salutation, key="c_sal")

        st.subheader("Body Paragraphs")
        para_count = st.number_input("Paragraphs", 1, 8, len(c.paragraphs) or 3, key="c_para_n")
        while len(c.paragraphs) < para_count:
            c.paragraphs.append("")
        c.paragraphs = c.paragraphs[:para_count]
        for i, para in enumerate(c.paragraphs):
            c.paragraphs[i] = st.text_area(
                f"Paragraph {i+1}", para, height=100, key=f"c_para_{i}"
            )

        st.subheader("Sign-off")
        col1, col2 = st.columns(2)
        c.signoff_name = col1.text_input("Name", c.signoff_name, key="c_sign_name")
        c.signoff_email = col2.text_input("Email", c.signoff_email, key="c_sign_email")
        c.signoff_phone = st.text_input("Phone", c.signoff_phone, key="c_sign_phone")

    # ─── Generate Button ─────────────────────────────────────────────────────

    st.header("Step 3: Generate Documents")
    if st.button("Generate .docx & .pdf", type="primary"):
        with st.spinner("Generating documents..."):
            try:
                slug = lambda s: ''.join(c for c in s if c.isalnum() or c == '-').rstrip()
                c_slug = slug(company) if company else "Company"
                r_slug = slug(role) if role else "Role"
                import shutil
                folder_name = f"Aliullah-{c_slug}-{r_slug}"
                output_dir = os.path.join(save_dir, folder_name)
                if os.path.isdir(output_dir):
                    shutil.rmtree(output_dir)
                os.makedirs(output_dir, exist_ok=True)

                resume_path = build_resume(st.session_state.resume, output_dir,
                                           company=company, job_title=role)
                cover_path = build_coverletter(st.session_state.cover, output_dir,
                                               company=company, job_title=role)

                resume_pdf = None
                cover_pdf = None
                try:
                    resume_pdf = convert_to_pdf(resume_path)
                    cover_pdf = convert_to_pdf(cover_path)
                except Exception as pdf_err:
                    st.warning(f"PDF conversion skipped: {pdf_err}")

                st.session_state.output_dir = output_dir
                st.session_state.generated = True
                save_state(st.session_state.resume, st.session_state.cover,
                           st.session_state.get("_company", ""),
                           st.session_state.get("_job_title", ""))
                st.success(f"Documents generated in: `{output_dir}`")
                st.rerun()
            except Exception as e:
                st.error(f"Generation failed: {e}")

    # ─── Preview & Download ──────────────────────────────────────────────────

    if st.session_state.generated and st.session_state.output_dir:
        d = st.session_state.output_dir
        r = st.session_state.resume
        c = st.session_state.cover

        st.header("Step 4: Preview & Download")
        prev_tab1, prev_tab2 = st.tabs(["Resume Preview", "Cover Letter Preview"])

        with prev_tab1:
            files = os.listdir(d) if os.path.isdir(d) else []
            resume_pdfs = [f for f in files if f.endswith('.pdf') and 'Resume' in f]
            if resume_pdfs:
                for f in sorted(resume_pdfs):
                    _pdf_link(os.path.join(d, f), f)
            else:
                st.info("PDF not generated. Download the .docx below.")

        with prev_tab2:
            files = os.listdir(d) if os.path.isdir(d) else []
            cover_pdfs = [f for f in files if f.endswith('.pdf') and 'CoverLetter' in f]
            if cover_pdfs:
                for f in sorted(cover_pdfs):
                    _pdf_link(os.path.join(d, f), f)
            else:
                st.info("PDF not generated. Download the .docx below.")

        st.subheader("Downloads")
        files = os.listdir(d) if os.path.isdir(d) else []
        col1, col2, col3, col4 = st.columns(4)

        for f in sorted(files):
            fpath = os.path.join(d, f)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as fh:
                    ext = f.split('.')[-1]
                    label = f"Download {f}"
                    if ext == "docx":
                        col1.download_button(label, fh, file_name=f, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    elif ext == "pdf":
                        col2.download_button(label, fh, file_name=f, mime="application/pdf")

        if files:
            zip_path = os.path.join(d, "documents.zip")
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for f in files:
                    fpath = os.path.join(d, f)
                    if f != "documents.zip":
                        zf.write(fpath, f)
            with open(zip_path, "rb") as zh:
                col3.download_button("Download All (ZIP)", zh, file_name="documents.zip", mime="application/zip")

elif not st.session_state.parsed:
    if input_method == "Paste AI Output":
        st.info("Paste JSON output and click 'Parse Content' to begin.")
    elif input_method == "AI Generate":
        st.info("Fill in job details and click 'Generate with AI' to begin.")
    elif input_method == "Scrape Jobs":
        st.info("Enter search criteria and click 'Search Jobs' to begin.")
    else:
        st.info("Edit the fields below directly, then click 'Generate .docx & .pdf'.")
