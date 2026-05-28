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
            uni="Friedrich-Alexander-Universitat",
            location="Erlangen-Germany",
            degree="MSc. Artificial Intelligence",
            grade=", Note 1.6",
            dates="April 2023 – March 2026 (Expected)",
        ),
        Education(
            uni="NED University of Engineering and Technology",
            location="Karachi-Pakistan",
            degree="BE., Industrial and Manufacturing Engineering",
            grade=", Grade 1.1",
            dates="December 2016 – October 2020",
        ),
    ],
    experience=[
        Experience(
            company="Siemens",
            location="Nuremberg, Germany",
            role="Working Student – Data Scientist",
            dates="October 2024 – Present",
            bullets=[
                "Developed and optimized Python-based forecasting models, improving accuracy by 10–12% across industrial use cases.",
                "Fine-tuned foundation models (Chronos) for electrical load demand forecasting, supporting production-level ML pipelines.",
                "Engineered scalable forecasting APIs with validation pipelines, increasing adoption by 20x and enhancing model reliability.",
                "Implemented MLflow-based experiment tracking, model versioning, and CI/CD workflows for reproducible deployments.",
                "Delivered analytical dashboards and demos to 500+ stakeholders, enabling data-driven planning and decisions.",
            ],
        ),
        Experience(
            company="TecHayal",
            location="Remote",
            role="Data Scientist",
            dates="November 2022 – March 2023",
            bullets=[
                "Built and deployed deep learning pipelines, improving image recognition accuracy by 30% for data-driven marketing.",
                "Designed Python APIs and automated data workflows, increasing system efficiency and data accessibility.",
                "Analyzed user and product data to generate actionable insights for business and product strategy.",
            ],
        ),
        Experience(
            company="Freelance",
            location="Remote",
            role="Data Scientist and Analyst",
            dates="October 2021 – November 2022",
            bullets=[
                "Built time-series forecasting models for sales and inventory planning, improving demand prediction efficiency.",
                "Developed SQL-based data pipelines to ensure high data quality and KPI reliability across client projects.",
                "Created Tableau and Power BI dashboards for automated reporting and performance monitoring.",
            ],
        ),
    ],
    skills=[
        Skill("Programming:", "Python, SQL, REST APIs, JavaScript"),
        Skill("AI/ML Engineering:", "PyTorch, TensorFlow, Scikit-learn, Foundation models, GenAI, RAG, AI Agents"),
        Skill("Software & DevOps:", "Git, GitHub, GitLab, Docker, AWS (S3, EC2), CI/CD, MLflow"),
        Skill("Data Engineering & ETL:", "Pandas, Dockerized workflows, MySQL, BigQuery"),
        Skill("Visualization & Tools:", "Streamlit, Plotly, Tableau, Power BI, MS Office"),
    ],
    certifications=[
        "Machine Learning in Production from deeplearning.ai",
        "Deep Learning Specialization from deeplearning.ai",
        "ChatGPT Prompt Engineering for Developers from deeplearning.ai",
    ],
    projects=[
        Project(
            "NLP and GenAI Projects – RAG and Multi-Agent: ",
            "End-to-end NLP and GenAI pipelines with retrieval-augmented generation and multi-agent systems.",
        ),
        Project(
            "SmartCompare – AI Product Recommender: ",
            "Python-based recommender delivering personalized product suggestions at scale.",
        ),
        Project(
            "YOLO v5 Object Detector: ",
            "Real-time object detection system achieving high accuracy in production scenarios.",
        ),
    ],
    achievements=[
        "Ranked 2nd in bachelor’s with a 3.9/4.0 GPA (1.1 German grade).",
        "Recipient of multiple merit-based scholarships awarded by HEC Pakistan and other organizations.",
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
    recipient_name="Bending Spoons Recruitment Team",
    recipient_city="Milan, Italy",
    salutation="Dear Hiring Team,",
    paragraphs=[
        (
            "I am writing to apply for the Graduate AI Software Engineer position at Bending Spoons. "
            "With a Master’s in Artificial Intelligence from FAU Erlangen-Nuremberg and hands-on "
            "experience building production AI systems at Siemens, I am drawn to your approach of combining "
            "engineering rigor with ambitious product thinking to build software used by millions."
        ),
        (
            "At Siemens, I engineered scalable forecasting APIs, fine-tuned foundation models for industrial "
            "energy demand prediction, and implemented end-to-end MLflow pipelines that increased model adoption "
            "by 20x. Earlier, I built deep learning and NLP systems independently, including a RAG-based research "
            "assistant and a real-time AI product recommender, which required taking full ownership from design "
            "through deployment. These experiences pushed me to write clean, reproducible, production-ready code "
            "across diverse stacks – from Python backends and REST APIs to Docker and AWS. I have also "
            "presented technical solutions to 500+ stakeholders, which sharpened my ability to translate "
            "engineering decisions into business outcomes."
        ),
        (
            "What draws me to Bending Spoons specifically is the expectation of real ownership, the integration "
            "of AI deeply into how work gets done, and the culture of simplifying relentlessly rather than adding "
            "complexity. I am at a stage in my career where I want to work somewhere that takes both product "
            "quality and team excellence seriously, and Bending Spoons fits that precisely. I would welcome the "
            "opportunity to discuss how I can contribute. Thank you for your time and consideration."
        ),
    ],
    signoff_name="Your Name",
    signoff_email="",
    signoff_phone="",
)
