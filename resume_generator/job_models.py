"""Models for scraped job listings."""

from dataclasses import dataclass, field


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    date_posted: str = ""
    job_board: str = ""
    job_link: str = ""
    description: str = ""
