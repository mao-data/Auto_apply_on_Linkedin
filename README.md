# LinkedIn Auto Job Application Bot

Automated LinkedIn job application tool with **AI-powered resume customization** using Claude API.

## Features

- **Automated Easy Apply** — Finds and applies to LinkedIn jobs automatically
- **AI Job Fit Analysis** — Uses Claude to score how well your resume matches each job (skip low-fit jobs)
- **AI Cover Letter Generation** — Generates personalized cover letters for each application
- **Smart Resume Tailoring** — Rewrites bullet points to align with job requirements
- **Multi-page Search** — Automatically paginates through search results
- **Security Check Handling** — Pauses for manual verification when LinkedIn detects automation
- **Application Logging** — Saves all successful applications to JSON with timestamps
- **Configurable Filters** — Job keywords, location, experience level, job type, and more

## Prerequisites

```bash
pip install -r requirements.txt
```

Optional (for PDF resume reading):
```bash
pip install PyPDF2
```

## Setup

1. Copy the environment template and fill in your credentials:
```bash
cp .env.example .env
```

2. Edit `.env` with your details:
```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
ANTHROPIC_API_KEY=sk-ant-xxxxx    # Optional, for AI features
JOB_KEYWORDS=Software Engineer
JOB_LOCATION=United States
MAX_APPLICATIONS=10
```

3. Place your resume (PDF or TXT) in the project directory

## Usage

### Basic (no AI)
```bash
python inita.py
```

### With AI-powered customization
```bash
python inita.py --ai
```

### Override max applications
```bash
python inita.py --ai --max 20
```

## Configuration

All settings are managed via `.env` file:

| Variable | Default | Description |
|---|---|---|
| `LINKEDIN_EMAIL` | (required) | Your LinkedIn email |
| `LINKEDIN_PASSWORD` | (required) | Your LinkedIn password |
| `ANTHROPIC_API_KEY` | (optional) | Claude API key for AI features |
| `JOB_KEYWORDS` | Software Engineer | Job search keywords |
| `JOB_LOCATION` | United States | Job location |
| `EXPERIENCE_LEVEL` | 1 | 1=Entry, 2=Mid-Senior, 3=Director |
| `JOB_TYPE` | F | F=Full-time, P=Part-time, C=Contract |
| `MAX_APPLICATIONS` | 10 | Max applications per run |
| `RESUME_PATH` | resume.pdf | Path to your resume |

## AI Features (Optional)

When running with `--ai`, the bot will:

1. **Analyze job fit** before applying — scores each job 1-10 and skips poor matches (< 6)
2. **Generate cover letters** for each successful application (saved to the results JSON)
3. **Identify skill gaps** — logs which required skills are missing from your resume

Requires an [Anthropic API key](https://console.anthropic.com/).

## Output

Successful applications are saved to `applications_YYYYMMDD_HHMMSS.json`:

```json
[
  {
    "title": "Software Engineer",
    "company": "Example Corp",
    "location": "Remote",
    "timestamp": "2026-04-24 15:30:45",
    "cover_letter": "Dear Hiring Manager..."
  }
]
```

## Project Structure

```
├── inita.py           # Main bot script
├── config.py          # Configuration management
├── ai_customizer.py   # AI-powered resume/cover letter tools
├── .env.example       # Environment template
├── .gitignore         # Git ignore rules
├── requirements.txt   # Python dependencies
└── README.md
```

## Safety Features

- Automatic delays between applications to avoid rate limiting
- Handles LinkedIn security verification prompts
- Graceful error handling — skips problematic jobs and continues
- Anti-detection browser flags
- Keyboard interrupt support (Ctrl+C to stop gracefully)

## Limitations

- Only works with "Easy Apply" jobs
- LinkedIn may change their DOM structure — selectors may need updates
- Some multi-step applications with custom questions may fail
- AI features require an Anthropic API key and incur API costs

## Disclaimer

This tool is for educational purposes only. Use responsibly and in accordance with LinkedIn's terms of service.

## Author

Moris Wu
