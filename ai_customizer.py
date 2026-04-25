import logging

import anthropic
from config import Config

logger = logging.getLogger("LinkedInAutoApply")


class AICustomizer:
    """Uses Claude API to customize resumes and generate cover letters based on job descriptions."""

    def __init__(self):
        api_key = Config.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AI customization. Set it in .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = Config.AI_MODEL

    def tailor_resume_bullets(self, resume_text: str, job_description: str) -> str:
        """Generate tailored resume bullet points based on the job description."""
        logger.info("Generating tailored resume bullets...")
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a professional resume writer. Given my current resume and a job description, "
                        "rewrite ONLY the bullet points under each role to better align with the job requirements. "
                        "Keep the same job titles, companies, dates, and education. "
                        "Do NOT fabricate experience — only rephrase and emphasize relevant skills.\n\n"
                        f"## My Resume:\n{resume_text}\n\n"
                        f"## Job Description:\n{job_description}\n\n"
                        "Return the full updated resume text."
                    ),
                }
            ],
        )
        return message.content[0].text

    def generate_cover_letter(self, resume_text: str, job_description: str, company_name: str, job_title: str) -> str:
        """Generate a personalized cover letter for a specific job."""
        logger.info(f"Generating cover letter for {job_title} at {company_name}...")
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a concise, professional cover letter (under 300 words) for this job application. "
                        "Use specific details from my resume that match the job requirements. "
                        "Be genuine — do not exaggerate or fabricate.\n\n"
                        f"## Position: {job_title} at {company_name}\n\n"
                        f"## Job Description:\n{job_description}\n\n"
                        f"## My Resume:\n{resume_text}\n\n"
                        "Return only the cover letter text, ready to paste."
                    ),
                }
            ],
        )
        return message.content[0].text

    def analyze_job_fit(self, resume_text: str, job_description: str) -> dict:
        """Analyze how well the resume fits the job and return a score + suggestions."""
        logger.info("Analyzing job fit...")
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Analyze how well this resume matches the job description. "
                        "Return a JSON object with:\n"
                        '- "score": 1-10 fit score\n'
                        '- "matching_skills": list of skills that match\n'
                        '- "missing_skills": list of required skills not in resume\n'
                        '- "recommendation": "apply" or "skip" (apply if score >= 6)\n\n'
                        f"## Resume:\n{resume_text}\n\n"
                        f"## Job Description:\n{job_description}\n\n"
                        "Return ONLY valid JSON, no markdown."
                    ),
                }
            ],
        )
        import json

        raw = message.content[0].text
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI job fit response as JSON: {raw[:200]}")
            return {"score": 0, "recommendation": "skip", "matching_skills": [], "missing_skills": ["parse_error"]}
