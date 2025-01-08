# LinkedIn Auto Job Application Bot

A Python script that automates the job application process on LinkedIn using Selenium WebDriver.

## Features
- Automatically logs into LinkedIn
- Searches for jobs based on specified criteria
- Applies to jobs with "Easy Apply" option
- Handles resume uploads automatically
- Tracks and logs successful applications
- Supports customizable search filters
- Limits maximum applications to prevent overuse

## Prerequisites
```
pip install selenium
pip install webdriver-manager
pip install beautifulsoup4
```

## Setup
1. Create a `credentials.json` file in the project directory:
```
json
{
"email": "your_linkedin_email@example.com",
"password": "your_linkedin_password"
}
```
2. Place your resume (PDF format) in the project directory
3. Update the resume filename in the script 

## Usage
```
python inita.py
```
## Configuration Options
You can modify these parameters in the script:
- Job keywords (default: "Data Analyst")
- Location (default: "United States")
- Experience level (default: Entry level)
- Job type (default: Full-time)
- Time period (default: Past week)
- Maximum applications (default: 10)

## Search Filters
```
filters = {
"f_E": "1" # Experience Level (1=Entry, 2=Mid-Senior, 3=Director)
"f_JT": "F" # Job Type (F=Full-time, P=Part-time, C=Contract)
"f_AL": "true" # Easy Apply only
"f_TPR": "r604800" # Time Posted (Past week)
}
```
## Output Example
✅ Successfully applied to job #1:
```
Title: Data Analyst
Company: Example Corp
Location: Remote
--------------------------------------------------
📋 SUMMARY OF SUCCESSFUL APPLICATIONS:
==================================================
Data Analyst
Company: Example Corp
Location: Remote
Applied: 2024-03-14 15:30:45
--------------------------------------------------
```
## Safety Features
- Automatic breaks between applications
- Error handling for failed applications
- Clean exit on completion
- Progress tracking
- Detailed logging

## Limitations
- Only works with "Easy Apply" jobs
- Requires LinkedIn account
- May need updates if LinkedIn changes their website structure
- Limited to 10 applications per run (configurable)

## Contributing
Feel free to fork this repository and submit pull requests for any improvements.

## Disclaimer
This tool is for educational purposes only. Use it responsibly and in accordance with LinkedIn's terms of service. The authors are not responsible for any account restrictions or other consequences of using this tool.

## Author
Moris Wu
