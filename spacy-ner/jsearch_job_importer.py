import requests
import logging
import time
from typing import List, Dict, Any, Optional
from database import db
from embedding_service import ResumeJobEmbeddingService

logger = logging.getLogger(__name__)


class JSearchJobImporter:
    def __init__(self, rapidapi_key: str):
        # JSearch API via RapidAPI
        self.rapidapi_key = rapidapi_key
        self.base_url = "https://jsearch.p.rapidapi.com"

        self.session = requests.Session()
        self.session.headers.update({
            'X-RapidAPI-Key': self.rapidapi_key,
            'X-RapidAPI-Host': 'jsearch.p.rapidapi.com',
            'User-Agent': 'LandIt-JobMatcher/1.0'
        })

        # Initialize embedding service for job processing
        try:
            self.embedding_service = ResumeJobEmbeddingService()
            logger.info(" Embedding service ready for JSearch jobs")
        except Exception as e:
            logger.error(f" Embedding service failed: {e}")
            self.embedding_service = None

        self.stats = {
            'total_fetched': 0,
            'successfully_imported': 0,
            'failed_imports': 0,
            'duplicate_jobs': 0
        }

    def import_jobs(self, keywords: List[str] = None, max_jobs: int = 50, location: str = "United States"):
        """Import jobs from JSearch API with better error handling"""
        if keywords is None:
            keywords = [
                "software engineer",
                "data scientist",
                "product manager",
                "full stack developer",
                "machine learning engineer"
            ]

        logger.info(f" Starting JSearch job import for {len(keywords)} keywords...")

        jobs_per_keyword = max(10, max_jobs // len(keywords))

        for keyword in keywords:
            try:
                logger.info(f"Processing keyword: '{keyword}'")
                self._import_jobs_for_keyword(keyword, jobs_per_keyword, location)
                time.sleep(2)  # Rate limiting between keywords
            except Exception as e:
                logger.error(f" Failed to import jobs for '{keyword}': {e}")
                continue

        logger.info(f" JSearch import completed: {self.stats}")
        return self.stats

    def _import_jobs_for_keyword(self, keyword: str, max_per_keyword: int, location: str):
        """Import jobs for a specific keyword - skip entire keyword if rate limited"""
        page = 1
        jobs_imported = 0
        max_pages = 3  # Safety limit

        while jobs_imported < max_per_keyword and page <= max_pages:
            try:
                # Build API request parameters
                params = {
                    'query': f"{keyword} in {location}",
                    'page': str(page),
                    'num_pages': '1',
                    'date_posted': 'all',
                    'employment_types': 'FULLTIME,CONTRACTOR',
                    'job_requirements': 'under_3_years_experience,more_than_3_years_experience',
                    'country': 'us'
                }

                logger.info(f" Fetching JSearch jobs: '{keyword}' page {page}")

                response = self.session.get(f"{self.base_url}/search", params=params, timeout=30)

                # Debug logging
                logger.debug(f"Request URL: {response.url}")
                logger.debug(f"Response status: {response.status_code}")

                # Handle rate limiting - SKIP ENTIRE KEYWORD if rate limited
                if response.status_code == 429:
                    logger.warning(f"Rate limit hit for '{keyword}', skipping this keyword entirely")
                    break  # Break out of the while loop, skip to next keyword

                if response.status_code != 200:
                    logger.error(f"API Error {response.status_code}: {response.text[:500]}")
                    break  # Skip this keyword on any API error

                data = response.json()

                # Check for API errors
                if not data.get('status', '').lower() == 'ok':
                    logger.error(f"JSearch API Error: {data}")
                    break

                jobs = data.get('data', [])

                if not jobs:
                    logger.info(f"No more jobs found for '{keyword}' on page {page}")
                    break

                # Process each job
                page_jobs_processed = 0
                for job_data in jobs:
                    if jobs_imported >= max_per_keyword:
                        break

                    try:
                        if self._process_job(job_data, keyword):
                            jobs_imported += 1
                            page_jobs_processed += 1
                            self.stats['successfully_imported'] += 1
                        else:
                            self.stats['duplicate_jobs'] += 1
                    except Exception as e:
                        logger.error(f" Failed to process job: {e}")
                        self.stats['failed_imports'] += 1

                self.stats['total_fetched'] += len(jobs)

                logger.info(f"Page {page}: Processed {page_jobs_processed} jobs, total: {jobs_imported}")

                # JSearch typically returns 10 jobs per page
                if len(jobs) < 10:
                    break

                # Rate limiting between pages
                time.sleep(1)
                page += 1

            except requests.exceptions.RequestException as e:
                logger.error(f" API request failed for '{keyword}' page {page}: {e}")
                break  # Skip this keyword on network errors
            except Exception as e:
                logger.error(f" Unexpected error for '{keyword}' page {page}: {e}")
                break  # Skip this keyword on any other errors

        logger.info(f"Completed keyword '{keyword}': imported {jobs_imported} jobs")

    def test_api_connection(self):
        """Test API connection with minimal request"""
        try:
            params = {
                'query': 'software engineer in New York',
                'page': '1',
                'num_pages': '1',
                'country': 'us'
            }

            logger.info(f"Testing JSearch API connection...")
            response = self.session.get(f"{self.base_url}/search", params=params, timeout=30)

            logger.info(f"Test response status: {response.status_code}")

            if response.status_code == 401:
                logger.error(" Invalid RapidAPI key")
                return False
            elif response.status_code == 403:
                logger.error(" API access forbidden - check subscription")
                return False
            elif response.status_code != 200:
                logger.error(f"Test failed with status {response.status_code}")
                return False

            data = response.json()
            jobs_found = len(data.get('data', []))
            logger.info(f" Test successful! Found {jobs_found} jobs")
            return True

        except Exception as e:
            logger.error(f"API test failed: {e}")
            return False

    def _process_job(self, job_data: Dict[str, Any], search_keyword: str) -> bool:
        """Process and store a single job with better error handling"""
        try:
            # Extract job details from JSearch response
            job_dict = self._extract_job_details(job_data, search_keyword)

            # Check for duplicates (by title + company)
            if self._is_duplicate_job(job_dict['title'], job_dict['company']):
                logger.debug(f"Duplicate job: {job_dict['title']} at {job_dict['company']}")
                return False

            # Generate embeddings if service is available
            embeddings = {}
            if self.embedding_service:
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
                    logger.warning(f"Failed to generate embeddings for job: {e}")

            # Store in database
            job_id = db.store_job_posting(job_dict, embeddings)
            logger.info(f" Stored JSearch job: {job_dict['title']} at {job_dict['company']} (ID: {job_id})")

            return True

        except Exception as e:
            logger.error(f" Error processing job: {e}")
            return False

    def _extract_job_details(self, job_data: Dict[str, Any], search_keyword: str) -> Dict[str, Any]:
        """Extract and normalize job details from JSearch API response"""
        try:
            # Extract salary information with safe conversion
            salary_min = None
            salary_max = None
            try:
                if job_data.get('job_min_salary'):
                    salary_min = int(float(job_data['job_min_salary']))
                if job_data.get('job_max_salary'):
                    salary_max = int(float(job_data['job_max_salary']))
            except (ValueError, TypeError):
                logger.debug("Could not parse salary information")

            # Determine experience level from title/description
            experience_level = self._determine_experience_level(
                job_data.get('job_title', ''),
                job_data.get('job_description', '')
            )

            # Extract location
            location = self._format_location(job_data)

            # Extract skills from description
            skills_required = self._extract_skills_from_description(job_data.get('job_description', ''))

            # Get job type
            job_type = self._normalize_job_type(job_data.get('job_employment_type', ''))

            # Handle requirements and responsibilities - convert lists to strings
            requirements = job_data.get('job_highlights', {}).get('Qualifications', [])
            responsibilities = job_data.get('job_highlights', {}).get('Responsibilities', [])

            if isinstance(requirements, list):
                requirements = ' '.join(requirements)
            if isinstance(responsibilities, list):
                responsibilities = ' '.join(responsibilities)

            # FIXED: Ensure benefits is always an array
            benefits = job_data.get('job_benefits', [])
            if isinstance(benefits, str):
                benefits = [benefits]
            elif not isinstance(benefits, list):
                benefits = []

            # Ensure all required fields have safe defaults
            job_dict = {
                'title': job_data.get('job_title', '').strip() or 'Unknown Position',
                'company': job_data.get('employer_name', '').strip() or 'Unknown Company',
                'description': job_data.get('job_description', '') or '',
                'requirements': requirements or '',
                'responsibilities': responsibilities or '',
                'location': location,
                'remote_allowed': self._is_remote_job(job_data.get('job_description', '')),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'experience_level': experience_level,
                'job_type': job_type,
                'industry': search_keyword,
                'skills_required': skills_required,
                'skills_preferred': [],
                'education_required': '',
                'job_url': job_data.get('job_apply_link', ''),
                'source': 'jsearch',
                'external_job_id': str(job_data.get('job_id', '')),  # Use external_job_id not external_id
                'posted_date': job_data.get('job_posted_at_datetime_utc', ''),
                'category': job_data.get('job_publisher', ''),
                'benefits': benefits,  # FIXED: Now always an array
                'currency': 'USD',
                'company_size': None,
                'application_deadline': None
            }

            logger.debug(f"Extracted job: {job_dict['title']} at {job_dict['company']}")

            return job_dict

        except Exception as e:
            logger.error(f"Error extracting job details: {e}")
            logger.error(f"Problematic job data: {job_data}")
            raise

    def _determine_experience_level(self, title: str, description: str) -> str:
        """Determine experience level from job title and description"""
        text = (title + ' ' + description).lower()

        if any(word in text for word in ['senior', 'sr.', 'lead', 'principal', 'architect', 'staff']):
            return 'senior'
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'intern', 'graduate', 'trainee']):
            return 'entry'
        elif any(word in text for word in ['manager', 'director', 'head of', 'vp', 'chief']):
            return 'executive'
        else:
            return 'mid'

    def _format_location(self, job_data: Dict) -> str:
        """Format location from JSearch job data"""
        location_parts = []

        if job_data.get('job_city'):
            location_parts.append(job_data['job_city'])
        if job_data.get('job_state'):
            location_parts.append(job_data['job_state'])
        if job_data.get('job_country'):
            location_parts.append(job_data['job_country'])

        return ', '.join(location_parts) if location_parts else ''

    def _normalize_job_type(self, employment_type: str) -> str:
        """Normalize job type from JSearch format"""
        type_mapping = {
            'FULLTIME': 'full-time',
            'PARTTIME': 'part-time',
            'CONTRACTOR': 'contract',
            'INTERN': 'internship'
        }
        return type_mapping.get(employment_type.upper(), 'full-time')

    def _is_remote_job(self, description: str) -> bool:
        """Check if job allows remote work"""
        if not description:
            return False

        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'telecommute', 'virtual']
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in remote_keywords)

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract technical skills from job description using shared skill taxonomy."""
        from api import extract_skills_for_jobs
        return extract_skills_for_jobs(description, max_skills=20)

    def _is_duplicate_job(self, title: str, company: str) -> bool:
        """Check if job already exists in database"""
        try:
            existing_jobs = db.get_jobs_by_title_company(title, company)
            return len(existing_jobs) > 0
        except:
            return False

    def get_import_summary(self) -> Dict[str, Any]:
        """Get summary of import statistics"""
        return {
            'imported': self.stats['successfully_imported'],
            'total_fetched': self.stats['total_fetched'],
            'failed': self.stats['failed_imports'],
            'duplicates': self.stats['duplicate_jobs'],
            'source': 'jsearch'
        }