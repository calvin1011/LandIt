import requests
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from database import db
from embedding_service import ResumeJobEmbeddingService

logger = logging.getLogger(__name__)


class MuseJobImporter:
    """
    Import real job data from The Muse API (free, no API key required)
    """

    def __init__(self):
        self.embedding_service = ResumeJobEmbeddingService()
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.base_url = "https://www.themuse.com/api/public/jobs"

    def import_jobs(self, categories: List[str] = None, locations: List[str] = None, max_jobs: int = 100):
        """
        Import jobs from The Muse API

        Args:
            categories: List of job categories (e.g., ['Software Engineer', 'Data Science'])
            locations: List of locations (e.g., ['San Francisco', 'New York', 'Remote'])
            max_jobs: Maximum number of jobs to import per category
        """
        if categories is None:
            categories = [
                'Software Engineer',
                'Data Science',
                'Product Management',
                'Engineering',
                'Design',
                'Marketing'
            ]

        logger.info(f" Starting The Muse import for {len(categories)} categories")

        for category in categories:
            try:
                logger.info(f" Importing jobs for category: {category}")
                self._import_category(category, locations, max_jobs)
                time.sleep(1)  # Rate limiting - be nice to the API

            except Exception as e:
                logger.error(f" Error importing category '{category}': {e}")
                self.error_count += 1

    def _import_category(self, category: str, locations: List[str] = None, max_jobs: int = 100):
        """Import jobs for a specific category"""
        page = 0
        jobs_imported_for_category = 0

        while jobs_imported_for_category < max_jobs:
            try:
                params = {
                    'category': category,
                    'page_size': 20,  # Max 20 per request
                    'page': page
                }

                # Add location filter if specified
                if locations:
                    params['location'] = locations[0]  # Use first location for now

                response = requests.get(self.base_url, params=params, timeout=10)

                if response.status_code != 200:
                    logger.error(f"API error for {category}: {response.status_code}")
                    break

                data = response.json()
                jobs = data.get('results', [])

                if not jobs:
                    logger.info(f"No more jobs found for {category} on page {page}")
                    break

                logger.info(f" Found {len(jobs)} jobs for '{category}' (page {page})")

                for job in jobs:
                    if jobs_imported_for_category >= max_jobs:
                        break

                    try:
                        if self._process_job(job):
                            jobs_imported_for_category += 1
                        time.sleep(0.1)  # Small delay between processing jobs

                    except Exception as e:
                        logger.error(f" Error processing job: {e}")
                        self.error_count += 1

                page += 1

            except Exception as e:
                logger.error(f" Error fetching page {page} for {category}: {e}")
                break

    def _process_job(self, job: Dict) -> bool:
        """Process and store a single job"""
        try:
            # Skip if we already have this job (check by title + company)
            title = job.get('name', '').strip()
            company_info = job.get('company', {})
            company = company_info.get('name', '').strip()

            if not title or not company:
                self.skipped_count += 1
                return False

            # Check if job already exists in database
            if self._job_exists(title, company):
                logger.debug(f"Job already exists: {title} at {company}")
                self.skipped_count += 1
                return False

            # Parse job data
            job_data = self._parse_muse_job(job)

            if job_data:
                self._store_job(job_data)
                return True
            else:
                self.skipped_count += 1
                return False

        except Exception as e:
            logger.error(f"Error processing job: {e}")
            self.error_count += 1
            return False

    def _parse_muse_job(self, job: Dict) -> Optional[Dict]:
        """Parse The Muse job data into our format"""
        try:
            # Basic job info
            title = job.get('name', '').strip()
            company_info = job.get('company', {})
            company = company_info.get('name', '').strip()

            # Job content and description
            contents = job.get('contents', '')
            if not contents:
                return None

            # Clean HTML from contents
            description = self._clean_html(contents)

            # Extract skills from job description
            skills = self._extract_skills_from_text(description)

            # Get location info
            locations = job.get('locations', [])
            location = ''
            remote_allowed = False

            if locations:
                location_names = []
                for loc in locations:
                    loc_name = loc.get('name', '')
                    if loc_name:
                        location_names.append(loc_name)
                        if 'remote' in loc_name.lower() or 'flexible' in loc_name.lower():
                            remote_allowed = True

                location = ', '.join(location_names[:2])  # Limit to 2 locations

            # Determine job type and experience level from description
            job_type = self._determine_job_type(description)
            experience_level = self._determine_experience_level(description)

            # Extract industry from company info
            industry = ''
            if 'industry' in company_info:
                industry = company_info.get('industry', '')

            # Get job URL
            job_url = job.get('refs', {}).get('landing_page', '')

            return {
                'title': title,
                'company': company,
                'description': description[:2000],  # Limit description length
                'requirements': self._extract_requirements(description),
                'responsibilities': self._extract_responsibilities(description),
                'location': location,
                'remote_allowed': remote_allowed,
                'salary_min': None,  # The Muse doesn't provide salary info
                'salary_max': None,
                'experience_level': experience_level,
                'job_type': job_type,
                'industry': industry,
                'skills_required': skills,
                'skills_preferred': [],
                'education_required': self._extract_education_requirements(description),
                'source': 'themuse',
                'job_url': job_url,
                'posted_date': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error parsing Muse job: {e}")
            return None

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract common tech skills from job description"""
        if not text:
            return []

        text_lower = text.lower()

        # Comprehensive list of tech skills to look for
        tech_skills = [
            # Programming Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
            'kotlin', 'typescript', 'scala', 'r', 'matlab', 'sql', 'html', 'css',

            # Frontend Frameworks/Libraries
            'react', 'angular', 'vue', 'svelte', 'jquery', 'bootstrap', 'tailwind',

            # Backend Frameworks
            'node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'rails',
            'fastapi', 'asp.net', 'nestjs',

            # Cloud Platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',

            # DevOps & Tools
            'docker', 'kubernetes', 'terraform', 'jenkins', 'gitlab', 'github',
            'ansible', 'puppet', 'chef',

            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            'dynamodb', 'sqlite', 'oracle',

            # Data Science & ML
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
            'tableau', 'power bi', 'spark', 'hadoop',

            # Mobile Development
            'ios', 'android', 'react native', 'flutter', 'xamarin',

            # Other Tools
            'git', 'jira', 'confluence', 'slack', 'figma', 'sketch', 'photoshop',
            'linux', 'unix', 'bash', 'powershell'
        ]

        found_skills = []
        for skill in tech_skills:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                # Capitalize properly
                if skill == 'node.js':
                    found_skills.append('Node.js')
                elif skill == 'c++':
                    found_skills.append('C++')
                elif skill == 'c#':
                    found_skills.append('C#')
                elif skill == 'asp.net':
                    found_skills.append('ASP.NET')
                else:
                    found_skills.append(skill.title())

        return list(set(found_skills))[:15]  # Limit to top 15 skills

    def _determine_experience_level(self, description: str) -> str:
        """Determine experience level from job description"""
        desc_lower = description.lower()

        # Senior level indicators
        senior_terms = ['senior', 'lead', 'principal', 'staff', 'architect',
                        '5+ years', '6+ years', '7+ years', '8+ years', '10+ years',
                        'leadership', 'mentor', 'team lead']

        # Entry level indicators
        entry_terms = ['junior', 'entry', 'graduate', 'intern', 'new grad',
                       '0-2 years', '1-2 years', 'recent graduate', 'bootcamp']

        # Count occurrences
        senior_count = sum(1 for term in senior_terms if term in desc_lower)
        entry_count = sum(1 for term in entry_terms if term in desc_lower)

        if senior_count > entry_count and senior_count > 0:
            return 'senior'
        elif entry_count > 0:
            return 'entry'
        else:
            return 'mid'

    def _determine_job_type(self, description: str) -> str:
        """Determine job type from description"""
        desc_lower = description.lower()

        if any(term in desc_lower for term in ['contract', 'contractor', 'freelance', 'consulting']):
            return 'contract'
        elif any(term in desc_lower for term in ['part-time', 'part time', 'parttime']):
            return 'part-time'
        elif any(term in desc_lower for term in ['intern', 'internship']):
            return 'internship'
        else:
            return 'full-time'

    def _extract_requirements(self, description: str) -> str:
        """Extract requirements section from job description"""
        # Look for common requirements section headers
        patterns = [
            r'requirements?:?\s*(.*?)(?=responsibilities?:|qualifications?:|experience?:|$)',
            r'qualifications?:?\s*(.*?)(?=responsibilities?:|requirements?:|experience?:|$)',
            r'you have:?\s*(.*?)(?=responsibilities?:|requirements?:|we offer:|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                requirements = match.group(1).strip()
                if len(requirements) > 50:  # Only return if substantial
                    return requirements[:500]  # Limit length

        return ''

    def _extract_responsibilities(self, description: str) -> str:
        """Extract responsibilities section from job description"""
        patterns = [
            r'responsibilities?:?\s*(.*?)(?=requirements?:|qualifications?:|benefits?:|$)',
            r'you will:?\s*(.*?)(?=requirements?:|qualifications?:|benefits?:|$)',
            r'role:?\s*(.*?)(?=requirements?:|qualifications?:|benefits?:|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                responsibilities = match.group(1).strip()
                if len(responsibilities) > 50:
                    return responsibilities[:500]

        return ''

    def _extract_education_requirements(self, description: str) -> str:
        """Extract education requirements from job description"""
        desc_lower = description.lower()

        education_terms = [
            "bachelor's degree", "master's degree", "phd", "doctorate",
            "computer science", "engineering", "mathematics", "statistics",
            "degree in", "bs in", "ms in", "ba in", "ma in"
        ]

        for term in education_terms:
            if term in desc_lower:
                # Try to extract the sentence containing the education requirement
                sentences = description.split('.')
                for sentence in sentences:
                    if term in sentence.lower():
                        return sentence.strip()[:200]

        return ''

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        if not text:
            return ''

        # Remove HTML tags
        clean_text = re.sub(r'<[^<]+?>', '', text)

        # Remove extra whitespace and normalize
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'\n+', '\n', clean_text)

        return clean_text.strip()

    def _job_exists(self, title: str, company: str) -> bool:
        """Check if job already exists in database (simple implementation)"""
        # This is a simplified check - you might want to implement a more sophisticated
        # duplicate detection system
        try:
            # For now, we'll assume jobs don't exist and let the database handle duplicates
            return False
        except Exception:
            return False

    def _store_job(self, job_data: Dict):
        """Store job in database with embeddings"""
        try:
            # Generate embeddings
            description_embedding = self.embedding_service.generate_job_embedding(job_data)
            title_embedding = self.embedding_service.model.encode(job_data['title'])
            requirements_text = job_data.get('requirements', job_data['description'][:500])
            requirements_embedding = self.embedding_service.model.encode(requirements_text)

            # Store in database
            job_id = db.store_job_posting(
                job_data,
                {
                    'description': description_embedding,
                    'title': title_embedding,
                    'requirements': requirements_embedding
                }
            )

            self.imported_count += 1
            logger.info(f" Imported: {job_data['title']} at {job_data['company']} (ID: {job_id})")

        except Exception as e:
            logger.error(f" Failed to store job '{job_data.get('title', 'Unknown')}': {e}")
            self.error_count += 1

    def get_import_summary(self) -> Dict:
        """Get summary of import results"""
        total_processed = self.imported_count + self.skipped_count + self.error_count

        return {
            'imported': self.imported_count,
            'skipped': self.skipped_count,
            'errors': self.error_count,
            'total_processed': total_processed,
            'success_rate': (self.imported_count / total_processed * 100) if total_processed > 0 else 0
        }

    def reset_counters(self):
        """Reset import counters"""
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0


# Main function to run the importer
def main():
    """Main function to run The Muse job import"""
    logging.basicConfig(level=logging.INFO)

    importer = MuseJobImporter()

    print(" Starting The Muse job import...")
    print(" No API key required - using public API")

    # Define categories to import
    categories = [
        'Software Engineer',
        'Data Science',
        'Product Management',
        'Engineering',
        'Design',
        'Marketing',
        'Sales'
    ]

    # Optional: specify locations
    locations = ['San Francisco', 'New York', 'Remote', 'Los Angeles', 'Seattle']

    try:
        # Import jobs
        importer.import_jobs(
            categories=categories,
            locations=locations,
            max_jobs=20  # Import up to 20 jobs per category
        )

        # Print summary
        summary = importer.get_import_summary()
        print(f"\n Import Summary:")
        print(f"    Imported: {summary['imported']}")
        print(f"     Skipped: {summary['skipped']}")
        print(f"    Errors: {summary['errors']}")
        print(f"    Total Processed: {summary['total_processed']}")
        print(f"    Success Rate: {summary['success_rate']:.1f}%")

        if summary['imported'] > 0:
            print(f"\n Successfully imported {summary['imported']} real jobs from The Muse!")
            print(" Your resume builder now has real job opportunities!")
        else:
            print(f"\n No jobs were imported. Check the logs for details.")

    except Exception as e:
        logger.error(f" Import failed: {e}")
        print(f"\n Import failed: {e}")


if __name__ == "__main__":
    main()