import os
import time
import json
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import Config


class LinkedInAutoApply:
    def __init__(self, use_ai=False):
        Config.validate()
        self.logger = self._setup_logging()
        self.driver = self._setup_driver()
        self.resume_path = os.path.abspath(Config.RESUME_PATH)
        self.use_ai = use_ai
        self.ai = None

        if use_ai:
            try:
                from ai_customizer import AICustomizer
                self.ai = AICustomizer()
                self.resume_text = self._read_resume_text()
                self.logger.info("AI customization enabled")
            except Exception as e:
                self.logger.warning(f"AI customization unavailable: {e}. Continuing without AI.")
                self.use_ai = False

    def _read_resume_text(self):
        """Read resume text for AI processing. Supports .txt and .pdf (with PyPDF2)."""
        resume_path = self.resume_path
        if resume_path.endswith(".txt"):
            with open(resume_path) as f:
                return f.read()
        elif resume_path.endswith(".pdf"):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(resume_path)
                return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
            except ImportError:
                self.logger.warning("PyPDF2 not installed. Install it for PDF resume reading: pip install PyPDF2")
                return ""
        return ""

    def _setup_logging(self):
        logger = logging.getLogger("LinkedInAutoApply")
        logger.setLevel(logging.INFO)

        # File handler
        fh = logging.FileHandler("linkedin_auto_apply.log")
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(ch)

        return logger

    def _setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )

    def _wait_and_find(self, by, value, timeout=10):
        """Wait for element and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def _wait_and_click(self, by, value, timeout=10):
        """Wait for element to be clickable and click it."""
        el = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        el.click()
        return el

    def _safe_find_text(self, by, value, default="Unknown"):
        """Find element text without raising exceptions."""
        try:
            return self.driver.find_element(by, value).text.strip()
        except (NoSuchElementException, Exception):
            return default

    def login(self):
        """Log into LinkedIn."""
        self.logger.info("Logging in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)

        self._wait_and_find(By.ID, "username").send_keys(Config.LINKEDIN_EMAIL)
        self._wait_and_find(By.ID, "password").send_keys(Config.LINKEDIN_PASSWORD)
        self._wait_and_click(By.CSS_SELECTOR, "button[type='submit']")

        time.sleep(5)

        # Check for security verification
        if "checkpoint" in self.driver.current_url:
            self.logger.warning("LinkedIn security check detected. Please complete it manually.")
            input("Press Enter after completing the security check...")

        self.logger.info("Login successful")

    def search_jobs(self, page=0):
        """Navigate to job search results page."""
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?f_AL=true"
            f"&f_E={Config.EXPERIENCE_LEVEL}"
            f"&f_JT={Config.JOB_TYPE}"
            f"&f_TPR=r604800"
            f"&keywords={Config.JOB_KEYWORDS.replace(' ', '%20')}"
            f"&location={Config.JOB_LOCATION.replace(' ', '%20')}"
            f"&start={page * 25}"
        )
        self.driver.get(search_url)
        time.sleep(4)
        self.logger.info(f"Searching: {Config.JOB_KEYWORDS} in {Config.JOB_LOCATION} (page {page + 1})")

    def _get_job_cards(self):
        """Get all job card elements on the current page."""
        selectors = [
            "div.job-card-container",
            "li.jobs-search-results__list-item",
            "div.jobs-search-results-list__list-item",
            "li.ember-view.jobs-search-results__list-item",
        ]
        for selector in selectors:
            try:
                cards = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if cards:
                    return cards
            except TimeoutException:
                continue
        return []

    def _get_job_details(self):
        """Extract job title, company, and location from the detail panel."""
        title_selectors = [
            "h1.t-24",
            "h2.t-24",
            "h1.job-details-jobs-unified-top-card__job-title",
            "h1.jobs-unified-top-card__job-title",
            "a.job-details-jobs-unified-top-card__job-title-link",
        ]
        company_selectors = [
            "div.job-details-jobs-unified-top-card__company-name a",
            "span.job-details-jobs-unified-top-card__company-name",
            "a.jobs-unified-top-card__company-name",
            "span.jobs-unified-top-card__company-name",
        ]
        location_selectors = [
            "span.job-details-jobs-unified-top-card__bullet",
            "span.jobs-unified-top-card__bullet",
            "span.jobs-unified-top-card__workplace-type",
        ]

        title = "Unknown Title"
        company = "Unknown Company"
        location = "Unknown Location"

        for sel in title_selectors:
            title = self._safe_find_text(By.CSS_SELECTOR, sel)
            if title != "Unknown":
                break
        for sel in company_selectors:
            company = self._safe_find_text(By.CSS_SELECTOR, sel)
            if company != "Unknown":
                break
        for sel in location_selectors:
            location = self._safe_find_text(By.CSS_SELECTOR, sel)
            if location != "Unknown":
                break

        return title, company, location

    def _get_job_description(self):
        """Extract the full job description text."""
        desc_selectors = [
            "div.jobs-description__content",
            "div.jobs-box__html-content",
            "div#job-details",
            "article.jobs-description",
        ]
        for sel in desc_selectors:
            text = self._safe_find_text(By.CSS_SELECTOR, sel)
            if text != "Unknown" and len(text) > 50:
                return text
        return ""

    def _click_easy_apply(self):
        """Find and click the Easy Apply button. Returns True if successful."""
        apply_selectors = [
            "button.jobs-apply-button",
            "button.jobs-apply-button--top-card",
            "button[aria-label*='Easy Apply']",
            "div.jobs-apply-button--top-card button",
        ]
        for selector in apply_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if "Easy Apply" in btn.text or "easy apply" in btn.text.lower():
                    btn.click()
                    time.sleep(2)
                    return True
            except (TimeoutException, Exception):
                continue
        return False

    def _upload_resume(self):
        """Attempt to upload resume if a file input is found."""
        try:
            file_input = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(self.resume_path)
            self.logger.info("Resume uploaded")
            time.sleep(2)
        except (TimeoutException, Exception):
            pass  # Resume may already be on file

    def _navigate_application_steps(self):
        """Navigate through multi-step application form. Returns True if submitted."""
        max_steps = 10
        for _ in range(max_steps):
            time.sleep(2)
            # Check for submit button
            try:
                submit_btn = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "button[aria-label='Submit application'], "
                    "button[aria-label='Review your application'], "
                    "button[data-easy-apply-next-button][aria-label='Submit application']"
                )
                if "Submit" in submit_btn.text or "Review" in submit_btn.text:
                    submit_btn.click()
                    time.sleep(2)
                    # If it was "Review", look for the final submit
                    try:
                        final_submit = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((
                                By.CSS_SELECTOR,
                                "button[aria-label='Submit application']"
                            ))
                        )
                        final_submit.click()
                        time.sleep(2)
                    except (TimeoutException, Exception):
                        pass
                    return True
            except NoSuchElementException:
                pass

            # Check for next button
            try:
                next_btn = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "button[aria-label='Continue to next step'], "
                    "button[data-easy-apply-next-button]"
                )
                next_btn.click()
                time.sleep(2)
            except NoSuchElementException:
                break

        return False

    def _dismiss_modal(self):
        """Close any post-application or error modals."""
        dismiss_selectors = [
            "button[aria-label='Dismiss']",
            "button[aria-label='Discard']",
            "button.artdeco-modal__dismiss",
        ]
        for sel in dismiss_selectors:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                btn.click()
                time.sleep(1)
                return
            except (NoSuchElementException, Exception):
                continue

    def apply_to_jobs(self):
        """Main loop: iterate through job cards and apply."""
        successful = []
        jobs_applied = 0

        job_cards = self._get_job_cards()
        if not job_cards:
            self.logger.warning("No job cards found on this page")
            return 0, successful

        self.logger.info(f"Found {len(job_cards)} job listings")

        for card in job_cards:
            if jobs_applied >= Config.MAX_APPLICATIONS:
                break

            try:
                card.click()
                time.sleep(3)

                title, company, location = self._get_job_details()
                self.logger.info(f"Reviewing: {title} at {company}")

                # AI job fit analysis (optional)
                if self.use_ai and self.ai and self.resume_text:
                    job_desc = self._get_job_description()
                    if job_desc:
                        try:
                            fit = self.ai.analyze_job_fit(self.resume_text, job_desc)
                            score = fit.get("score", 5)
                            rec = fit.get("recommendation", "apply")
                            self.logger.info(f"  AI fit score: {score}/10 — {rec}")
                            if rec == "skip":
                                self.logger.info(f"  Skipping (low fit). Missing: {fit.get('missing_skills', [])}")
                                continue
                        except Exception as e:
                            self.logger.warning(f"  AI analysis failed: {e}")

                # Click Easy Apply
                if not self._click_easy_apply():
                    self.logger.info(f"  No Easy Apply button found, skipping")
                    continue

                # Upload resume
                self._upload_resume()

                # Navigate steps and submit
                if self._navigate_application_steps():
                    jobs_applied += 1
                    app_info = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    successful.append(app_info)
                    self.logger.info(f"  ✅ Applied #{jobs_applied}: {title} at {company}")

                    # Generate cover letter for records (optional)
                    if self.use_ai and self.ai and self.resume_text:
                        job_desc = self._get_job_description()
                        if job_desc:
                            try:
                                cover_letter = self.ai.generate_cover_letter(
                                    self.resume_text, job_desc, company, title
                                )
                                app_info["cover_letter"] = cover_letter
                                self.logger.info("  Cover letter generated and saved")
                            except Exception as e:
                                self.logger.warning(f"  Cover letter generation failed: {e}")
                else:
                    self.logger.info(f"  Could not complete application for {title}")
                    self._dismiss_modal()

            except Exception as e:
                self.logger.error(f"  Error processing job card: {e}")
                self._dismiss_modal()
                continue

            time.sleep(3)

        return jobs_applied, successful

    def cleanup(self):
        """Close browser and save application log."""
        self.driver.quit()
        self.logger.info("Browser session closed")

    def save_results(self, applications):
        """Save successful applications to a JSON file."""
        if not applications:
            return
        filename = f"applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(applications, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Results saved to {filename}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Auto Apply Bot")
    parser.add_argument("--ai", action="store_true", help="Enable AI-powered job fit analysis and cover letter generation")
    parser.add_argument("--max", type=int, default=None, help="Override max applications (default from .env)")
    args = parser.parse_args()

    if args.max:
        Config.MAX_APPLICATIONS = args.max

    resume_path = os.path.abspath(Config.RESUME_PATH)
    if not os.path.exists(resume_path):
        print(f"Error: Resume not found at {resume_path}")
        print("Set RESUME_PATH in your .env file or place resume.pdf in the project directory.")
        exit(1)

    bot = LinkedInAutoApply(use_ai=args.ai)
    all_applications = []
    total_applied = 0
    page = 0

    try:
        bot.login()
        time.sleep(3)

        while total_applied < Config.MAX_APPLICATIONS:
            bot.search_jobs(page=page)
            applied, apps = bot.apply_to_jobs()

            all_applications.extend(apps)
            total_applied += applied

            if applied == 0:
                bot.logger.info("No more applications on this page, moving on...")

            page += 1
            time.sleep(3)

    except KeyboardInterrupt:
        bot.logger.info("Stopped by user")
    except Exception as e:
        bot.logger.error(f"Fatal error: {e}")
    finally:
        print(f"\n{'=' * 50}")
        print(f"FINAL SUMMARY: Applied to {total_applied} jobs")
        print(f"{'=' * 50}")
        if all_applications:
            for i, app in enumerate(all_applications, 1):
                print(f"\n{i}. {app['title']}")
                print(f"   Company: {app['company']}")
                print(f"   Location: {app['location']}")
                print(f"   Applied: {app['timestamp']}")
            print(f"\n{'=' * 50}")

        bot.save_results(all_applications)
        bot.cleanup()


if __name__ == "__main__":
    main()
