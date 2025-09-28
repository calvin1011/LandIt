import requests
import logging
from datetime import datetime
from database import db
from typing import Dict, List
import numpy as np

logger = logging.getLogger(__name__)


class RemotiveJobImporter:
    """
    Imports remote job postings from the Remotive API, following official documentation.
    """

    def __init__(self):
        """Initializes the importer and statistics."""
        self.api_url = "https://remotive.com/api/remote-jobs"
        self.stats = {
            'total_fetched': 0,
            'successfully_imported': 0,
            'failed_imports': 0,
            'duplicates_skipped': 0
        }

    def get_import_summary(self) -> Dict:
        """Returns a summary of the import statistics."""
        return self.stats

    def import_jobs(self, limit: int = 25):
        """
        Fetches jobs from the Remotive API and stores them in the database.

        Args:
            limit (int): The maximum number of jobs to fetch, per API documentation.
        """
        # Per Remotive's rate limiting, this function should not be called
        # excessively (e.g., more than 2x per minute or 4x per day).
        logger.info("=== Starting Remotive Job Import ===")
        try:
            if not db.test_connection():
                logger.error("Database connection failed. Aborting Remotive import.")
                return

            params = {'limit': limit}
            logger.info(f"Fetching up to {limit} jobs from Remotive API...")
            response = requests.get(self.api_url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()
            jobs_from_api = data.get('jobs', [])
            self.stats['total_fetched'] = len(jobs_from_api)
            logger.info(f"Found {self.stats['total_fetched']} jobs from API.")

            for job_data in jobs_from_api:
                try:
                    title = job_data.get('title', '').strip()
                    company = job_data.get('company_name', '').strip()

                    if not title or not company:
                        logger.warning("Skipping job with missing title or company name.")
                        self.stats['failed_imports'] += 1
                        continue

                    if db.get_jobs_by_title_company(title, company):
                        logger.info(f"Skipping duplicate job: {title} at {company}")
                        self.stats['duplicates_skipped'] += 1
                        continue

                    job_dict = self._prepare_job_data(job_data)

                    embeddings = {
                        'description': np.zeros(384),
                        'title': np.zeros(384),
                        'requirements': np.zeros(384)
                    }

                    db.store_job_posting(job_dict, embeddings)
                    self.stats['successfully_imported'] += 1

                except Exception as e:
                    self.stats['failed_imports'] += 1
                    logger.error(f"Failed to process job '{job_data.get('title')}': {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from Remotive API: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Remotive import: {e}")
        finally:
            logger.info(f"=== Remotive import completed: {self.stats} ===")

    def _prepare_job_data(self, job_data: Dict) -> Dict:
        """Transforms API data into the format needed for the database."""

        # Correctly parse the ISO 8601 date string from the API
        publication_date_str = job_data.get('publication_date')
        posted_date = datetime.utcnow()
        if publication_date_str:
            try:
                # Replace 'Z' with '+00:00' for broader Python version compatibility
                if publication_date_str.endswith('Z'):
                    publication_date_str = publication_date_str[:-1] + '+00:00'
                posted_date = datetime.fromisoformat(publication_date_str)
            except ValueError:
                logger.warning(f"Could not parse publication_date: {publication_date_str}")

        # The API response does not contain a 'tags' field.
        # We will use the 'category' as a starting point for skills.
        skills = []
        if category := job_data.get('category'):
            skills.append(category)

        return {
            'title': job_data.get('title', '').strip(),
            'company': job_data.get('company_name', '').strip(),
            'description': job_data.get('description', ''),
            'requirements': "See description",
            'location': job_data.get('candidate_required_location', 'Remote'),
            'remote_allowed': True,
            'experience_level': 'mid',
            'job_type': job_data.get('job_type', 'full-time'),
            'source': 'Remotive',
            'job_url': job_data.get('url', ''),
            'posted_date': posted_date,
            'skills_required': skills
        }