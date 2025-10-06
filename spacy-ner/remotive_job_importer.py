import requests
import logging
from datetime import datetime
from database import db
from typing import Dict, List
from embedding_service import ResumeJobEmbeddingService # <-- ADDED IMPORT

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
        # Initialize embedding service for job processing
        try:
            self.embedding_service = ResumeJobEmbeddingService()
            logger.info("Embedding service ready for Remotive jobs")
        except Exception as e:
            logger.error(f"Embedding service failed: {e}")
            self.embedding_service = None

    def get_import_summary(self) -> Dict:
        """Returns a summary of the import statistics."""
        return self.stats

    def import_jobs(self, limit: int = 25):
        """
        Fetches jobs from the Remotive API and stores them in the database.

        Args:
            limit (int): The maximum number of jobs to fetch, per API documentation.
        """

        if not self.embedding_service:
            logger.error("Embedding service not available. Aborting import.")
            return

        logger.info("=== Starting Remotive Job Import ===")
        try:
            if not db.test_connection():
                logger.error("Database connection failed. Aborting Remotive import.")
                return

            response = requests.get(self.api_url, params={'limit': limit})
            response.raise_for_status()
            data = response.json()
            jobs_to_process = data.get('jobs', [])
            self.stats['total_fetched'] = len(jobs_to_process)

            logger.info(f"Fetched {self.stats['total_fetched']} jobs from Remotive API.")

            for job in jobs_to_process:
                try:
                    job_data = self._normalize_job_data(job)

                    if self._is_duplicate(job_data['title'], job_data['company']):
                        self.stats['duplicates_skipped'] += 1
                        continue

                    # Generate embeddings
                    description_text = job_data.get('description', '')
                    description_embedding = self.embedding_service.generate_embedding(description_text)

                    # Generate skills embedding
                    skills_list = job_data.get('skills_required', [])
                    skills_embedding = None
                    if skills_list:
                        skills_text = ". ".join(skills_list)
                        skills_embedding = self.embedding_service.generate_embedding(skills_text)

                    # Store job posting with embeddings
                    job_id = db.store_job_posting(
                        job_data,
                        {
                            'description': description_embedding,
                            'requirements': description_embedding,
                            'skills_embedding': skills_embedding
                        }
                    )

                    if job_id:
                        self.stats['successfully_imported'] += 1
                    else:
                        self.stats['failed_imports'] += 1

                except Exception as e:
                    logger.error(f"Error processing job ID {job.get('id')}: {e}")
                    self.stats['failed_imports'] += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch jobs from Remotive API: {e}")

        logger.info("=== Remotive Job Import Finished ===")


    def _is_duplicate(self, title: str, company: str) -> bool:
        """
        Checks if a job with the same title and company already exists.
        """
        return db.get_jobs_by_title_company(title, company) is not None


    def _normalize_job_data(self, job_data: Dict) -> Dict:
        """
        Normalizes data from the Remotive API to match the database schema.
        """
        # Parse the ISO 8601 date string from the API
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
            'external_job_id': str(job_data.get('id', '')),
            'posted_date': posted_date.strftime('%Y-%m-%d'),
            'skills_required': skills
        }