import requests
import logging
import time
import os
from typing import List, Dict, Any
from database import db
from embedding_service import ResumeJobEmbeddingService

logger = logging.getLogger(__name__)

class USAJobsImporter:
    """
    Imports job data from the USAJOBS API.
    """

    def __init__(self):
        self.api_key = os.getenv('USAJOBS_API_KEY')
        self.user_email = os.getenv('USER_EMAIL')
        self.base_url = "https://data.usajobs.gov/api"

        if not self.api_key or not self.user_email:
            raise ValueError("USAJOBS_API_KEY and USER_EMAIL must be set in .env file")

        self.session = requests.Session()
        self.session.headers.update({
            'Host': 'data.usajobs.gov',
            'User-Agent': self.user_email,
            'Authorization-Key': self.api_key
        })

        self.embedding_service = ResumeJobEmbeddingService()
        self.stats = {
            'total_fetched': 0,
            'successfully_imported': 0,
            'failed_imports': 0,
            'duplicates_skipped': 0
        }

    def get_import_summary(self) -> Dict:
        return self.stats

    def import_jobs(self, keywords: List[str] = None, max_jobs: int = 50):
        if keywords is None:
            keywords = ["IT Specialist", "Data Scientist", "Cybersecurity Specialist"]

        logger.info(f"=== Starting USAJOBS Job Import for {len(keywords)} keywords ===")
        jobs_per_keyword = max_jobs // len(keywords)

        for keyword in keywords:
            try:
                self._import_jobs_for_keyword(keyword, jobs_per_keyword)
                time.sleep(1.5)  # Be respectful of the API
            except Exception as e:
                logger.error(f"Failed to import jobs for keyword '{keyword}': {e}")
                self.stats['failed_imports'] += 1

        logger.info(f"=== USAJOBS import completed: {self.stats} ===")

    def _import_jobs_for_keyword(self, keyword: str, max_per_keyword: int):
        page = 1
        imported_count = 0
        max_pages = 20  # API limit is 10,000 results / 500 per page = 20 pages

        while imported_count < max_per_keyword and page <= max_pages:
            params = {
                'Keyword': keyword,
                'ResultsPerPage': 500,
                'Page': page
            }
            try:
                response = self.session.get(f"{self.base_url}/Search", params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                jobs = data.get('SearchResult', {}).get('SearchResultItems', [])

                if not jobs:
                    logger.info(f"No more jobs found for '{keyword}' on page {page}.")
                    break

                self.stats['total_fetched'] += len(jobs)

                for job_data in jobs:
                    if imported_count >= max_per_keyword:
                        break
                    if self._process_job(job_data.get('MatchedObjectDescriptor', {})):
                        imported_count += 1
                        self.stats['successfully_imported'] += 1
                    else:
                        self.stats['duplicates_skipped'] += 1

                page += 1
                time.sleep(1)  # Delay between pages

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed for '{keyword}' page {page}: {e}")
                break

    def _process_job(self, job_data: Dict[str, Any]) -> bool:
        title = job_data.get('PositionTitle', 'Unknown Title')
        company = job_data.get('OrganizationName', 'Unknown Company')

        if self._is_duplicate_job(title, company):
            return False

        job_dict = self._extract_job_details(job_data)

        embeddings = {}
        try:
            description_embedding = self.embedding_service.generate_job_embedding(job_dict)
            title_embedding = self.embedding_service.model.encode(job_dict['title'])
            requirements_embedding = self.embedding_service.model.encode(job_dict.get('requirements', ''))
            embeddings = {
                'description': description_embedding,
                'title': title_embedding,
                'requirements': requirements_embedding
            }
        except Exception as e:
            logger.warning(f"Could not generate embeddings for '{title}': {e}")

        db.store_job_posting(job_dict, embeddings)
        logger.info(f"Stored USAJOBS job: {job_dict['title']} at {job_dict['company']}")
        return True

    def _extract_job_details(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Maps USAJOBS API fields to our database schema."""
        salary_min = job_data.get('PositionRemuneration', [{}])[0].get('MinimumRange')
        salary_max = job_data.get('PositionRemuneration', [{}])[0].get('MaximumRange')

        # Helper function to safely join lists or use strings
        def to_string(value: Any) -> str:
            if isinstance(value, list):
                return ' '.join(str(v) for v in value)
            return str(value) if value is not None else ''

        job_summary = job_data.get('UserArea', {}).get('Details', {}).get('JobSummary', '')
        requirements = job_data.get('UserArea', {}).get('Details', {}).get('Requirements', '')
        responsibilities = job_data.get('UserArea', {}).get('Details', {}).get('MajorDuties', '')

        return {
            'title': job_data.get('PositionTitle', 'Unknown Title').strip(),
            'company': job_data.get('OrganizationName', 'US Government').strip(),
            'description': to_string(job_summary),
            'requirements': to_string(requirements),
            'responsibilities': to_string(responsibilities),
            'location': job_data.get('PositionLocationDisplay', 'Various Locations'),
            'remote_allowed': 'Telework' in job_data.get('UserArea', {}).get('Details', {}).get('Telework', ''),
            'salary_min': int(float(salary_min)) if salary_min and salary_min != '0' else None,
            'salary_max': int(float(salary_max)) if salary_max and salary_max != '0' else None,
            'job_type': 'full-time',
            'experience_level': 'mid',
            'source': 'USAJOBS',
            'job_url': job_data.get('PositionURI', ''),
            'external_job_id': job_data.get('PositionID'),
            'posted_date': job_data.get('PublicationStartDate')
        }

    def _is_duplicate_job(self, title: str, company: str) -> bool:
        try:
            return len(db.get_jobs_by_title_company(title, company)) > 0
        except Exception as e:
            logger.error(f"Error checking for duplicate job: {e}")
            return False  # Proceed with insertion if check fails

    def test_api_connection(self) -> bool:
        """Tests the connection to the USAJOBS API."""
        try:
            response = self.session.get(f"{self.base_url}/Search", params={'ResultsPerPage': 1}, timeout=15)
            if response.status_code == 200:
                logger.info("USAJOBS API connection successful.")
                return True
            else:
                logger.error(f"USAJOBS API connection failed with status {response.status_code}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"USAJOBS API connection failed: {e}")
            return False