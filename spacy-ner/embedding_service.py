import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional, Tuple
import logging
import json
import re
from sklearn.metrics.pairwise import cosine_similarity
import torch

logger = logging.getLogger(__name__)


class ResumeJobEmbeddingService:
    """
    Advanced embedding service for resume and job matching using sentence transformers
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service

        Args:
            model_name: Sentence transformer model to use
                       Options: 'all-MiniLM-L6-v2' (fast, 384 dim)
                               'all-mpnet-base-v2' (better quality, 768 dim)
        """
        self.model_name = model_name
        self.embedding_dim = 384 if "MiniLM" in model_name else 768

        try:
            logger.info(f"Loading sentence transformer model: {model_name}")
            self.model = SentenceTransformer(model_name)

            # Set device (GPU if available)
            if torch.cuda.is_available():
                self.model = self.model.cuda()
                logger.info(" Using GPU for embeddings")
            else:
                logger.info(" Using CPU for embeddings")

            logger.info(f" Embedding service initialized with {self.embedding_dim}D vectors")

        except Exception as e:
            logger.error(f" Failed to load embedding model: {e}")
            raise

    def generate_resume_embedding(self, resume_data: Dict) -> np.ndarray:
        """
        Generate comprehensive embedding from structured resume data

        Args:
            resume_data: Structured resume data from your existing parser

        Returns:
            numpy array of embedding vector
        """
        try:
            # Extract and weight different resume components
            text_components = []

            # 1. Skills (highest weight - most important for matching)
            skills_text = self._extract_skills_text(resume_data)
            if skills_text:
                text_components.extend([skills_text] * 3)  # 3x weight

            # 2. Work experience (high weight)
            experience_text = self._extract_experience_text(resume_data)
            if experience_text:
                text_components.extend([experience_text] * 2)  # 2x weight

            # 3. Job titles and roles (high weight)
            titles_text = self._extract_titles_text(resume_data)
            if titles_text:
                text_components.extend([titles_text] * 2)  # 2x weight

            # 4. Education (moderate weight)
            education_text = self._extract_education_text(resume_data)
            if education_text:
                text_components.append(education_text)

            # 5. Achievements (moderate weight)
            achievements_text = self._extract_achievements_text(resume_data)
            if achievements_text:
                text_components.append(achievements_text)

            # Combine all components
            if not text_components:
                # Fallback to raw resume text if structured data is incomplete
                combined_text = resume_data.get('resume_text', '')[:2000]  # Limit length
            else:
                combined_text = " ".join(text_components)

            # Generate embedding
            embedding = self.model.encode(combined_text, convert_to_numpy=True)

            logger.debug(f"Generated resume embedding: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate resume embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)

    def generate_job_embedding(self, job_data: Dict) -> np.ndarray:
        """
        Generate embedding from job posting data

        Args:
            job_data: Job posting data (title, description, requirements, etc.)

        Returns:
            numpy array of embedding vector
        """
        try:
            text_components = []

            # 1. Job title (high weight)
            title = job_data.get('title', '')
            if title:
                text_components.extend([title] * 2)  # 2x weight

            # 2. Required skills (highest weight)
            skills = job_data.get('skills_required', [])
            if skills:
                skills_text = " ".join(skills)
                text_components.extend([skills_text] * 3)  # 3x weight

            # 3. Job requirements (high weight)
            requirements = job_data.get('requirements', '')
            if requirements:
                text_components.extend([requirements] * 2)  # 2x weight

            # 4. Job description (standard weight)
            description = job_data.get('description', '')
            if description:
                # Limit description length to avoid overwhelming other components
                description_truncated = description[:1000]
                text_components.append(description_truncated)

            # 5. Responsibilities (standard weight)
            responsibilities = job_data.get('responsibilities', '')
            if responsibilities:
                text_components.append(responsibilities[:500])

            # Combine all components
            combined_text = " ".join(text_components)

            # Generate embedding
            embedding = self.model.encode(combined_text, convert_to_numpy=True)

            logger.debug(f"Generated job embedding: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate job embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dim)

    def generate_skills_embedding(self, skills_data: List[str]) -> np.ndarray:
        """
        Generate specialized embedding focused only on skills

        Args:
            skills_data: List of skills

        Returns:
            numpy array of embedding vector
        """
        try:
            if not skills_data:
                return np.zeros(self.embedding_dim)

            # Clean and combine skills
            clean_skills = [skill.strip().lower() for skill in skills_data if skill.strip()]
            skills_text = " ".join(clean_skills)

            embedding = self.model.encode(skills_text, convert_to_numpy=True)
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate skills embedding: {e}")
            return np.zeros(self.embedding_dim)

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Handle zero vectors
            if np.allclose(embedding1, 0) or np.allclose(embedding2, 0):
                return 0.0

            # Calculate cosine similarity
            similarity = cosine_similarity([embedding1], [embedding2])[0][0]

            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0

    def batch_calculate_similarities(self, query_embedding: np.ndarray,
                                     target_embeddings: List[np.ndarray]) -> List[float]:
        """
        Calculate similarities between one query and multiple targets efficiently

        Args:
            query_embedding: Single query embedding
            target_embeddings: List of target embeddings

        Returns:
            List of similarity scores
        """
        try:
            if not target_embeddings:
                return []

            # Stack embeddings for batch processing
            target_matrix = np.vstack(target_embeddings)

            # Calculate similarities in batch
            similarities = cosine_similarity([query_embedding], target_matrix)[0]

            # Ensure all scores are between 0 and 1
            similarities = np.clip(similarities, 0.0, 1.0)

            return similarities.tolist()

        except Exception as e:
            logger.error(f"Failed to calculate batch similarities: {e}")
            return [0.0] * len(target_embeddings)

    # Helper methods for extracting text from structured resume data

    def _extract_skills_text(self, resume_data: Dict) -> str:
        """Extract skills text from structured resume data"""
        skills_text = []

        # From structured data
        if 'structured_data' in resume_data:
            structured = resume_data['structured_data']

            # Skills by category
            skills = structured.get('skills', {})
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    if isinstance(skill_list, list):
                        for skill in skill_list:
                            if isinstance(skill, dict):
                                skills_text.append(skill.get('name', ''))
                            else:
                                skills_text.append(str(skill))

            # Work experience skills
            work_exp = structured.get('work_experience', [])
            for exp in work_exp:
                if isinstance(exp, dict):
                    exp_skills = exp.get('skills', [])
                    skills_text.extend(exp_skills)

        # From extracted entities
        if 'extracted_entities' in resume_data:
            entities = resume_data['extracted_entities']
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict) and entity.get('label') in ['SKILL', 'TECHNOLOGY', 'TOOL']:
                        skills_text.append(entity.get('text', ''))

        return " ".join(filter(None, skills_text))

    def _extract_experience_text(self, resume_data: Dict) -> str:
        """Extract work experience text"""
        experience_text = []

        if 'structured_data' in resume_data:
            work_exp = resume_data['structured_data'].get('work_experience', [])
            for exp in work_exp:
                if isinstance(exp, dict):
                    # Add job responsibilities and achievements
                    if exp.get('achievements'):
                        experience_text.extend(exp['achievements'])

                    # Add any description text
                    if exp.get('description'):
                        experience_text.append(exp['description'])

        # From extracted entities
        if 'extracted_entities' in resume_data:
            entities = resume_data['extracted_entities']
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict) and entity.get('label') in ['EXPERIENCE', 'ACHIEVEMENT']:
                        experience_text.append(entity.get('text', ''))

        return " ".join(filter(None, experience_text))

    def _extract_titles_text(self, resume_data: Dict) -> str:
        """Extract job titles text"""
        titles_text = []

        if 'structured_data' in resume_data:
            work_exp = resume_data['structured_data'].get('work_experience', [])
            for exp in work_exp:
                if isinstance(exp, dict) and exp.get('title'):
                    titles_text.append(exp['title'])

        # From extracted entities
        if 'extracted_entities' in resume_data:
            entities = resume_data['extracted_entities']
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict) and entity.get('label') in ['TITLE', 'JOB']:
                        titles_text.append(entity.get('text', ''))

        return " ".join(filter(None, titles_text))

    def _extract_education_text(self, resume_data: Dict) -> str:
        """Extract education text"""
        education_text = []

        if 'structured_data' in resume_data:
            education = resume_data['structured_data'].get('education', [])
            for edu in education:
                if isinstance(edu, dict):
                    if edu.get('degree'):
                        education_text.append(edu['degree'])
                    if edu.get('field'):
                        education_text.append(edu['field'])
                    if edu.get('school'):
                        education_text.append(edu['school'])

        # From extracted entities
        if 'extracted_entities' in resume_data:
            entities = resume_data['extracted_entities']
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict) and entity.get('label') in ['EDUCATION', 'DEGREE', 'FIELD']:
                        education_text.append(entity.get('text', ''))

        return " ".join(filter(None, education_text))

    def _extract_achievements_text(self, resume_data: Dict) -> str:
        """Extract achievements text"""
        achievements_text = []

        if 'structured_data' in resume_data:
            achievements = resume_data['structured_data'].get('achievements', [])
            achievements_text.extend(achievements)

        # From extracted entities
        if 'extracted_entities' in resume_data:
            entities = resume_data['extracted_entities']
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict) and entity.get('label') in ['ACHIEVEMENT', 'ACCOMPLISHMENT']:
                        achievements_text.append(entity.get('text', ''))

        return " ".join(filter(None, achievements_text))


class EmbeddingCache:
    """
    Simple in-memory cache for embeddings to improve performance
    """

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}

    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache"""
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key]
        return None

    def set(self, key: str, embedding: np.ndarray):
        """Store embedding in cache"""
        if len(self.cache) >= self.max_size:
            # Remove least accessed item
            least_accessed = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_accessed]
            del self.access_count[least_accessed]

        self.cache[key] = embedding
        self.access_count[key] = 1

    def clear(self):
        """Clear the cache"""
        self.cache.clear()
        self.access_count.clear()


# Test the embedding service
def test_embedding_service():
    """Test the embedding service with sample data"""
    logger.info(" Testing Embedding Service")

    # Initialize service
    embedding_service = ResumeJobEmbeddingService()

    # Sample resume data (format from your existing system)
    sample_resume = {
        "structured_data": {
            "skills": {
                "Programming Languages": [
                    {"name": "Python", "proficiency": "Expert"},
                    {"name": "JavaScript", "proficiency": "Proficient"}
                ],
                "Web Technologies": [
                    {"name": "React", "proficiency": "Proficient"},
                    {"name": "Node.js", "proficiency": "Intermediate"}
                ]
            },
            "work_experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "skills": ["Python", "Django", "PostgreSQL"],
                    "achievements": ["Led team of 5 engineers", "Improved performance by 40%"]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "school": "University of Technology",
                    "field": "Computer Science"
                }
            ]
        },
        "extracted_entities": [
            {"text": "Python", "label": "SKILL"},
            {"text": "Senior Software Engineer", "label": "TITLE"},
            {"text": "Computer Science", "label": "FIELD"}
        ]
    }

    # Sample job data
    sample_job = {
        "title": "Full Stack Developer",
        "description": "We are looking for a full stack developer to join our team",
        "requirements": "3+ years experience with Python, React, and PostgreSQL",
        "skills_required": ["Python", "React", "PostgreSQL", "JavaScript"],
        "responsibilities": "Develop web applications, maintain databases, collaborate with team"
    }

    # Generate embeddings
    print("Generating resume embedding...")
    resume_embedding = embedding_service.generate_resume_embedding(sample_resume)
    print(f"Resume embedding shape: {resume_embedding.shape}")

    print("Generating job embedding...")
    job_embedding = embedding_service.generate_job_embedding(sample_job)
    print(f"Job embedding shape: {job_embedding.shape}")

    # Calculate similarity
    similarity = embedding_service.calculate_similarity(resume_embedding, job_embedding)
    print(f"Similarity score: {similarity:.4f}")

    # Test skills embedding
    skills_embedding = embedding_service.generate_skills_embedding(["Python", "React", "PostgreSQL"])
    print(f"Skills embedding shape: {skills_embedding.shape}")

    print(" Embedding service test completed!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run test
    test_embedding_service()