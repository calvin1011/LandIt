import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
import numpy as np
import os
from typing import Optional, List, Dict, Tuple
import logging
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection class with vector support for job matching system
    """

    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            # Database configuration using Supabase format
            db_config = {
                'user': os.getenv('user'),
                'password': os.getenv('password'),
                'host': os.getenv('host'),
                'port': int(os.getenv('port', 6543)),
                'dbname': os.getenv('dbname')
            }

            self.connection = psycopg2.connect(**db_config)
            self.connection.autocommit = True

            # Test vector extension
            cursor = self.get_cursor()
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            if cursor.fetchone():
                logger.info(" Database connection established with vector support")
            else:
                logger.warning(" Database connected but vector extension not found")

            cursor.close()

        except Exception as e:
            logger.error(f" Database connection failed: {e}")
            raise

    def get_cursor(self):
        """Get database cursor with dictionary results"""
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    # Vector utility methods

    def vector_to_db(self, vector: np.ndarray) -> str:
        """Convert numpy array to PostgreSQL vector format"""
        return '[' + ','.join(map(str, vector.tolist())) + ']'

    def db_to_vector(self, db_vector: str) -> np.ndarray:
        """Convert PostgreSQL vector format to numpy array"""
        if not db_vector:
            return np.array([])

        # Remove brackets and convert to numpy array
        vector_str = db_vector.strip('[]')
        return np.array([float(x) for x in vector_str.split(',')])

    # Resume operations

    def store_user_resume(self, user_email: str, resume_data: Dict,
                          embeddings: Dict[str, np.ndarray]) -> int:
        """
        Store user resume with embeddings

        Args:
            user_email: User's email
            resume_data: Structured resume data from your parser
            embeddings: Dict with keys: 'full_resume', 'skills', 'experience'

        Returns:
            Resume ID
        """
        try:
            cursor = self.get_cursor()

            # Prepare data
            resume_text = resume_data.get('resume_text', '')
            extracted_entities = json.dumps(resume_data.get('extracted_entities', []))
            structured_data = json.dumps(resume_data.get('structured_data', {}))
            resume_analytics = json.dumps(resume_data.get('resume_analytics', {}))

            # Extract metadata
            work_exp = resume_data.get('structured_data', {}).get('work_experience', [])
            years_of_experience = len(work_exp)  # Simple calculation

            current_job_title = ''
            if work_exp:
                current_job_title = work_exp[0].get('title', '')

            # Extract top skills
            skills_data = resume_data.get('structured_data', {}).get('skills', {})
            top_skills = []
            for category, skills_list in skills_data.items():
                for skill in skills_list[:3]:  # Top 3 per category
                    if isinstance(skill, dict):
                        top_skills.append(skill.get('name', ''))
                    else:
                        top_skills.append(str(skill))

            # Convert embeddings to database format
            full_resume_embedding = self.vector_to_db(embeddings.get('full_resume', np.array([])))
            skills_embedding = self.vector_to_db(embeddings.get('skills', np.array([])))
            experience_embedding = self.vector_to_db(embeddings.get('experience', np.array([])))

            # Insert or update resume
            query = """
                    INSERT INTO user_resumes (user_email, resume_text, extracted_entities, structured_data, \
                                              resume_analytics, full_resume_embedding, skills_embedding, \
                                              experience_embedding, years_of_experience, current_job_title, \
                                              top_skills, updated_at) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) ON CONFLICT (user_email) 
            DO \
                    UPDATE SET
                        resume_text = EXCLUDED.resume_text, \
                        extracted_entities = EXCLUDED.extracted_entities, \
                        structured_data = EXCLUDED.structured_data, \
                        resume_analytics = EXCLUDED.resume_analytics, \
                        full_resume_embedding = EXCLUDED.full_resume_embedding, \
                        skills_embedding = EXCLUDED.skills_embedding, \
                        experience_embedding = EXCLUDED.experience_embedding, \
                        years_of_experience = EXCLUDED.years_of_experience, \
                        current_job_title = EXCLUDED.current_job_title, \
                        top_skills = EXCLUDED.top_skills, \
                        updated_at = NOW() \
                        RETURNING id; \
                    """

            cursor.execute(query, (
                user_email, resume_text, extracted_entities, structured_data,
                resume_analytics, full_resume_embedding, skills_embedding,
                experience_embedding, years_of_experience, current_job_title,
                top_skills
            ))

            resume_id = cursor.fetchone()['id']
            cursor.close()

            logger.info(f" Stored resume for {user_email} (ID: {resume_id})")
            return resume_id

        except Exception as e:
            logger.error(f" Failed to store resume: {e}")
            raise

    def get_user_resume(self, user_email: str) -> Optional[Dict]:
        """Get user resume with embeddings"""
        try:
            cursor = self.get_cursor()

            query = """
                    SELECT * \
                    FROM user_resumes \
                    WHERE user_email = %s; \
                    """

            cursor.execute(query, (user_email,))
            result = cursor.fetchone()
            cursor.close()

            if not result:
                return None

            # Convert embeddings back to numpy arrays
            resume_data = dict(result)
            resume_data['full_resume_embedding'] = self.db_to_vector(result['full_resume_embedding'])
            resume_data['skills_embedding'] = self.db_to_vector(result['skills_embedding'])
            resume_data['experience_embedding'] = self.db_to_vector(result['experience_embedding'])

            return resume_data

        except Exception as e:
            logger.error(f" Failed to get resume: {e}")
            return None

    # Job operations

    def store_job_posting(self, job_data: Dict, embeddings: Dict[str, np.ndarray]) -> int:
        """Store job posting with embeddings - with better array handling"""
        try:
            cursor = self.get_cursor()

            # Convert embeddings
            description_embedding = self.vector_to_db(embeddings.get('description', np.array([])))
            requirements_embedding = self.vector_to_db(embeddings.get('requirements', np.array([])))
            title_embedding = self.vector_to_db(embeddings.get('title', np.array([])))

            # Ensure arrays are properly formatted
            def safe_parse_array(data, default=[]):
                """Safely parse data into a list, handling strings, JSON strings, and lists"""
                if data is None:
                    return default
                if isinstance(data, list):
                    return data
                if isinstance(data, str):
                    try:
                        # Try to parse as JSON array
                        parsed = json.loads(data)
                        if isinstance(parsed, list):
                            return parsed
                        else:
                            # If it's a single value in JSON, wrap in array
                            return [parsed]
                    except (json.JSONDecodeError, TypeError):
                        # If it's a plain string, treat as single-item array
                        return [data]
                # For any other type, try to convert to list
                try:
                    return list(data)
                except (TypeError, ValueError):
                    return [str(data)]

            # Apply safe parsing to all array fields
            benefits = safe_parse_array(job_data.get('benefits', []))
            skills_required = safe_parse_array(job_data.get('skills_required', []))
            skills_preferred = safe_parse_array(job_data.get('skills_preferred', []))

            query = """
                    INSERT INTO jobs (title, company, description, requirements, responsibilities, \
                                      location, remote_allowed, salary_min, salary_max, currency, \
                                      experience_level, job_type, industry, company_size, \
                                      benefits, skills_required, skills_preferred, education_required, \
                                      description_embedding, requirements_embedding, title_embedding, \
                                      source, job_url, posted_date, is_active, external_job_id) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, COALESCE(%s, 'USD'), \
                            %s, %s, %s, %s, %s, \
                            %s, %s, %s, \
                            %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                    """

            cursor.execute(query, (
                job_data.get('title'), job_data.get('company'), job_data.get('description'),
                job_data.get('requirements'), job_data.get('responsibilities'),
                job_data.get('location'), job_data.get('remote_allowed', False),
                job_data.get('salary_min'), job_data.get('salary_max'),
                job_data.get('currency'),  # Will use 'USD' if None
                job_data.get('experience_level'), job_data.get('job_type'),
                job_data.get('industry'), job_data.get('company_size'),
                benefits,  # Now properly formatted as array
                skills_required, skills_preferred,
                job_data.get('education_required'), description_embedding,
                requirements_embedding, title_embedding, job_data.get('source', 'manual'),
                job_data.get('job_url'), job_data.get('posted_date'), True,
                job_data.get('external_job_id')
            ))

            job_id = cursor.fetchone()['id']
            cursor.close()

            logger.info(f" Stored job posting: {job_data.get('title')} (ID: {job_id})")
            return job_id

        except Exception as e:
            logger.error(f" Failed to store job: {e}")
            logger.error(f" Job data: {job_data}")
            raise

    def get_all_jobs_with_embeddings(self) -> List[Dict]:
        """Get all active jobs with their embeddings"""
        try:
            cursor = self.get_cursor()

            query = """
                    SELECT id, \
                           title, \
                           company, \
                           description, \
                           requirements, \
                           location,
                           salary_min, \
                           salary_max, \
                           experience_level, \
                           skills_required,
                           remote_allowed, \
                           job_url, \
                           source,
                           description_embedding, \
                           requirements_embedding, \
                           title_embedding
                    FROM jobs
                    WHERE is_active = true
                      AND source NOT IN ('test', 'manual')
                      AND job_url IS NOT NULL
                    ORDER BY posted_date DESC; \
                    """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()

            # Convert embeddings back to numpy arrays
            jobs = []
            for result in results:
                job_data = dict(result)
                job_data['description_embedding'] = self.db_to_vector(result['description_embedding'])
                job_data['requirements_embedding'] = self.db_to_vector(result['requirements_embedding'])
                job_data['title_embedding'] = self.db_to_vector(result['title_embedding'])
                jobs.append(job_data)

            return jobs

        except Exception as e:
            logger.error(f" Failed to get jobs: {e}")
            return []

    # Recommendation operations

    def store_recommendation(self, user_email: str, job_id: int, scores: Dict,
                             match_reasons: Dict) -> int:
        """Store job recommendation with scores"""
        try:
            cursor = self.get_cursor()

            query = """
                    INSERT INTO job_recommendations (user_email, job_id, semantic_similarity_score, skills_match_score, \
                                                     experience_match_score, location_match_score, salary_match_score, \
                                                     overall_score, match_reasons, skill_matches, skill_gaps) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_email, job_id)
            DO \
                    UPDATE SET
                        semantic_similarity_score = EXCLUDED.semantic_similarity_score, \
                        skills_match_score = EXCLUDED.skills_match_score, \
                        experience_match_score = EXCLUDED.experience_match_score, \
                        location_match_score = EXCLUDED.location_match_score, \
                        salary_match_score = EXCLUDED.salary_match_score, \
                        overall_score = EXCLUDED.overall_score, \
                        match_reasons = EXCLUDED.match_reasons, \
                        skill_matches = EXCLUDED.skill_matches, \
                        skill_gaps = EXCLUDED.skill_gaps \
                        RETURNING id; \
                    """

            cursor.execute(query, (
                user_email, job_id, scores.get('semantic_similarity', 0.0),
                scores.get('skills_match', 0.0), scores.get('experience_match', 0.0),
                scores.get('location_match', 0.0), scores.get('salary_match', 0.0),
                scores.get('overall_score', 0.0), json.dumps(match_reasons),
                match_reasons.get('skill_matches', []), match_reasons.get('skill_gaps', [])
            ))

            rec_id = cursor.fetchone()['id']
            cursor.close()

            return rec_id

        except Exception as e:
            logger.error(f" Failed to store recommendation: {e}")
            raise

    def get_user_recommendations(self, user_email: str, limit: int = 10) -> List[Dict]:
        """Get user's job recommendations with job details"""
        try:
            cursor = self.get_cursor()

            query = """
                    SELECT jr.*, \
                           j.title, \
                           j.company, \
                           j.description, \
                           j.location, \
                           j.salary_min, \
                           j.salary_max, \
                           j.experience_level, \
                           j.job_type, \
                           j.skills_required, \
                           j.job_url
                    FROM job_recommendations jr
                             JOIN jobs j ON jr.job_id = j.id
                    WHERE jr.user_email = %s \
                      AND j.is_active = true
                    ORDER BY jr.overall_score DESC, jr.created_at DESC
                        LIMIT %s; \
                    """

            cursor.execute(query, (user_email, limit))
            results = cursor.fetchall()
            cursor.close()

            return [dict(result) for result in results]

        except Exception as e:
            logger.error(f" Failed to get recommendations: {e}")
            return []

    # Feedback operations

    def store_feedback(self, user_email: str, recommendation_id: int, feedback_data: Dict) -> int:
        """Store user feedback on job recommendation"""
        try:
            cursor = self.get_cursor()

            query = """
                    INSERT INTO recommendation_feedback (user_email, recommendation_id, job_id, overall_rating, \
                                                         skills_relevance_rating, experience_match_rating, \
                                                         location_rating, \
                                                         company_interest_rating, feedback_type, feedback_sentiment, \
                                                         feedback_text, improvement_suggestions, time_spent_viewing, \
                                                         clicked_apply_button, visited_company_page, shared_job, \
                                                         action_taken, application_status) \
                    VALUES (%s, %s, (SELECT job_id FROM job_recommendations WHERE id = %s), \
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id; \
                    """

            cursor.execute(query, (
                user_email, recommendation_id, recommendation_id,
                feedback_data.get('overall_rating'), feedback_data.get('skills_relevance_rating'),
                feedback_data.get('experience_match_rating'), feedback_data.get('location_rating'),
                feedback_data.get('company_interest_rating'), feedback_data.get('feedback_type'),
                feedback_data.get('feedback_sentiment'), feedback_data.get('feedback_text'),
                feedback_data.get('improvement_suggestions'), feedback_data.get('time_spent_viewing'),
                feedback_data.get('clicked_apply_button', False),
                feedback_data.get('visited_company_page', False),
                feedback_data.get('shared_job', False), feedback_data.get('action_taken'),
                feedback_data.get('application_status')
            ))

            feedback_id = cursor.fetchone()['id']
            cursor.close()

            logger.info(f" Stored feedback for recommendation {recommendation_id}")
            return feedback_id

        except Exception as e:
            logger.error(f" Failed to store feedback: {e}")
            raise

    def save_job(self, user_email: str, job_id: int) -> int:
        """Save a job for a user"""
        try:
            cursor = self.get_cursor()
            query = """
                    INSERT INTO saved_jobs (user_email, job_id)
                    VALUES (%s, %s) ON CONFLICT (user_email, job_id) DO NOTHING
                RETURNING id; \
                    """
            cursor.execute(query, (user_email, job_id))
            result = cursor.fetchone()
            cursor.close()
            return result['id'] if result else None
        except Exception as e:
            logger.error(f"Failed to save job: {e}")
            raise

    def get_saved_jobs(self, user_email: str) -> List[Dict]:
        """Get all jobs saved by a specific user"""
        try:
            cursor = self.get_cursor()
            query = """
                    SELECT j.*, sj.created_at as saved_at
                    FROM jobs j
                             JOIN saved_jobs sj ON j.id = sj.job_id
                    WHERE sj.user_email = %s
                    ORDER BY sj.created_at DESC; \
                    """
            cursor.execute(query, (user_email,))
            results = cursor.fetchall()
            cursor.close()
            return [dict(result) for result in results]
        except Exception as e:
            logger.error(f"Failed to get saved jobs: {e}")
            return []

    def record_application(self, user_email: str, job_id: int) -> Optional[int]:
        """Records a job application for a user."""
        try:
            cursor = self.get_cursor()
            query = """
                    INSERT INTO applications (user_email, job_id)
                    VALUES (%s, %s) ON CONFLICT (user_email, job_id) DO NOTHING
                RETURNING id; \
                    """
            cursor.execute(query, (user_email, job_id))
            result = cursor.fetchone()
            cursor.close()
            logger.info(f"Recorded application for user {user_email} to job {job_id}")
            return result['id'] if result else None
        except Exception as e:
            logger.error(f"Failed to record application: {e}")
            raise

    def get_feedback_analytics(self, days: int = 30) -> Dict:
        """Get feedback analytics for model improvement"""
        try:
            cursor = self.get_cursor()

            query = """
                    SELECT AVG(overall_rating)                                       as avg_rating, \
                           COUNT(*)                                                  as total_feedback, \
                           AVG(jr.semantic_similarity_score)                         as avg_semantic_score, \
                           AVG(jr.skills_match_score)                                as avg_skills_score, \
                           AVG(jr.experience_match_score)                            as avg_experience_score, \
                           COUNT(CASE WHEN rf.action_taken = 'applied' THEN 1 END)   as applications, \
                           COUNT(CASE WHEN rf.action_taken = 'saved' THEN 1 END)     as saves, \
                           COUNT(CASE WHEN rf.action_taken = 'dismissed' THEN 1 END) as dismissals
                    FROM recommendation_feedback rf
                             JOIN job_recommendations jr ON rf.recommendation_id = jr.id
                    WHERE rf.created_at > NOW() - INTERVAL '%s days'; \
                    """

            cursor.execute(query, (days,))
            result = cursor.fetchone()
            cursor.close()

            return dict(result) if result else {}

        except Exception as e:
            logger.error(f" Failed to get feedback analytics: {e}")
            return {}

    # Vector similarity search methods

    def find_similar_jobs_by_vector(self, query_embedding: np.ndarray,
                                    limit: int = 20, threshold: float = 0.3) -> List[Dict]:
        """
        Find similar jobs using vector similarity search

        Args:
            query_embedding: Resume embedding to match against
            limit: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of job matches with similarity scores
        """
        try:
            cursor = self.get_cursor()

            # Convert embedding to database format
            query_vector = self.vector_to_db(query_embedding)

            # Use cosine similarity for vector search
            # Note: This is a simple approach. For production, consider using pgvector indexes
            query = """
                    SELECT id, \
                           title, \
                           company, \
                           description, \
                           location,
                           salary_min, \
                           salary_max, \
                           experience_level, \
                           skills_required,
                           remote_allowed, \
                           job_url, \
                           source,
                           (1 - (description_embedding <=> %s::vector)) as similarity_score
                    FROM jobs
                    WHERE is_active = true
                      AND source NOT IN ('test', 'manual') 
                      AND job_url IS NOT NULL           
                      AND (1 - (description_embedding <=> %s::vector)) > %s
                    ORDER BY description_embedding <=> %s::vector
                        LIMIT %s; \
                    """

            cursor.execute(query, (query_vector, query_vector, threshold, query_vector, limit))
            results = cursor.fetchall()
            cursor.close()

            return [dict(result) for result in results]

        except Exception as e:
            logger.error(f" Vector similarity search failed: {e}")
            return []

    def bulk_update_recommendations_viewed(self, recommendation_ids: List[int]):
        """Mark multiple recommendations as viewed"""
        try:
            cursor = self.get_cursor()

            query = """
                    UPDATE job_recommendations
                    SET is_viewed = true, \
                        viewed_at = NOW()
                    WHERE id = ANY (%s); \
                    """

            cursor.execute(query, (recommendation_ids,))
            cursor.close()

        except Exception as e:
            logger.error(f" Failed to update viewed status: {e}")

    def get_jobs_by_title_company(self, title: str, company: str) -> List[Dict]:
        """Check for existing jobs by title and company"""
        query = """
                SELECT id \
                FROM jobs
                WHERE LOWER(title) = LOWER(%s) \
                  AND LOWER(company) = LOWER(%s) LIMIT 1 \
                """
        cursor = self.connection.cursor()
        cursor.execute(query, (title, company))
        return cursor.fetchall()

    def get_jobs_excluding_ids(self, exclude_ids: List[int]) -> List[Dict]:
        """Get all active jobs excluding specific job IDs"""
        try:
            cursor = self.get_cursor()

            if exclude_ids:
                query = """
                        SELECT id, \
                               title, \
                               company, \
                               description, \
                               requirements, \
                               location,
                               salary_min, \
                               salary_max, \
                               experience_level, \
                               skills_required,
                               description_embedding, \
                               requirements_embedding, \
                               title_embedding
                        FROM jobs
                        WHERE is_active = true \
                          AND id != ALL(%s)
                        ORDER BY posted_date DESC; \
                        """
                cursor.execute(query, (exclude_ids,))
            else:
                # If no exclusions, use existing method
                return self.get_all_jobs_with_embeddings()

            results = cursor.fetchall()
            cursor.close()

            jobs = []
            for result in results:
                job_data = dict(result)
                job_data['description_embedding'] = self.db_to_vector(result['description_embedding'])
                job_data['requirements_embedding'] = self.db_to_vector(result['requirements_embedding'])
                job_data['title_embedding'] = self.db_to_vector(result['title_embedding'])
                jobs.append(job_data)

            return jobs

        except Exception as e:
            logger.error(f"Failed to get jobs excluding IDs: {e}")
            return []

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get job data by ID"""
        try:
            cursor = self.get_cursor()
            query = "SELECT * FROM jobs WHERE id = %s AND is_active = true"
            cursor.execute(query, (job_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get job by ID: {e}")
            return None

    def store_learning_plan(self, user_email: str, job_id: int, recommendation_id: Optional[int],
                            learning_plan: Dict) -> int:
        """Store learning plan in database"""
        try:
            cursor = self.get_cursor()

            query = """
                    INSERT INTO learning_plans (user_email, job_id, recommendation_id, plan_data, created_at)
                    VALUES (%s, %s, %s, %s, NOW()) RETURNING id;
                    """

            cursor.execute(query, (
                user_email,
                job_id,
                recommendation_id,
                json.dumps(learning_plan)
            ))

            plan_id = cursor.fetchone()['id']
            cursor.close()

            logger.info(f" Stored learning plan for {user_email} (ID: {plan_id})")
            return plan_id

        except Exception as e:
            logger.error(f" Failed to store learning plan: {e}")
            raise

    def get_user_learning_plans(self, user_email: str, limit: int = 10) -> List[Dict]:
        """Get user's learning plans"""
        try:
            cursor = self.get_cursor()

            query = """
                    SELECT lp.*, j.title as job_title, j.company
                    FROM learning_plans lp
                             LEFT JOIN jobs j ON lp.job_id = j.id
                    WHERE lp.user_email = %s
                    ORDER BY lp.created_at DESC
                        LIMIT %s;
                    """

            cursor.execute(query, (user_email, limit))
            results = cursor.fetchall()
            cursor.close()

            # Parse JSON plan_data for each result
            plans = []
            for result in results:
                plan_dict = dict(result)
                if plan_dict.get('plan_data'):
                    try:
                        plan_dict['plan_data'] = json.loads(plan_dict['plan_data'])
                    except json.JSONDecodeError:
                        plan_dict['plan_data'] = {}
                plans.append(plan_dict)

            return plans

        except Exception as e:
            logger.error(f" Failed to get learning plans: {e}")
            return []

    def update_learning_progress(self, plan_id: int, progress_data: Dict) -> int:
        """Update progress on a learning plan"""
        try:
            cursor = self.get_cursor()

            query = """
                    INSERT INTO learning_progress (plan_id, progress_data, updated_at)
                    VALUES (%s, %s, NOW()) RETURNING id;
                    """

            cursor.execute(query, (plan_id, json.dumps(progress_data)))

            progress_id = cursor.fetchone()['id']
            cursor.close()

            return progress_id

        except Exception as e:
            logger.error(f" Failed to update learning progress: {e}")
            raise

    def deactivate_old_jobs(self, days_old: int = 30) -> int:
        """
        Deactivate jobs older than specified days

        Args:
            days_old: Jobs older than this many days will be deactivated

        Returns:
            Number of jobs deactivated
        """
        try:
            cursor = self.get_cursor()

            query = """
                    UPDATE jobs
                    SET is_active  = false,
                        updated_at = NOW()
                    WHERE is_active = true
                      AND posted_date < NOW() - INTERVAL '%s days'
                        RETURNING id; \
                    """

            cursor.execute(query, (days_old,))
            results = cursor.fetchall()
            count = len(results)
            cursor.close()

            logger.info(f"Deactivated {count} jobs older than {days_old} days")
            return count

        except Exception as e:
            logger.error(f"Failed to deactivate old jobs: {e}")
            return 0

    # Utility methods

    def test_connection(self) -> bool:
        """Test database connection and vector support"""
        try:
            cursor = self.get_cursor()

            # Test basic connection
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            logger.info(f"PostgreSQL Version: {version['version']}")

            # Test vector extension
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            vector_ext = cursor.fetchone()
            if vector_ext:
                logger.info(" pgvector extension is available")
            else:
                logger.error(" pgvector extension not found")
                return False

            # Test tables exist
            cursor.execute("""
                           SELECT table_name
                           FROM information_schema.tables
                           WHERE table_schema = 'public'
                           ORDER BY table_name;
                           """)
            tables = cursor.fetchall()
            logger.info(f"Found {len(tables)} tables")

            # Test vector columns
            cursor.execute("""
                           SELECT table_name, column_name
                           FROM information_schema.columns
                           WHERE data_type = 'USER-DEFINED'
                             AND udt_name = 'vector';
                           """)
            vector_columns = cursor.fetchall()
            logger.info(f"Found {len(vector_columns)} vector columns")

            cursor.close()
            return True

        except Exception as e:
            logger.error(f" Database test failed: {e}")
            return False


# Global database instance
db = DatabaseConnection()


# Test the database connection
def test_database_operations():
    """Test database operations with sample data"""
    logger.info(" Testing Database Operations")

    try:
        # Test connection
        if not db.test_connection():
            logger.error("Database connection test failed")
            return

        # Test sample data operations
        from embedding_service import ResumeJobEmbeddingService

        # Initialize embedding service
        embedding_service = ResumeJobEmbeddingService()

        # Sample resume data
        sample_resume_data = {
            "resume_text": "John Doe Software Engineer with Python experience",
            "structured_data": {
                "skills": {
                    "Programming": [{"name": "Python"}, {"name": "JavaScript"}]
                },
                "work_experience": [
                    {"title": "Software Engineer", "company": "Tech Corp"}
                ]
            },
            "extracted_entities": [
                {"text": "Python", "label": "SKILL"},
                {"text": "Software Engineer", "label": "TITLE"}
            ]
        }

        # Generate embeddings
        full_resume_embedding = embedding_service.generate_resume_embedding(sample_resume_data)
        skills_embedding = embedding_service.generate_skills_embedding(["Python", "JavaScript"])
        experience_embedding = np.random.rand(384)  # Mock experience embedding

        # Test storing resume
        resume_id = db.store_user_resume(
            "test@example.com",
            sample_resume_data,
            {
                'full_resume': full_resume_embedding,
                'skills': skills_embedding,
                'experience': experience_embedding
            }
        )

        logger.info(f" Stored test resume with ID: {resume_id}")

        # Test retrieving resume
        retrieved_resume = db.get_user_resume("test@example.com")
        if retrieved_resume:
            logger.info(" Successfully retrieved resume")
            logger.info(f"Resume embedding shape: {retrieved_resume['full_resume_embedding'].shape}")

        # Test sample job posting
        sample_job_data = {
            "title": "Python Developer",
            "company": "Example Corp",
            "description": "Looking for Python developer with web experience",
            "requirements": "3+ years Python, Django, PostgreSQL",
            "location": "San Francisco, CA",
            "skills_required": ["Python", "Django", "PostgreSQL"],
            "experience_level": "mid",
            "job_type": "full-time",
            "salary_min": 80000,
            "salary_max": 120000
        }

        # Generate job embeddings
        job_embedding = embedding_service.generate_job_embedding(sample_job_data)

        # Test storing job
        job_id = db.store_job_posting(
            sample_job_data,
            {
                'description': job_embedding,
                'requirements': job_embedding,
                'title': embedding_service.model.encode(sample_job_data['title'])
            }
        )

        logger.info(f" Stored test job with ID: {job_id}")

        # Test similarity search
        similar_jobs = db.find_similar_jobs_by_vector(full_resume_embedding, limit=5)
        logger.info(f" Found {len(similar_jobs)} similar jobs")

        if similar_jobs:
            for job in similar_jobs:
                logger.info(f"   - {job['title']} at {job['company']} (similarity: {job['similarity_score']:.3f})")

        logger.info(" Database operations test completed successfully!")

    except Exception as e:
        logger.error(f" Database operations test failed: {e}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run test
    test_database_operations()