"""Data models for resume and cover letter content."""

from dataclasses import dataclass, field


@dataclass
class Education:
    uni: str
    location: str
    degree: str
    grade: str = ""
    dates: str = ""


@dataclass
class Experience:
    company: str
    location: str
    role: str
    dates: str
    bullets: list[str] = field(default_factory=list)


@dataclass
class Skill:
    label: str
    value: str


@dataclass
class Project:
    title: str
    description: str


@dataclass
class Resume:
    full_name: str = "Your Name"
    address: str = ""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    summary: str = ""
    education: list[Education] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)


@dataclass
class CoverLetter:
    full_name: str = "Your Name"
    address: str = ""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    recipient_name: str = ""
    recipient_city: str = ""
    salutation: str = "Dear Hiring Team,"
    paragraphs: list[str] = field(default_factory=list)
    signoff_name: str = "Your Name"
    signoff_email: str = ""
    signoff_phone: str = ""


# ─── DEFAULT CONTENT (backward-compatible with the old hardcoded data) ──────

DEFAULT_RESUME = Resume(
    full_name="Your Name",
    address="",
    phone="",
    email="",
    linkedin="",
    github="",
    portfolio="",
    education=[
        Education(
            uni="Example University",
            location="Example City, Country",
            degree="MSc. Computer Science",
            grade=", Grade 1.5",
            dates="September 2021 – August 2023",
        ),
        Education(
            uni="Example Institute of Technology",
            location="Example City, Country",
            degree="BSc. Software Engineering",
            grade=", Grade 1.2",
            dates="October 2017 – July 2021",
        ),
    ],
    experience=[
        Experience(
            company="Example Corp",
            location="Example City, Country",
            role="Software Engineer",
            dates="January 2022 – Present",
            bullets=[
                "Built and deployed scalable APIs serving 10K+ daily users, improving system throughput by 40%.",
                "Designed event-driven microservices architecture, reducing deployment time from days to hours.",
                "Implemented CI/CD pipelines with automated testing and canary deployments for zero-downtime releases.",
                "Mentored junior engineers through code review and pair programming, raising team velocity by 25%.",
                "Led migration from monolith to service-oriented architecture with zero production incidents.",
            ],
        ),
        Experience(
            company="Startup Ltd.",
            location="Remote",
            role="Junior Developer",
            dates="June 2020 – December 2021",
            bullets=[
                "Developed frontend components improving page load times by 30% across the core product.",
                "Built ETL pipelines processing large datasets for customer-facing analytics dashboards.",
                "Collaborated with design and product teams to ship 3 major features on schedule.",
            ],
        ),
        Experience(
            company="Freelance",
            location="Remote",
            role="Full-Stack Developer",
            dates="October 2019 – May 2020",
            bullets=[
                "Delivered web applications for small business clients using modern frontend and backend stacks.",
                "Built automated reporting tools that saved clients 10+ hours per week on manual data entry.",
                "Managed end-to-end projects from requirements gathering through deployment and maintenance.",
            ],
        ),
    ],
    skills=[
        Skill("Programming:", "Python, JavaScript, TypeScript, Go, SQL"),
        Skill("Frameworks:", "React, FastAPI, Node.js, Django"),
        Skill("Data & Storage:", "PostgreSQL, Redis, MongoDB, BigQuery"),
        Skill("DevOps & Cloud:", "Docker, Kubernetes, AWS, Terraform, CI/CD"),
        Skill("Tools:", "Git, GitHub Actions, Datadog, Jira, Figma"),
    ],
    certifications=[
        "AWS Solutions Architect Associate from Amazon Web Services",
        "Kubernetes Application Developer (CKAD) from CNCF",
        "Machine Learning Specialization from deeplearning.ai",
    ],
    projects=[
        Project(
            "E-Commerce Microservices Platform: ",
            "Scalable backend handling concurrent orders with event-driven architecture and message queues.",
        ),
        Project(
            "Real-Time Analytics Dashboard: ",
            "Live monitoring system processing streaming data with sub-second query response times.",
        ),
        Project(
            "Automated Deployment Pipeline: ",
            "CI/CD workflow with automated testing, linting, and zero-downtime rolling deployments.",
        ),
    ],
    achievements=[
        "Won 1st place in national hackathon out of 50+ participating teams.",
        "Open-source contributor with projects collectively reaching 500+ GitHub stars.",
    ],
)

DEFAULT_COVER = CoverLetter(
    full_name="Your Name",
    address="",
    phone="",
    email="",
    linkedin="",
    github="",
    portfolio="",
    recipient_name="Acme Corp Recruitment Team",
    recipient_city="Example City, Country",
    salutation="Dear Hiring Team,",
    paragraphs=[
        (
            "I am writing to apply for the Software Engineer position at Acme Corp. "
            "With a Master’s in Computer Science and hands-on "
            "experience building production systems at scale, I am drawn to your approach of combining "
            "engineering rigor with ambitious product thinking to build software used by millions."
        ),
        (
            "In my current role at Example Corp, I engineered scalable APIs, designed event-driven "
            "microservices, and implemented CI/CD pipelines that enabled zero-downtime deployments. "
            "Earlier, I built full-stack applications independently, taking ownership from design "
            "through deployment. These experiences pushed me to write clean, reproducible, production-ready code "
            "across diverse stacks – from Python backends and REST APIs to Docker and AWS. I have also "
            "presented technical solutions to stakeholders across the organization, which sharpened my ability "
            "to translate engineering decisions into business outcomes."
        ),
        (
            "What draws me to Acme Corp specifically is the expectation of real ownership, the focus on "
            "engineering excellence, and the culture of continuous improvement. "
            "I am at a stage in my career where I want to work somewhere that takes both product "
            "quality and team excellence seriously, and Acme Corp fits that precisely. I would welcome the "
            "opportunity to discuss how I can contribute. Thank you for your time and consideration."
        ),
    ],
    signoff_name="Your Name",
    signoff_email="",
    signoff_phone="",
)
