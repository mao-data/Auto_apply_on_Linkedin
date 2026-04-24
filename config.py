import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # LinkedIn credentials
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Job search settings
    JOB_KEYWORDS = os.getenv("JOB_KEYWORDS", "Software Engineer")
    JOB_LOCATION = os.getenv("JOB_LOCATION", "United States")
    EXPERIENCE_LEVEL = os.getenv("EXPERIENCE_LEVEL", "1")  # 1=Entry, 2=Mid-Senior, 3=Director
    JOB_TYPE = os.getenv("JOB_TYPE", "F")  # F=Full-time, P=Part-time, C=Contract
    MAX_APPLICATIONS = int(os.getenv("MAX_APPLICATIONS", "10"))

    # Resume
    RESUME_PATH = os.getenv("RESUME_PATH", "resume.pdf")

    @classmethod
    def validate(cls):
        """Validate that required config values are set."""
        missing = []
        if not cls.LINKEDIN_EMAIL:
            missing.append("LINKEDIN_EMAIL")
        if not cls.LINKEDIN_PASSWORD:
            missing.append("LINKEDIN_PASSWORD")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
