import requests
import logging
import time
from typing import List, Dict, Any, Optional
from database import db
from embedding_service import ResumeJobEmbeddingService

logger = logging.getLogger(__name__)


class AdzunaJobImporter:
    def __init__(self):
        # Your Adzuna API credentials
        self.app_id = "091309e2"
        self.app_key = "dc9d659bbbb55ce320190bf9954f8f06"
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search"

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CalTech-JobMatcher/1.0'
        })

        # Initialize embedding service for job processing
        try:
            self.embedding_service = ResumeJobEmbeddingService()
            logger.info(" Embedding service ready for Adzuna jobs")
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
        """
        Import jobs from Adzuna API
        """
        if not self.embedding_service:
            logger.error("Embedding service not available. Aborting import.")
            return

        if keywords is None:
            keywords = [
                'Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer',
                'DevOps Engineer', 'Cybersecurity Analyst', 'Cloud Engineer'
            ]

        logger.info(f"=== Starting Adzuna Job Import for keywords: {', '.join(keywords)} ===")

        for keyword in keywords:
            logger.info(f" Fetching jobs for '{keyword}' in {location}")
            try:
                # Fetch job data from API
                fetched_jobs = self._fetch_jobs_from_api(keyword, location)
                if not fetched_jobs:
                    logger.warning(f" No jobs found for '{keyword}'")
                    continue

                self.stats['total_fetched'] += len(fetched_jobs)
                jobs_to_process = fetched_jobs[:max_jobs]
                logger.info(f" Processing {len(jobs_to_process)} jobs for '{keyword}'")

                # Process and store each job
                for job in jobs_to_process:
                    try:
                        # Normalize and enrich job data
                        job_data = self._normalize_job_data(job)
                        if not job_data or self._is_duplicate_job(job_data['title'], job_data['company']):
                            if job_data: self.stats['duplicate_jobs'] += 1
                            continue

                        # Generate embeddings
                        description_text = job_data.get('description', '')
                        description_embedding = self.embedding_service.generate_embedding(description_text)

                        # --- START: THIS IS THE NEW CODE ---
                        # Generate skills embedding from the required skills list
                        skills_list = job_data.get('skills_required', [])
                        skills_embedding = None
                        if skills_list:
                            # Join the list of skills into a single string for embedding
                            skills_text = ". ".join(skills_list)
                            skills_embedding = self.embedding_service.generate_embedding(skills_text)
                        # --- END: NEW CODE ---

                        # Store job posting with the new skills_embedding
                        job_id = db.store_job_posting(
                            job_data,
                            {
                                'description': description_embedding,
                                'requirements': description_embedding,  # Adzuna doesn't separate these well
                                'skills_embedding': skills_embedding  # Add the new embedding here
                            }
                        )

                        if job_id:
                            self.stats['successfully_imported'] += 1
                        else:
                            self.stats['failed_imports'] += 1

                    except Exception as e:
                        logger.error(f" Error processing Adzuna job {job.get('id')}: {e}")
                        self.stats['failed_imports'] += 1

                time.sleep(1)  # Respectful delay between keywords

            except Exception as e:
                logger.error(f" Failed to fetch or process jobs for '{keyword}': {e}")

        logger.info("=== Adzuna Job Import Finished ===")

    def _import_jobs_for_keyword(self, keyword: str, max_per_keyword: int, location: str):
        """Import jobs for a specific keyword with safety limits"""
        page = 1
        jobs_imported = 0
        max_pages = 5  # SAFETY LIMIT: Don't fetch more than 5 pages per keyword
        consecutive_empty_pages = 0

        logger.info(f"Importing up to {max_per_keyword} jobs for '{keyword}' (max {max_pages} pages)")

        while jobs_imported < max_per_keyword and page <= max_pages:
            try:
                # Calculate how many more jobs we need
                jobs_needed = max_per_keyword - jobs_imported
                results_per_page = min(20, jobs_needed)  # Don't fetch more than needed

                # Build API request
                params = {
                    'app_id': self.app_id,
                    'app_key': self.app_key,
                    'results_per_page': results_per_page,
                    'what': keyword,
                    'where': location,
                    'sort_by': 'date',
                    'content-type': 'application/json'
                }

                logger.info(f" Fetching Adzuna jobs: '{keyword}' page {page} (need {jobs_needed} more)")

                # FIXED URL - page number goes in the URL path
                url = f"{self.base_url}/{page}"

                # Make request with timeout
                response = self.session.get(url, params=params, timeout=30)

                # Debug logging
                logger.debug(f"Request URL: {response.url}")
                logger.debug(f"Response status: {response.status_code}")

                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limit hit, waiting 60 seconds...")
                    time.sleep(60)
                    continue  # Retry the same page

                if response.status_code == 400:
                    logger.error(f"Bad Request (400) for keyword '{keyword}' page {page}")
                    logger.error(f"Response text: {response.text[:500]}")
                    break

                response.raise_for_status()
                data = response.json()

                # Check for API errors in response
                if 'error' in data:
                    logger.error(f"API Error: {data['error']}")
                    break

                jobs = data.get('results', [])

                if not jobs:
                    consecutive_empty_pages += 1
                    logger.info(f"No jobs found for '{keyword}' on page {page}")

                    # If we get 2 consecutive empty pages, stop
                    if consecutive_empty_pages >= 2:
                        logger.info(f"Stopping after {consecutive_empty_pages} consecutive empty pages")
                        break
                else:
                    consecutive_empty_pages = 0  # Reset counter
                    logger.info(f"Page {page}: Found {len(jobs)} jobs")

                # Process each job
                page_jobs_processed = 0
                for job_data in jobs:
                    if jobs_imported >= max_per_keyword:
                        logger.info(f"Reached max jobs per keyword ({max_per_keyword})")
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

                logger.info(
                    f"Page {page} completed: processed {page_jobs_processed} jobs, total imported: {jobs_imported}")

                # Safety check: if we processed 0 jobs on this page, stop
                if page_jobs_processed == 0 and len(jobs) == 0:
                    logger.info(f"No jobs processed on page {page}, stopping")
                    break

                page += 1

                # Rate limiting between pages
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                logger.error(f" API request failed for '{keyword}' page {page}: {e}")
                # Log response details if available
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text[:500]}")
                break
            except Exception as e:
                logger.error(f" Unexpected error for '{keyword}' page {page}: {e}")
                break

        logger.info(f"Completed '{keyword}': imported {jobs_imported} jobs over {page - 1} pages")

    def test_api_connection(self):
        """Test API connection with minimal request"""
        try:
            params = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'results_per_page': 1,
                'what': 'software',
                'where': 'New York',
                'content-type': 'application/json'
            }

            url = f"{self.base_url}/1"
            logger.info(f"Testing API connection: {url}")
            logger.info(f"Params: {params}")

            response = self.session.get(url, params=params, timeout=30)

            logger.info(f"Test response status: {response.status_code}")
            logger.info(f"Test response URL: {response.url}")

            if response.status_code != 200:
                logger.error(f"Test failed with status {response.status_code}")
                logger.error(f"Response: {response.text[:1000]}")
                return False

            data = response.json()
            logger.info(f"Test successful! Found {len(data.get('results', []))} jobs")
            return True

        except Exception as e:
            logger.error(f"API test failed: {e}")
            return False

    def _process_job(self, job_data: Dict[str, Any], search_keyword: str) -> bool:
        """Process and store a single job"""
        try:
            # Extract job details from Adzuna response
            job_dict = self._extract_job_details(job_data, search_keyword)

            # Check for duplicates (by title + company)
            if self._is_duplicate_job(job_dict['title'], job_dict['company']):
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
            logger.debug(f" Stored Adzuna job: {job_dict['title']} at {job_dict['company']}")

            return True

        except Exception as e:
            logger.error(f" Error processing job: {e}")
            raise

    def _extract_job_details(self, job_data: Dict[str, Any], search_keyword: str) -> Dict[str, Any]:
        """Extract and normalize job details from Adzuna API response"""

        # Extract salary information
        salary_min = None
        salary_max = None
        if job_data.get('salary_min'):
            salary_min = int(job_data['salary_min'])
        if job_data.get('salary_max'):
            salary_max = int(job_data['salary_max'])

        # Determine experience level from title/description
        experience_level = self._determine_experience_level(
            job_data.get('title', ''),
            job_data.get('description', '')
        )

        # Extract location
        location = self._format_location(job_data.get('location', {}))

        # Extract skills from description
        skills_required = self._extract_skills_from_description(job_data.get('description', ''))

        return {
            'title': job_data.get('title', '').strip(),
            'company': job_data.get('company', {}).get('display_name', 'Unknown Company'),
            'description': job_data.get('description', ''),
            'requirements': job_data.get('description', ''),  # Adzuna combines these
            'responsibilities': '',
            'location': location,
            'remote_allowed': self._is_remote_job(job_data.get('description', '')),
            'salary_min': salary_min,
            'salary_max': salary_max,
            'experience_level': experience_level,
            'job_type': 'full-time',  # Adzuna doesn't always specify
            'industry': search_keyword,
            'skills_required': skills_required,
            'skills_preferred': [],
            'education_required': '',
            'job_url': job_data.get('redirect_url', ''),  # This is the key advantage of Adzuna!
            'source': 'adzuna',
            'external_id': str(job_data.get('id', '')),
            'posted_date': job_data.get('created', ''),
            'category': job_data.get('category', {}).get('label', '')
        }

    def _determine_experience_level(self, title: str, description: str) -> str:
        """Determine experience level from job title and description"""
        text = (title + ' ' + description).lower()

        if any(word in text for word in ['senior', 'sr.', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in text for word in ['junior', 'jr.', 'entry', 'intern', 'graduate', 'trainee']):
            return 'entry'
        elif any(word in text for word in ['manager', 'director', 'head of', 'vp', 'chief']):
            return 'executive'
        else:
            return 'mid'

    def _format_location(self, location_data: Dict) -> str:
        """Format location from Adzuna location object"""
        if not location_data:
            return ''

        parts = []
        if location_data.get('display_name'):
            return location_data['display_name']

        if location_data.get('area'):
            parts.extend(location_data['area'])

        return ', '.join(parts) if parts else ''

    def _is_remote_job(self, description: str) -> bool:
        """Check if job allows remote work"""
        remote_keywords = ['remote', 'work from home', 'wfh', 'distributed', 'telecommute']
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in remote_keywords)

    def _extract_skills_from_description(self, description: str) -> List[str]:
        """Extract technical skills from job description"""
        # Common tech skills to look for
        tech_skills = [
            'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws', 'docker',
            'kubernetes', 'git', 'linux', 'mongodb', 'postgresql', 'redis', 'elasticsearch',
            'machine learning', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
            'html', 'css', 'vue.js', 'angular', 'typescript', 'go', 'rust', 'c++', 'c#',
            'azure', 'gcp', 'terraform', 'jenkins', 'ci/cd', 'agile', 'scrum'
        ]

        description_lower = description.lower()
        found_skills = []

        for skill in tech_skills:
            if skill.lower() in description_lower:
                found_skills.append(skill)

        return found_skills[:10]  # Limit to top 10 skills

    def _is_duplicate_job(self, title: str, company: str) -> bool:
        """Check if job already exists in database"""
        try:
            # Simple check - you might want to make this more sophisticated
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
            'source': 'adzuna'
        }