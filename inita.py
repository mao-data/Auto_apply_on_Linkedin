import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests
import smtplib
from email.mime.text import MIMEText
from selenium.webdriver.common.keys import Keys
import sys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class LinkedInAutoApply:
    def __init__(self, credentials_file='credentials.json', resume_path='path/to/your/resume.pdf'):
        self.resume_path = os.path.abspath(resume_path)
        self.logger = self.setup_logging()
        self.credentials = self.load_credentials(credentials_file)
        self.driver = self.setup_driver()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='linkedin_auto_apply.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('LinkedInAutoApply')

    def load_credentials(self, credentials_file):
        try:
            with open(credentials_file) as f:
                credentials = json.load(f)
                
            # Verify required fields
            required_fields = ['email', 'password']
            missing_fields = [field for field in required_fields if field not in credentials]
            if missing_fields:
                raise ValueError(f"Missing required fields in credentials.json: {missing_fields}")
                
            return credentials
        except FileNotFoundError:
            self.logger.error(f"Credentials file {credentials_file} not found")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON format in {credentials_file}")
            raise

    def setup_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--disable-notifications')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--start-maximized')
            return webdriver.Chrome(options=options)
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromeDriver: {str(e)}")
            raise

    def login(self):
        try:
            self.driver.get("https://www.linkedin.com/login")
            email_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            
            email_field.send_keys(self.credentials['email'])
            password_field.send_keys(self.credentials['password'])
            password_field.submit()
            
            # Add delay to ensure login completes
            time.sleep(3)
            
            self.logger.info("Successfully logged in to LinkedIn")
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    def search_jobs(self, keywords, location, filters=None):
        base_url = "https://www.linkedin.com/jobs/search/?"
        params = {
            'keywords': keywords,
            'location': location,
        }
        if filters:
            params.update(filters)
            
        search_url = base_url + '&'.join([f'{k}={v}' for k, v in params.items()])
        self.driver.get(search_url)
        self.logger.info(f"Searching jobs with parameters: {params}")

    def apply_to_job(self, job_url):
        try:
            self.driver.get(job_url)
            apply_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button"))
            )
            apply_button.click()
            
            # Auto-fill form logic would go here
            # This is a simplified version
            
            self.logger.info(f"Successfully applied to job: {job_url}")
            self.notify_user(f"Applied to job: {job_url}")
            
        except TimeoutException:
            self.logger.error(f"Timeout while applying to job: {job_url}")
        except Exception as e:
            self.logger.error(f"Error applying to job {job_url}: {str(e)}")

    def notify_user(self, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = 'LinkedIn Auto Apply Update'
            msg['From'] = self.credentials['email']
            msg['To'] = self.credentials['notification_email']

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(self.credentials['email'], self.credentials['email_password'])
                smtp_server.sendmail(self.credentials['email'], 
                                  self.credentials['notification_email'], 
                                  msg.as_string())
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")

    def cleanup(self):
        self.driver.quit()
        self.logger.info("Browser session closed")

    def apply_to_jobs(self, max_applications=10):
        """Apply to jobs with detailed logging and error handling"""
        jobs_applied = 0
        successful_applications = []  # List to store successful applications
        
        try:
            print("Waiting for job listings to load...")
            job_cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container"))
            )
            
            print(f"Found {len(job_cards)} job listings")
            
            for job_card in job_cards:
                if jobs_applied >= max_applications:
                    break
                    
                try:
                    # Click on the job card
                    print("Clicking on job card...")
                    job_card.click()
                    time.sleep(3)
                    
                    # Get job details
                    try:
                        job_title = self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text
                        company_name = self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text
                        job_location = self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__bullet").text
                    except:
                        job_title = "Unknown Title"
                        company_name = "Unknown Company"
                        job_location = "Unknown Location"
                    
                    # Find the Easy Apply button
                    try:
                        apply_button = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "jobs-apply-button"))
                        )
                        print(f"Found apply button for {job_title} at {company_name}")
                        
                        if "Easy Apply" in apply_button.text:
                            print("Clicking Easy Apply button...")
                            apply_button.click()
                            time.sleep(3)
                            
                            # Add resume upload handling
                            try:
                                print("Looking for resume upload field...")
                                resume_input = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((
                                        By.CSS_SELECTOR, 
                                        "input[type='file']"
                                    ))
                                )
                                resume_input.send_keys(self.resume_path)
                                print("Resume uploaded successfully")
                                time.sleep(2)
                                
                            except Exception as e:
                                print(f"No resume upload field found or error uploading: {str(e)}")
                            
                            # Handle the application steps
                            while True:
                                try:
                                    # Look for Next or Submit buttons
                                    next_button = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((
                                            By.CSS_SELECTOR, 
                                            "button[aria-label='Continue to next step'], button[aria-label='Submit application']"
                                        ))
                                    )
                                    
                                    if "Submit" in next_button.text:
                                        print("Submitting application...")
                                        next_button.click()
                                        jobs_applied += 1
                                        successful_applications.append({
                                            'title': job_title,
                                            'company': company_name,
                                            'location': job_location,
                                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                        })
                                        print(f"\n✅ Successfully applied to job #{jobs_applied}:")
                                        print(f"Title: {job_title}")
                                        print(f"Company: {company_name}")
                                        print(f"Location: {job_location}")
                                        print("-" * 50)
                                        break
                                    else:
                                        print("Clicking next...")
                                        next_button.click()
                                        time.sleep(2)
                                        
                                except Exception as e:
                                    print(f"Could not complete application: {str(e)}")
                                    break
                                    
                    except Exception as e:
                        print(f"Could not find Easy Apply button: {str(e)}")
                        continue
                        
                except Exception as e:
                    print(f"Error applying to job: {str(e)}")
                    continue
                    
                time.sleep(3)
                
        except Exception as e:
            print(f"Error in apply_to_jobs: {str(e)}")
        
        # Print summary of successful applications
        if successful_applications:
            print("\n📋 SUMMARY OF SUCCESSFUL APPLICATIONS:")
            print("=" * 50)
            for idx, app in enumerate(successful_applications, 1):
                print(f"\n{idx}. {app['title']}")
                print(f"   Company: {app['company']}")
                print(f"   Location: {app['location']}")
                print(f"   Applied: {app['timestamp']}")
                print("-" * 50)
        
        return jobs_applied, successful_applications

if __name__ == "__main__":
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    resume_path = os.path.join(current_dir, "resume.pdf")
    
    # Check if resume exists
    if not os.path.exists(resume_path):
        print(f"Error: Resume not found at {resume_path}")
        exit(1)
    
    auto_apply = LinkedInAutoApply(
        credentials_file='credentials.json',
        resume_path=resume_path
    )
    
    total_applications = 0
    page_number = 0
    
    try:
        print("Logging in to LinkedIn...")
        auto_apply.login()
        time.sleep(3)
        
        while True:
            try:
                print(f"\nStarting search page {page_number + 1}...")
                search_url = (
                    f"https://www.linkedin.com/jobs/search/"
                    f"?f_AL=true"
                    f"&f_E=1"
                    f"&f_JT=F"
                    f"&f_TPR=r604800"
                    f"&keywords=Software%20Engineer"
                    f"&location=United%20States"
                    f"&start={page_number * 25}"
                )
                
                auto_apply.driver.get(search_url)
                time.sleep(5)
                
                print("Starting job applications for this page...")
                remaining_applications = 10 - total_applications
                jobs_applied, successful_apps = auto_apply.apply_to_jobs(max_applications=remaining_applications)
                
                total_applications += jobs_applied
                print(f"\nTotal jobs applied so far: {total_applications}")
                
                if total_applications >= 10:
                    print("\n🎉 Reached maximum number of applications (10). Stopping...")
                    break
                
                if jobs_applied == 0:
                    print("No more jobs found on this page, moving to next page...")
                
                page_number += 1
                
            except Exception as e:
                print(f"Error on page {page_number}: {str(e)}")
                page_number += 1
                continue
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("\n🔍 FINAL SUMMARY")
        print("=" * 50)
        print(f"Total jobs applied: {total_applications}")
        print("=" * 50)
        auto_apply.cleanup()
