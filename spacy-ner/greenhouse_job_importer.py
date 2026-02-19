import requests
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from database import db
from embedding_service import ResumeJobEmbeddingService
import re
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class GreenhouseJobImporter:
    BOARD_TOKENS = [
        "stripe",
        "shopify",
        "datadog",
        "doordash",
        "notion",
        "affirm",
        "cloudflare",
        "anduril",
        "canonical",
        "coinbase"
    ]
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"

    def __init__(self):
        self.session = requests.Session()
        try:
            self.embedding_service = ResumeJobEmbeddingService()
        except Exception as e:
            logger.error(f"Embedding service failed: {e}")
            self.embedding_service = None

        self.stats = {'total_fetched': 0, 'successfully_imported': 0, 'failed_imports': 0, 'duplicate_jobs': 0}

    def import_jobs(self, max_jobs_per_source: int = 250):
        """Imports jobs from a list of Greenhouse job boards"""

        for token in self.BOARD_TOKENS:
            self._import_jobs_for_token(token, max_jobs_per_source)

        logger.info(f"Greenhouse import completed: {self.stats}")
        return self.stats

    def _import_jobs_for_token(self, token: str, max_jobs: int):
        url = self.BASE_URL.format(board_token=token)
        jobs_imported = 0

        try:
            # Fetch job summary list
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            jobs_list = data.get('jobs', [])
            self.stats['total_fetched'] += len(jobs_list)

            # Use the company name provided by the API if available
            company_name = data.get('id', token).capitalize()

            logger.info(f"Fetched {len(jobs_list)} jobs from {company_name}'s board.")

            for job_summary in jobs_list:
                if jobs_imported >= max_jobs:
                    break

                try:
                    # Appends the job ID to the summary URL (which ends in /jobs)
                    full_job_url = f"{url}/{job_summary['id']}?questions=true"
                    full_job_response = self.session.get(full_job_url, timeout=30)
                    full_job_response.raise_for_status()
                    full_job_data = full_job_response.json()

                    # Process and Store
                    if self._process_job(full_job_data, company_name):
                        jobs_imported += 1
                        self.stats['successfully_imported'] += 1
                    else:
                        self.stats['duplicate_jobs'] += 1
                except Exception as e:
                    logger.error(f"Failed to process individual job {job_summary.get('id')}: {e}")
                    self.stats['failed_imports'] += 1
                    continue

            logger.info(f"Completed token '{token}': imported {jobs_imported} jobs")

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for token '{token}': {e}")
            self.stats['failed_imports'] += 1

    def _determine_experience_level(self, title: str, description: str) -> str:
        text = (title + ' ' + description).lower()
        if any(word in text for word in ['senior', 'sr.', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'intern', 'graduate', 'trainee']):
            return 'entry'
        elif any(word in text for word in ['manager', 'director', 'head of', 'vp', 'chief']):
            return 'executive'
        else:
            return 'mid'

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract technical skills from job description using shared skill taxonomy."""
        from api import extract_skills_for_jobs
        return extract_skills_for_jobs(description, max_skills=20)

    def _is_duplicate_job(self, title: str, company: str) -> bool:
        """Check if job already exists in database"""
        try:
            existing_jobs = db.get_jobs_by_title_company(title, company)
            return len(existing_jobs) > 0
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            return False

    def _process_job(self, job_data: Dict[str, Any], company_name: str) -> bool:
        description_html = job_data.get('content', '')
        description_clean = BeautifulSoup(description_html, 'html.parser').get_text()

        posted_date = datetime.now()

        location_parts = []
        offices = job_data.get('offices', [])
        for office in offices:
            if isinstance(office, dict) and office.get('location'):
                location_obj = office['location']
                if isinstance(location_obj, dict) and location_obj.get('name'):
                    location_parts.append(location_obj['name'])
                elif isinstance(location_obj, str):
                    location_parts.append(location_obj)

        location = ', '.join(location_parts) if location_parts else ''

        job_dict = {
            'title': job_data.get('title', ''),
            'company': company_name,
            'description': description_clean,
            'requirements': description_clean,
            'responsibilities': '',
            'location': location,
            'job_url': job_data.get('absolute_url', ''),
            'source': 'greenhouse',
            'external_id': str(job_data.get('id', '')),
            'experience_level': self._determine_experience_level(job_data.get('title', ''), description_clean),
            'skills_required': self._extract_skills_from_description(description_clean),
            'salary_min': None,
            'salary_max': None,
            'posted_date': posted_date,
            'remote_allowed': 'remote' in job_data.get('title', '').lower() or 'remote' in description_clean.lower()
        }

        if self._is_duplicate_job(job_dict['title'], job_dict['company']):
            return False

        # Embedding generation
        embeddings = {}
        if self.embedding_service:
            try:
                # Generate embeddings using the same methods as other importers
                description_embedding = self.embedding_service.generate_job_embedding(job_dict)
                title_embedding = self.embedding_service.model.encode(job_dict['title'])
                requirements_embedding = self.embedding_service.model.encode(job_dict.get('requirements', ''))

                # Ensure embeddings are not empty
                if (description_embedding is not None and
                        description_embedding.size > 0 and
                        title_embedding is not None and
                        title_embedding.size > 0):

                    embeddings = {
                        'description': description_embedding,
                        'title': title_embedding,
                        'requirements': requirements_embedding
                    }
                else:
                    logger.warning(f"Empty embeddings generated for job: {job_dict['title']}")
                    # Create dummy embeddings to avoid database error
                    dummy_embedding = np.random.rand(384)
                    embeddings = {
                        'description': dummy_embedding,
                        'title': dummy_embedding,
                        'requirements': dummy_embedding
                    }

            except Exception as e:
                logger.warning(f"Failed to generate embeddings for job '{job_dict['title']}': {e}")
                # Create dummy embeddings as fallback
                dummy_embedding = np.random.rand(384)
                embeddings = {
                    'description': dummy_embedding,
                    'title': dummy_embedding,
                    'requirements': dummy_embedding
                }

        try:
            db.store_job_posting(job_dict, embeddings)
            logger.debug(f"Stored Greenhouse job: {job_dict['title']} at {job_dict['company']}")
            return True
        except Exception as e:
            logger.error(f"Failed to store job in database: {e}")
            return False

    def get_import_summary(self) -> Dict[str, Any]:
        """Get summary of import statistics"""
        return {
            'imported': self.stats['successfully_imported'],
            'total_fetched': self.stats['total_fetched'],
            'failed': self.stats['failed_imports'],
            'duplicates': self.stats['duplicate_jobs'],
            'source': 'greenhouse'
        }