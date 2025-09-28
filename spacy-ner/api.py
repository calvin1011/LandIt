import spacy
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel, Field
import re
import logging
from typing import List, Optional, Dict, Any
import time
import json
from pathlib import Path
import io
import os
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from job_data_importer import MuseJobImporter
from adzuna_job_importer import AdzunaJobImporter
from jsearch_job_importer import JSearchJobImporter
from remotive_job_importer import RemotiveJobImporter
from ai_project_generator import AIProjectGenerator
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from contextlib import asynccontextmanager

# Scheduler for automated job imports
scheduler = BackgroundScheduler()

def run_all_job_imports():
    """Function to be called by the scheduler to run all job imports."""
    logger.info("SCHEDULER: Kicking off automated job import.")
    try:
        result = import_all_jobs_direct()
        logger.info(f"SCHEDULER: Automated job import successful: {result}")
    except Exception as e:
        logger.error(f"SCHEDULER: Exception during automated job import: {e}")

# Schedule job imports every 6 hours
scheduler.add_job(run_all_job_imports, 'interval', hours=6, next_run_time=datetime.now() + timedelta(seconds=10))

# simple in memory cache for requests
recent_learning_requests = {}
recent_match_requests = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File processing imports
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from semantic_extractor import SemanticResumeExtractor

try:
    from embedding_service import ResumeJobEmbeddingService
    from database import db
    embedding_service = ResumeJobEmbeddingService()
    logger.info(" Embedding service initialized for job matching")
except Exception as e:
    logger.error(f" Failed to initialize embedding service: {e}")
    embedding_service = None

# Import our intelligence modules with error handling
try:
    from intelligent_section_detector import ContextAwareEntityExtractor, IntelligentSectionDetector
    from relationship_extractor import ResumeIntelligenceAnalyzer

    INTELLIGENT_MODULES_AVAILABLE = True
    print(" Intelligent modules loaded successfully")
except ImportError as e:
    print(f" Intelligent modules not available: {e}")
    INTELLIGENT_MODULES_AVAILABLE = False

semantic_extractor = SemanticResumeExtractor()

# Load hybrid trained spaCy model
try:
    model_path = "output_hybrid"
    nlp = spacy.load(model_path)
    logger.info(f" Successfully loaded HYBRID model from: {model_path}")

    metadata_path = Path(model_path) / "training_info.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            training_info = json.load(f)
        logger.info(
            f" Model info: {training_info.get('model_type', 'unknown')} with {training_info.get('total_labels', 'unknown')} labels")
    else:
        training_info = {}

except Exception as e:
    logger.error(f" Failed to load hybrid model: {e}")
    try:
        nlp = spacy.load("output_hybrid")
        training_info = {"model_type": "custom_only"}
        logger.warning(" Using fallback custom model")
    except Exception as e2:
        logger.error(f" Failed to load any model: {e2}")
        nlp = spacy.load("en_core_web_sm")
        training_info = {"model_type": "pretrained_only"}
        logger.warning(" Using pretrained model only")


# --- NEW LIFESPAN MANAGER ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    This replaces the deprecated on_event handlers.
    """
    # Code to run on startup
    scheduler.start()
    logger.info("APScheduler started... will run job imports every 6 hours.")

    yield  # The application runs here

    # Code to run on shutdown
    scheduler.shutdown()
    logger.info("APScheduler shut down.")

# --- CORRECT APP INITIALIZATION ---
app = FastAPI(
    title="LandIt Intelligent Resume Parser",
    version="3.1.0",
    lifespan=lifespan  # Attach the new lifespan manager here
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8080",
        "http://localhost:8081"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"]
)

# Initialize intelligence analyzer with error handling
intelligence_analyzer = None
if INTELLIGENT_MODULES_AVAILABLE:
    try:
        intelligence_analyzer = ResumeIntelligenceAnalyzer(nlp)
        logger.info(" Intelligence analyzer initialized")
    except Exception as e:
        logger.error(f" Failed to initialize intelligence analyzer: {e}")
        intelligence_analyzer = None

class ResumeText(BaseModel):
    text: str
    analysis_level: str = Field(default="full", description="Analysis level: 'basic', 'standard', or 'full'")
    include_suggestions: bool = Field(default=True, description="Include improvement suggestions")


class EntityResponse(BaseModel):
    text: str
    label: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    section: Optional[str] = None


class WorkExperienceResponse(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    skills: List[str] = []
    achievements: List[str] = []


class EducationResponse(BaseModel):
    degree: str
    school: Optional[str] = None
    year: Optional[str] = None
    gpa: Optional[str] = None


class SkillCategoryResponse(BaseModel):
    category: str
    skills: List[Dict[str, Any]]


class IntelligentParseResponse(BaseModel):
    # Basic extraction results
    entities: List[EntityResponse]

    # Structured data
    work_experience: List[WorkExperienceResponse]
    education: List[EducationResponse]
    skills: List[SkillCategoryResponse]
    achievements: List[str]

    # Intelligence insights
    experience_metrics: Dict[str, Any]
    career_progression: Dict[str, Any]
    resume_analytics: Dict[str, Any]

    # Metadata
    processing_stats: Dict[str, Any]
    model_info: Dict[str, Any]
    suggestions: Optional[List[str]] = None

class JobPostingRequest(BaseModel):
    title: str
    company: str
    description: str
    requirements: Optional[str] = ""
    responsibilities: Optional[str] = ""
    location: Optional[str] = ""
    remote_allowed: bool = False
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_level: Optional[str] = "mid"  # entry, mid, senior, executive
    job_type: Optional[str] = "full-time"
    industry: Optional[str] = ""
    skills_required: List[str] = []
    skills_preferred: List[str] = []
    education_required: Optional[str] = ""

class JobMatchRequest(BaseModel):
    user_email: str
    top_k: int = 30
    min_similarity: float = 0.3
    offset: int = 0
    exclude_job_ids: List[int] = []
    randomize: bool = True

class FeedbackRequest(BaseModel):
    user_email: str
    recommendation_id: int
    overall_rating: Optional[int] = None  # 1-5
    skills_relevance_rating: Optional[int] = None
    experience_match_rating: Optional[int] = None
    location_rating: Optional[int] = None
    company_interest_rating: Optional[int] = None
    feedback_type: str  # positive, negative, applied, saved, dismissed
    feedback_text: Optional[str] = ""
    action_taken: Optional[str] = ""

class LearningPlanRequest(BaseModel):
    user_email: str
    job_id: int
    recommendation_id: Optional[int] = None

class StoreResumeRequest(BaseModel):
    user_email: str
    resume_data: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]] = None

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF bytes"""
    if not PDF_AVAILABLE:
        raise HTTPException(status_code=400, detail="PDF processing not available. Install PyPDF2: pip install PyPDF2")

    try:
        pdf_file = io.BytesIO(file_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF extraction failed: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX bytes"""
    if not DOCX_AVAILABLE:
        raise HTTPException(status_code=400,
                            detail="DOCX processing not available. Install python-docx: pip install python-docx")

    try:
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DOCX extraction failed: {str(e)}")


def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from TXT bytes"""
    try:
        return file_content.decode('utf-8').strip()
    except UnicodeDecodeError:
        try:
            return file_content.decode('latin-1').strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Text file encoding error: {str(e)}")


def safe_get_experience_metrics(results: Dict) -> Dict[str, Any]:
    """Safely extract experience metrics with all required keys"""
    experience_metrics = results.get("experience_metrics", {})

    # Ensure all required keys exist with safe defaults
    safe_metrics = {
        "total_years": experience_metrics.get("total_years", 0),
        "companies": experience_metrics.get("companies", 0),
        "roles": experience_metrics.get("roles", 0),
        "average_tenure": experience_metrics.get("average_tenure", 0.0)
    }

    return safe_metrics


def safe_context_extraction(text: str) -> Dict:
    """Safely perform context-aware extraction with proper error handling"""
    try:
        if not INTELLIGENT_MODULES_AVAILABLE:
            return _fallback_basic_extraction(text)

        context_extractor = ContextAwareEntityExtractor(nlp)
        results = context_extractor.extract_with_context(text)

        # Ensure the results have all required keys
        safe_results = {
            "entities": results.get("entities", []),
            "sections": results.get("sections", {}),
            "section_analysis": results.get("section_analysis", {
                "sections_found": 0,
                "has_experience": False,
                "has_education": False,
                "has_skills": False,
                "structure_score": 0
            }),
            "experience_analysis": results.get("experience_analysis", {
                "average_tenure": 0.0,
                "total_jobs": 0,
                "total_experience_months": 0.0,
                "valid_jobs": 0
            })
        }

        return safe_results

    except Exception as e:
        logger.error(f"Context extraction failed: {e}")
        return _fallback_basic_extraction(text)


def _fallback_basic_extraction(text: str) -> Dict:
    """Fallback to basic spaCy extraction if intelligent modules fail"""
    try:
        doc = nlp(text)
        entities = []

        for ent in doc.ents:
            # Map spaCy entities to our format
            entity_label = ent.label_
            if entity_label == "PERSON":
                entity_label = "NAME"
            elif entity_label == "ORG":
                entity_label = "COMPANY"

            entities.append({
                "text": ent.text,
                "label": entity_label,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.7,
                "section": "unknown",
                "section_boost": False
            })

        return {
            "entities": entities,
            "sections": {},
            "section_analysis": {
                "sections_found": 0,
                "has_experience": False,
                "has_education": False,
                "has_skills": False,
                "structure_score": 0
            },
            "experience_analysis": {
                "average_tenure": 0.0,
                "total_jobs": 0,
                "total_experience_months": 0.0,
                "valid_jobs": 0
            }
        }

    except Exception as e:
        logger.error(f"Even basic extraction failed: {e}")
        # Return completely safe defaults
        return {
            "entities": [],
            "sections": {},
            "section_analysis": {
                "sections_found": 0,
                "has_experience": False,
                "has_education": False,
                "has_skills": False,
                "structure_score": 0
            },
            "experience_analysis": {
                "average_tenure": 0.0,
                "total_jobs": 0,
                "total_experience_months": 0.0,
                "valid_jobs": 0
            }
        }


@app.post("/jobs/create")
def create_job_posting(job_data: JobPostingRequest):
    """
    Create a new job posting with embeddings
    """
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    try:
        start_time = time.time()

        # Convert to dict for processing
        job_dict = job_data.dict()

        # Generate embeddings for the job
        logger.info(f"Generating embeddings for job: {job_data.title}")

        description_embedding = embedding_service.generate_job_embedding(job_dict)
        title_embedding = embedding_service.model.encode(job_data.title)
        requirements_embedding = embedding_service.model.encode(job_data.requirements or "")

        # Store in database
        job_id = db.store_job_posting(
            job_dict,
            {
                'description': description_embedding,
                'title': title_embedding,
                'requirements': requirements_embedding
            }
        )

        processing_time = time.time() - start_time

        return {
            "success": True,
            "job_id": job_id,
            "title": job_data.title,
            "company": job_data.company,
            "processing_time": processing_time,
            "message": "Job posting created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create job posting: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job posting: {str(e)}")


@app.post("/jobs/find-matches")
def find_job_matches(match_request: JobMatchRequest):
    """
    Find job matches for a user's resume with rotation and fresh results
    """
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    try:
        # Create unique request key for caching the calls for finding jobs
        request_key = f"{match_request.user_email}_{match_request.top_k}_{match_request.offset}_{','.join(map(str, match_request.exclude_job_ids))}"
        request_hash = hashlib.md5(request_key.encode()).hexdigest()

        # Check for duplicate request
        now = datetime.now()
        if request_hash in recent_match_requests:
            cached_entry = recent_match_requests[request_hash]
            last_request_time = cached_entry['timestamp']

            # If request is still processing, reject it
            if cached_entry.get('processing', False):
                logger.info(f"Match request already processing for {match_request.user_email}, rejecting duplicate")
                raise HTTPException(
                    status_code=429,
                    detail="Request already being processed. Please wait a moment."
                )

            # If we have a cached response, return it
            if now - last_request_time < timedelta(seconds=3):  # 3 second window
                logger.info(f"Duplicate match request detected for {match_request.user_email}, returning cached result")
                return cached_entry['response']

        # Clean old cache entries
        keys_to_remove = []
        for key, value in recent_match_requests.items():
            if now - value['timestamp'] > timedelta(minutes=1):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del recent_match_requests[key]

        # Mark this request as processing
        recent_match_requests[request_hash] = {
            'timestamp': now,
            'processing': True,
            'response': None
        }

        import random
        start_time = time.time()

        # Get user's resume
        user_resume = db.get_user_resume(match_request.user_email)
        if not user_resume:
            raise HTTPException(status_code=404, detail="User resume not found. Please upload a resume first.")

        # Get all active jobs (excluding already shown ones)
        all_jobs = db.get_all_jobs_with_embeddings()
        if not all_jobs:
            return {
                "matches": [],
                "total_found": 0,
                "message": "No active job postings available"
            }

        # Filter out excluded jobs
        if match_request.exclude_job_ids:
            all_jobs = [job for job in all_jobs if job['id'] not in match_request.exclude_job_ids]

        logger.info(f"Finding matches among {len(all_jobs)} jobs for {match_request.user_email}")

        # Get user's resume embedding
        resume_embedding = user_resume['full_resume_embedding']
        skills_embedding = user_resume['skills_embedding']

        # Calculate matches
        matches = []
        for job in all_jobs:
            # Calculate similarity scores
            semantic_similarity = embedding_service.calculate_similarity(
                resume_embedding,
                job['description_embedding']
            )

            skills_similarity = embedding_service.calculate_similarity(
                skills_embedding,
                job['description_embedding']
            )

            # Calculate experience match
            user_years = user_resume.get('years_of_experience', 0)
            job_level = job.get('experience_level', 'mid')
            experience_match = calculate_experience_match(user_years, job_level)

            # Calculate location match
            location_match = calculate_location_match(
                user_resume.get('preferred_locations', []),
                job.get('location', ''),
                job.get('remote_allowed', False)
            )

            # Calculate overall score
            overall_score = (
                    semantic_similarity * 0.25 +
                    skills_similarity * 0.45 +
                    experience_match * 0.20 +
                    location_match * 0.10
            )

            # Only include jobs above minimum similarity
            if overall_score >= match_request.min_similarity:
                # Extract matching skills
                user_skills = extract_user_skills(user_resume)
                job_skills = job.get('skills_required', [])
                skill_matches = list(set(user_skills) & set([s.lower() for s in job_skills]))

                skill_gaps_detailed = categorize_skill_gaps(
                    user_skills,
                    job_skills,
                    job,
                    user_resume.get('experience_level', 'mid')
                )

                gap_analysis = calculate_gap_severity(
                    skill_gaps_detailed,
                    user_resume.get('experience_level', 'mid')
                )

                improvement_summary = generate_improvement_summary(
                    skill_gaps_detailed,
                    gap_analysis
                )

                matches.append({
                    'job_id': job['id'],
                    'title': job['title'],
                    'company': job['company'],
                    'job_url': job.get('job_url', ''),
                    'location': job.get('location'),
                    'remote_allowed': job.get('remote_allowed', False),
                    'salary_min': job.get('salary_min'),
                    'salary_max': job.get('salary_max'),
                    'experience_level': job.get('experience_level'),
                    'skills_required': job.get('skills_required', []),
                    'overall_score': round(overall_score, 3),
                    'semantic_similarity': round(semantic_similarity, 3),
                    'skills_similarity': round(skills_similarity, 3),
                    'experience_match': round(experience_match, 3),
                    'location_match': round(location_match, 3),
                    'skill_matches': skill_matches,
                    'skill_gaps': skill_gaps_detailed['critical'][:3],  # Keep existing for compatibility
                    'skill_gaps_detailed': skill_gaps_detailed,
                    'gap_analysis': gap_analysis,
                    'improvement_summary': improvement_summary,
                    'learning_priority': 'high' if gap_analysis['critical_gaps'] >= 2 else 'medium' if gap_analysis['critical_gaps'] >= 1 else 'low',

                    'match_explanation': generate_enhanced_match_explanation(
                        overall_score, skill_matches, skill_gaps_detailed, experience_match, gap_analysis
                    )
                })

        # Sort by overall score
        matches.sort(key=lambda x: x['overall_score'], reverse=True)

        # NEW: Implement job rotation logic
        if match_request.randomize and len(matches) > match_request.top_k:
            # Get top matches (2x what we need for quality)
            top_matches = matches[:match_request.top_k * 2]

            # Group by score ranges for intelligent rotation
            excellent_matches = [m for m in top_matches if m['overall_score'] >= 0.7]
            good_matches = [m for m in top_matches if 0.5 <= m['overall_score'] < 0.7]
            fair_matches = [m for m in top_matches if 0.3 <= m['overall_score'] < 0.5]

            # Randomize within each group
            if excellent_matches:
                random.shuffle(excellent_matches)
            if good_matches:
                random.shuffle(good_matches)
            if fair_matches:
                random.shuffle(fair_matches)

            # Recombine with some randomization but maintaining quality
            final_matches = []

            # Always include some excellent matches
            final_matches.extend(excellent_matches[:max(1, match_request.top_k // 2)])

            # Fill with good matches
            remaining_slots = match_request.top_k - len(final_matches)
            if remaining_slots > 0 and good_matches:
                final_matches.extend(good_matches[:remaining_slots])

            # Fill any remaining with fair matches
            remaining_slots = match_request.top_k - len(final_matches)
            if remaining_slots > 0 and fair_matches:
                final_matches.extend(fair_matches[:remaining_slots])

            matches = final_matches
        else:
            # Standard pagination without randomization
            start_idx = match_request.offset
            end_idx = start_idx + match_request.top_k
            matches = matches[start_idx:end_idx]

        # Store recommendations in database for feedback tracking
        recommendation_ids = []
        for match in matches:
            scores = {
                'semantic_similarity': match['semantic_similarity'],
                'skills_match': match['skills_similarity'],
                'experience_match': match['experience_match'],
                'location_match': match['location_match'],
                'overall_score': match['overall_score']
            }

            match_reasons = {
                'skill_matches': match['skill_matches'],
                'skill_gaps': match['skill_gaps'],
                'explanation': match['match_explanation']
            }

            rec_id = db.store_recommendation(
                match_request.user_email,
                match['job_id'],
                scores,
                match_reasons
            )
            recommendation_ids.append(rec_id)
            match['recommendation_id'] = rec_id

        processing_time = time.time() - start_time

        response = {
            "matches": matches,
            "total_found": len(matches),
            "total_jobs_analyzed": len(all_jobs),
            "user_email": match_request.user_email,
            "processing_time": processing_time,
            "recommendation_ids": recommendation_ids,
            "has_more": len(all_jobs) > (match_request.offset + len(matches)),
            "next_offset": match_request.offset + len(matches)
        }

        # Cache the response
        recent_match_requests[request_hash] = {
            'timestamp': now,
            'processing': False,
            'response': response
        }

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Job matching failed: {e}")
        # Clear processing flag on error
        if 'request_hash' in locals() and request_hash in recent_match_requests:
            del recent_match_requests[request_hash]
        raise HTTPException(status_code=500, detail=f"Job matching failed: {str(e)}")
def generate_enhanced_match_explanation(overall_score: float, skill_matches: List[str],
                                       skill_gaps_detailed: Dict, experience_match: float,
                                       gap_analysis: Dict) -> str:
    """
    Enhanced match explanation with actionable insights
    """
    if overall_score >= 0.8:
        quality = "Excellent"
    elif overall_score >= 0.6:
        quality = "Good"
    elif overall_score >= 0.4:
        quality = "Fair"
    else:
        quality = "Poor"

    explanation = f"{quality} match based on your profile. "

    if skill_matches:
        explanation += f"Strong alignment in {', '.join(skill_matches[:2])}. "

    critical_gaps = len(skill_gaps_detailed['critical'])
    if critical_gaps == 0:
        explanation += "You meet all critical requirements! "
    elif critical_gaps <= 2:
        explanation += f"Focus on learning {', '.join(skill_gaps_detailed['critical'][:2])} to become highly competitive. "
    else:
        explanation += f"This role requires significant upskilling in {critical_gaps} key areas. "

    if gap_analysis['estimated_learning_weeks'] <= 4:
        explanation += "Skills gap can be bridged quickly with focused learning."
    elif gap_analysis['estimated_learning_weeks'] <= 8:
        explanation += "Moderate learning investment needed for this role."
    else:
        explanation += "Consider this a longer-term career goal requiring substantial skill development."

    return explanation

@app.get("/jobs/recommendations/{user_email}")
def get_user_recommendations(user_email: str, limit: int = 10):
    """
    Get stored recommendations for a user
    """
    try:
        recommendations = db.get_user_recommendations(user_email, limit)

        # Format recommendations for frontend
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                'recommendation_id': rec['id'],
                'job_id': rec['job_id'],
                'title': rec['title'],
                'company': rec['company'],
                'location': rec['location'],
                'salary_range': format_salary_range(rec.get('salary_min'), rec.get('salary_max')),
                'experience_level': rec.get('experience_level'),
                'overall_score': rec['overall_score'],
                'skills_match_score': rec['skills_match_score'],
                'created_at': rec['created_at'].isoformat() if rec['created_at'] else None,
                'is_viewed': rec.get('is_viewed', False),
                'is_saved': rec.get('is_saved', False),
                'skill_matches': rec.get('skill_matches', []),
                'skill_gaps': rec.get('skill_gaps', [])
            })

        return {
            "recommendations": formatted_recommendations,
            "total": len(formatted_recommendations),
            "user_email": user_email
        }

    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@app.post("/jobs/feedback")
def submit_job_feedback(feedback: FeedbackRequest):
    """
    Submit feedback on a job recommendation
    """
    try:
        # Store feedback in database
        feedback_id = db.store_feedback(
            feedback.user_email,
            feedback.recommendation_id,
            feedback.dict()
        )

        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        }

    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@app.get("/jobs/analytics")
def get_job_analytics(days: int = 30):
    """
    Get job matching analytics for the last N days
    """
    try:
        analytics = db.get_feedback_analytics(days)

        return {
            "analytics": analytics,
            "period_days": days,
            "generated_at": time.time()
        }

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

def calculate_experience_match(user_years: int, job_level: str) -> float:
    """Calculate experience level match score"""
    level_requirements = {
        'entry': (0, 2),
        'mid': (2, 5),
        'senior': (5, 10),
        'executive': (10, 20)
    }

    if job_level not in level_requirements:
        return 0.8  # Default moderate match

    min_years, max_years = level_requirements[job_level]

    if min_years <= user_years <= max_years:
        return 1.0  # Perfect match
    elif user_years < min_years:
        # Under-qualified
        gap = min_years - user_years
        return max(0.3, 1.0 - (gap * 0.2))
    else:
        # Over-qualified
        excess = user_years - max_years
        return max(0.5, 1.0 - (excess * 0.1))


def calculate_location_match(user_locations: List[str], job_location: str, remote_allowed: bool) -> float:
    """Calculate location preference match"""
    if remote_allowed:
        return 1.0  # Perfect match for remote work

    if not user_locations or not job_location:
        return 0.6  # Neutral if no location data

    # Simple location matching (you can enhance this)
    job_location_lower = job_location.lower()
    for user_loc in user_locations:
        if user_loc.lower() in job_location_lower or job_location_lower in user_loc.lower():
            return 1.0

    return 0.3  # Low match for different locations


def extract_user_skills(user_resume: Dict) -> List[str]:
    """Extract skills list from user resume"""
    skills = []

    # From top_skills
    if 'top_skills' in user_resume:
        skills.extend([skill.lower() for skill in user_resume['top_skills']])

    # From structured data
    structured_data = user_resume.get('structured_data')
    if structured_data and isinstance(structured_data, str):
        try:
            structured_data = json.loads(structured_data)
        except:
            structured_data = {}

    if isinstance(structured_data, dict):
        skills_data = structured_data.get('skills', {})
        for category, skill_list in skills_data.items():
            for skill in skill_list:
                if isinstance(skill, dict):
                    skills.append(skill.get('name', '').lower())
                else:
                    skills.append(str(skill).lower())

    return list(set(skills))  # Remove duplicates


def generate_match_explanation(overall_score: float, skill_matches: List[str], skill_gaps: List[str],
                               experience_match: float) -> str:
    """Generate human-readable match explanation"""
    if overall_score >= 0.8:
        quality = "Excellent"
    elif overall_score >= 0.6:
        quality = "Good"
    elif overall_score >= 0.4:
        quality = "Fair"
    else:
        quality = "Poor"

    explanation = f"{quality} match based on your profile. "

    if skill_matches:
        explanation += f"Your skills in {', '.join(skill_matches[:3])} align well. "

    if skill_gaps:
        explanation += f"Consider developing skills in {', '.join(skill_gaps[:2])} to strengthen your application. "

    if experience_match >= 0.8:
        explanation += "Your experience level is well-suited for this role."
    elif experience_match < 0.5:
        explanation += "This role may require different experience level than your background."

    return explanation


def format_salary_range(salary_min: Optional[int], salary_max: Optional[int]) -> str:
    """Format salary range for display"""
    if salary_min and salary_max:
        return f"${salary_min:,} - ${salary_max:,}"
    elif salary_min:
        return f"${salary_min:,}+"
    elif salary_max:
        return f"Up to ${salary_max:,}"
    else:
        return "Salary not specified"


def categorize_skill_gaps(user_skills: List[str], job_skills: List[str], job_data: Dict,
                          user_experience_level: str) -> Dict:
    """
    Categorize skill gaps by importance and type
    """
    user_skills_lower = [skill.lower() for skill in user_skills]

    # Define critical skills by job type and experience level
    critical_skills_db = {
        'software': ['programming', 'coding', 'development'],
        'data': ['python', 'sql', 'analysis', 'statistics'],
        'web': ['html', 'css', 'javascript'],
        'cloud': ['aws', 'azure', 'gcp', 'docker'],
        'mobile': ['ios', 'android', 'react native', 'flutter']
    }

    # Trending skills (you can update this periodically)
    trending_skills = [
        'kubernetes', 'terraform', 'machine learning', 'ai', 'blockchain',
        'typescript', 'react', 'vue', 'golang', 'rust', 'graphql'
    ]

    skill_gaps = {
        'critical': [],
        'important': [],
        'nice_to_have': [],
        'trending': []
    }

    job_title_lower = job_data.get('title', '').lower()
    job_desc_lower = job_data.get('description', '').lower()

    for skill in job_skills:
        skill_lower = skill.lower()

        if skill_lower in user_skills_lower:
            continue  # User already has this skill

        # Categorize based on various factors
        is_critical = False
        is_important = False
        is_trending = skill_lower in [t.lower() for t in trending_skills]

        # Check if skill appears in job title (usually critical)
        if skill_lower in job_title_lower:
            is_critical = True

        # Check against critical skills database
        for category, critical_list in critical_skills_db.items():
            if category in job_title_lower or category in job_desc_lower:
                if any(crit in skill_lower for crit in critical_list):
                    is_critical = True
                    break

        # Check frequency in job description
        skill_mentions = job_desc_lower.count(skill_lower)
        if skill_mentions >= 3:  # Mentioned multiple times
            is_important = True
        elif skill_mentions >= 2:
            is_important = True

        # Categorize
        if is_critical:
            skill_gaps['critical'].append(skill)
        elif is_important:
            skill_gaps['important'].append(skill)
        elif is_trending:
            skill_gaps['trending'].append(skill)
        else:
            skill_gaps['nice_to_have'].append(skill)

    return skill_gaps


def calculate_gap_severity(skill_gaps_detailed: Dict, user_experience_level: str) -> Dict:
    """
    Calculate severity metrics for skill gaps
    """
    total_gaps = sum(len(gaps) for gaps in skill_gaps_detailed.values())
    critical_count = len(skill_gaps_detailed['critical'])

    # Calculate severity score (0-100, lower is better)
    severity_score = min(100, (critical_count * 25) + (len(skill_gaps_detailed['important']) * 10))

    # Estimate learning time based on gap types and user experience
    time_multipliers = {
        'entry': 1.5,
        'mid': 1.0,
        'senior': 0.7,
        'executive': 0.5
    }

    base_time = (critical_count * 4) + (len(skill_gaps_detailed['important']) * 2)  # weeks
    estimated_time = base_time * time_multipliers.get(user_experience_level, 1.0)

    # Calculate potential score improvement
    current_match = 100 - severity_score
    potential_improvement = min(25, critical_count * 8 + len(skill_gaps_detailed['important']) * 3)

    return {
        'total_gaps': total_gaps,
        'critical_gaps': critical_count,
        'severity_score': severity_score,
        'estimated_learning_weeks': round(estimated_time),
        'potential_score_improvement': potential_improvement,
        'difficulty_level': 'high' if critical_count >= 3 else 'medium' if critical_count >= 1 else 'low'
    }


def generate_improvement_summary(skill_gaps_detailed: Dict, gap_analysis: Dict) -> str:
    """
    Generate human-readable improvement summary
    """
    critical_count = len(skill_gaps_detailed['critical'])
    important_count = len(skill_gaps_detailed['important'])

    if critical_count == 0 and important_count == 0:
        return "You're well-qualified for this role! Focus on trending skills to stay competitive."

    summary_parts = []

    if critical_count > 0:
        critical_skills = ', '.join(skill_gaps_detailed['critical'][:3])
        summary_parts.append(f"Priority focus: {critical_skills}")

    if important_count > 0:
        important_skills = ', '.join(skill_gaps_detailed['important'][:2])
        summary_parts.append(f"Secondary skills: {important_skills}")

    time_estimate = gap_analysis['estimated_learning_weeks']
    summary_parts.append(f"Estimated learning time: {time_estimate} weeks")

    return ". ".join(summary_parts) + "."


@app.post("/generate-learning-plan")
def generate_learning_plan(request: LearningPlanRequest):
    """
    Generate AI-powered learning plan for a specific job recommendation
    """
    try:
        # Create a unique key for this request
        request_key = f"{request.user_email}_{request.job_id}_{request.recommendation_id}"
        request_hash = hashlib.md5(request_key.encode()).hexdigest()

        # Check if we've processed this exact request recently
        now = datetime.now()
        if request_hash in recent_learning_requests:
            cached_entry = recent_learning_requests[request_hash]
            last_request_time = cached_entry['timestamp']

            # If request is still processing, wait briefly and return error
            if cached_entry.get('processing', False):
                logger.info(f"Request already processing for {request_key}, rejecting duplicate")
                raise HTTPException(
                    status_code=429,
                    detail="Request already being processed. Please wait a moment."
                )

            # If we have a completed response within 10 seconds, return it
            if now - last_request_time < timedelta(seconds=10):  # Increased window
                logger.info(f"Duplicate learning plan request detected for {request_key}, returning cached result")
                return cached_entry['response']

        # Clean old entries (keep cache small)
        keys_to_remove = []
        for key, value in recent_learning_requests.items():
            if now - value['timestamp'] > timedelta(minutes=2):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del recent_learning_requests[key]

        # IMPORTANT: Mark this request as processing immediately
        recent_learning_requests[request_hash] = {
            'timestamp': now,
            'processing': True,
            'response': None
        }

        start_time = time.time()

        # Initialize AI project generator
        try:
            ai_generator = AIProjectGenerator()
        except ValueError as e:
            # Clear the processing flag on error
            del recent_learning_requests[request_hash]
            raise HTTPException(
                status_code=503,
                detail="AI service not available. OpenAI API key not configured."
            )

        # Get user's resume data
        user_resume = db.get_user_resume(request.user_email)
        if not user_resume:
            # Clear the processing flag on error
            del recent_learning_requests[request_hash]
            raise HTTPException(
                status_code=404,
                detail="User resume not found. Please upload a resume first."
            )

        # Get job data
        job_data = db.get_job_by_id(request.job_id)
        if not job_data:
            # Clear the processing flag on error
            del recent_learning_requests[request_hash]
            raise HTTPException(
                status_code=404,
                detail="Job not found."
            )

        # Get or calculate skill gaps for this job
        user_skills = extract_user_skills(user_resume)
        job_skills = job_data.get('skills_required', [])

        # Generate detailed skill gap analysis (reusing existing logic)
        skill_gaps_detailed = categorize_skill_gaps(
            user_skills,
            job_skills,
            job_data,
            user_resume.get('experience_level', 'mid')
        )

        gap_analysis = calculate_gap_severity(
            skill_gaps_detailed,
            user_resume.get('experience_level', 'mid')
        )

        # Build user profile for AI
        user_profile = {
            'experience_level': user_resume.get('experience_level', 'mid'),
            'years_of_experience': user_resume.get('years_of_experience', 0),
            'current_skills': user_skills,
            'current_job_title': user_resume.get('current_job_title', ''),
            'top_skills': user_resume.get('top_skills', [])
        }

        # Generate AI-powered learning plan
        logger.info(f"Generating learning plan for {request.user_email} -> {job_data.get('title')}")

        learning_plan = ai_generator.generate_learning_plan(
            user_profile=user_profile,
            job_data=job_data,
            skill_gaps_detailed=skill_gaps_detailed,
            gap_analysis=gap_analysis
        )

        # Store learning plan in database for future reference
        plan_id = db.store_learning_plan(
            user_email=request.user_email,
            job_id=request.job_id,
            recommendation_id=request.recommendation_id,
            learning_plan=learning_plan
        )

        processing_time = time.time() - start_time

        # Return comprehensive learning plan
        response = {
            "success": True,
            "plan_id": plan_id,
            "learning_plan": learning_plan,
            "job_info": {
                "title": job_data.get('title'),
                "company": job_data.get('company'),
                "job_id": request.job_id
            },
            "user_profile": {
                "experience_level": user_profile['experience_level'],
                "current_skills_count": len(user_skills)
            },
            "gap_summary": {
                "critical_gaps": len(skill_gaps_detailed.get('critical', [])),
                "important_gaps": len(skill_gaps_detailed.get('important', [])),
                "estimated_weeks": gap_analysis.get('estimated_learning_weeks', 8),
                "difficulty": gap_analysis.get('difficulty_level', 'medium')
            },
            "processing_time": processing_time,
            "message": f"Generated learning plan with {len(learning_plan.get('critical_projects', []))} critical projects"
        }

        # Update cache with completed response
        recent_learning_requests[request_hash] = {
            'timestamp': now,
            'processing': False,
            'response': response
        }

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to generate learning plan: {e}")
        # Clear the processing flag on error
        if request_hash in recent_learning_requests:
            del recent_learning_requests[request_hash]
        raise HTTPException(
            status_code=500,
            detail=f"Learning plan generation failed: {str(e)}"
        )

@app.get("/learning-plans/{user_email}")
def get_user_learning_plans(user_email: str, limit: int = 10):
    """
    Get user's saved learning plans
    """
    try:
        learning_plans = db.get_user_learning_plans(user_email, limit)

        return {
            "success": True,
            "learning_plans": learning_plans,
            "total": len(learning_plans),
            "user_email": user_email
        }

    except Exception as e:
        logger.error(f"Failed to get learning plans: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve learning plans: {str(e)}"
        )


@app.post("/learning-plans/{plan_id}/progress")
def update_learning_progress(plan_id: int, progress_data: Dict[str, Any]):
    """
    Update progress on a learning plan
    """
    try:
        # Store progress update
        progress_id = db.update_learning_progress(plan_id, progress_data)

        return {
            "success": True,
            "progress_id": progress_id,
            "message": "Progress updated successfully"
        }

    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update progress: {str(e)}"
        )

@app.get("/")
def root():
    return {
        "message": "LandIt Intelligent Resume Parser with Job Matching",
        "version": "3.1.0",  # Updated version
        "model_type": training_info.get("model_type", "unknown"),
        "intelligent_modules": INTELLIGENT_MODULES_AVAILABLE,
        "job_matching_enabled": embedding_service is not None,
        "file_processing": {
            "pdf_support": PDF_AVAILABLE,
            "docx_support": DOCX_AVAILABLE,
            "txt_support": True
        },
        "endpoints": {
            "/parse-resume": "Text-based parsing",
            "/parse-resume-file": "File upload parsing",
            "/parse-resume-semantic": "Semantic pattern matching",
            "/parse-resume-hybrid": "Combined spaCy + semantic",
            "/parse-resume-file-with-matching": "Parse resume and find job matches",
            "/jobs/create": "Create job posting",
            "/jobs/find-matches": "Find job matches for user",
            "/jobs/recommendations/{email}": "Get user recommendations",
            "/jobs/feedback": "Submit feedback on recommendations",
            "/jobs/analytics": "Get matching analytics"
        },
        "intelligence_features": [
            "Section-aware entity extraction",
            "Relationship detection",
            "Career progression analysis",
            "Skills categorization",
            "Achievement extraction",
            "ATS compatibility scoring",
            "Resume quality assessment",
            "Improvement suggestions",
            "Vector-based job matching",
            "Skills gap analysis",
            "Experience level matching"
        ] if INTELLIGENT_MODULES_AVAILABLE else [
            "Basic entity extraction",
            "Semantic pattern matching"
        ],
        "analysis_levels": {
            "basic": "Entity extraction only",
            "standard": "Entities + structured data",
            "full": "Complete intelligence analysis" if INTELLIGENT_MODULES_AVAILABLE else "Semantic analysis"
        },
        "job_matching_features": [
            "Resume parsing and analysis",
            "Vector-based job matching",
            "Skills gap analysis",
            "Experience level matching",
            "Location preference matching",
            "Feedback collection and learning",
            "Real-time recommendations"
        ] if embedding_service else []
    }

@app.get("/health")
def health_check():
    """Enhanced health check with intelligence status"""
    return {
        "status": "healthy",
        "model_loaded": "ner" in nlp.pipe_names,
        "model_type": training_info.get("model_type", "unknown"),
        "intelligent_modules": INTELLIGENT_MODULES_AVAILABLE,
        "file_processing": {
            "pdf_support": PDF_AVAILABLE,
            "docx_support": DOCX_AVAILABLE,
            "txt_support": True
        },
        "intelligence_modules_detail": {
            "section_detector": INTELLIGENT_MODULES_AVAILABLE,
            "relationship_extractor": INTELLIGENT_MODULES_AVAILABLE,
            "analytics_engine": intelligence_analyzer is not None
        },
        "total_labels": len(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else 0
    }


@app.post("/parse-resume-file")
async def parse_resume_file(
        file: UploadFile = File(...),
        analysis_level: str = "full",
        include_suggestions: bool = True,
        use_hybrid: bool = True
):
    """
    Parse resume from uploaded file (PDF, DOCX, TXT)
    This endpoint replaces your Node.js backend functionality
    """
    start_time = time.time()

    try:
        logger.info(f" Processing file: {file.filename} ({file.content_type})")

        # Validate file type
        allowed_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported: PDF, DOCX, TXT"
            )

        # Validate file size (5MB limit)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        # Extract text based on file type
        if file.content_type == 'text/plain':
            text = extract_text_from_txt(file_content)
        elif file.content_type == 'application/pdf':
            text = extract_text_from_pdf(file_content)
        elif file.content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            text = extract_text_from_docx(file_content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if not text.strip():
            raise HTTPException(status_code=400, detail="No text could be extracted from the file")

        logger.info(f" Extracted {len(text)} characters from {file.filename}")

        # Choose processing method based on use_hybrid parameter
        if use_hybrid and semantic_extractor:
            # Use hybrid processing for optimal results
            logger.info("Using hybrid processing for optimal extraction")

            try:
                # Get spaCy results (intelligent analysis)
                if intelligence_analyzer:
                    spacy_results = intelligence_analyzer.analyze_resume(text)
                    logger.info(f" spaCy analysis: {len(spacy_results.get('entities', []))} entities")
                else:
                    spacy_results = safe_context_extraction(text)
                    logger.info(f" Basic spaCy analysis: {len(spacy_results.get('entities', []))} entities")
            except Exception as e:
                logger.error(f"spaCy analysis failed: {str(e)}")
                spacy_results = {"entities": [], "experience_metrics": {"average_tenure": 0.0}}

            # Get semantic results
            try:
                semantic_results = semantic_extractor.extract_semantic_entities(text)
                logger.info(f" Semantic analysis: {len(semantic_results.get('entities', []))} entities")
            except Exception as e:
                logger.error(f"Semantic analysis failed: {str(e)}")
                semantic_results = {"entities": []}

            # Merge results intelligently
            try:
                merged_results = merge_extraction_results(spacy_results, semantic_results, text)
                logger.info(f" Hybrid merge: {len(merged_results.get('entities', []))} total entities")
            except Exception as e:
                logger.error(f"Merge failed: {str(e)}")
                # Fallback: use spaCy results only
                merged_results = spacy_results

            processing_time = time.time() - start_time

            # Build comprehensive hybrid response
            response = {
                "entities": merged_results.get("entities", []),
                "personal_info": merged_results.get("personal_info", {}),
                "work_experience": merged_results.get("work_experience", []),
                "education": merged_results.get("education", []),
                "skills": merged_results.get("skills", {}),
                "achievements": merged_results.get("achievements", []),
                "resume_analytics": merged_results.get("resume_analytics", {}),
                "experience_metrics": merged_results.get("experience_metrics", {"average_tenure": 0.0}),
                "processing_stats": {
                    "processing_time_seconds": processing_time,
                    "total_entities": len(merged_results.get("entities", [])),
                    "spacy_entities": len(spacy_results.get("entities", [])),
                    "semantic_entities": len(semantic_results.get("entities", [])),
                    "method": "hybrid_optimal",
                    "improvement": len(merged_results.get("entities", [])) - len(spacy_results.get("entities", []))
                },
                "file_info": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size_bytes": len(file_content),
                    "text_length": len(text)
                },
                "model_info": {
                    "model_type": training_info.get("model_type", "unknown"),
                    "version": "3.0.0",
                    "processing_method": "hybrid_automatic"
                }
            }

        else:
            # Use standard intelligent processing
            logger.info(" Using standard intelligent processing")
            data = ResumeText(text=text, analysis_level=analysis_level, include_suggestions=include_suggestions)
            response = parse_resume_intelligent(data)

            # Add file metadata to result
            response["file_info"] = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(file_content),
                "text_length": len(text)
            }

        processing_time = time.time() - start_time
        logger.info(f" Successfully processed {file.filename} in {processing_time:.2f}s")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f" File processing error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@app.post("/parse-resume", response_model=Dict[str, Any])
def parse_resume_intelligent(data: ResumeText):
    """
    Intelligent resume parsing with multiple analysis levels and comprehensive error handling
    """
    start_time = time.time()

    try:
        # Validate input
        text = data.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        if len(text) > 50000:
            logger.warning(f"Text truncated from {len(text)} to 50000 characters")
            text = text[:50000]

        logger.info(f"Processing resume with {data.analysis_level} analysis level")

        # Perform analysis based on requested level with proper error handling
        if data.analysis_level == "basic":
            results = safe_context_extraction(text)
        elif data.analysis_level == "standard":
            results = _perform_standard_analysis(text)
        else:  # full
            if intelligence_analyzer:
                try:
                    results = intelligence_analyzer.analyze_resume(text)
                except Exception as e:
                    logger.error(f"Full analysis failed, falling back to standard: {e}")
                    results = _perform_standard_analysis(text)
            else:
                logger.warning("Intelligence analyzer not available, falling back to standard analysis")
                results = _perform_standard_analysis(text)

        processing_time = time.time() - start_time

        # Generate suggestions if requested
        suggestions = None
        if data.include_suggestions and data.analysis_level == "full" and intelligence_analyzer:
            try:
                suggestions = _generate_improvement_suggestions(results)
            except Exception as e:
                logger.warning(f"Failed to generate suggestions: {e}")
                suggestions = ["Enable intelligent analysis for personalized suggestions"]

        # Ensure experience_metrics has all required keys
        if "experience_metrics" in results:
            results["experience_metrics"] = safe_get_experience_metrics(results)
        else:
            results["experience_metrics"] = {
                "total_years": 0,
                "companies": 0,
                "roles": 0,
                "average_tenure": 0.0
            }

        # Build safe response
        response = {
            "entities": results.get("entities", []),
            "sections": results.get("sections", {}),
            "section_analysis": results.get("section_analysis", {}),
            "experience_analysis": results.get("experience_analysis", {"average_tenure": 0.0}),
            "work_experience": results.get("work_experience", []),
            "education": results.get("education", []),
            "skills": results.get("skills", {}),
            "achievements": results.get("achievements", []),
            "experience_metrics": results.get("experience_metrics", {"average_tenure": 0.0}),
            "career_progression": results.get("career_progression", {}),
            "resume_analytics": results.get("resume_analytics", {}),
            "processing_stats": {
                "processing_time_seconds": processing_time,
                "total_entities": len(results.get("entities", [])),
                "analysis_level": data.analysis_level,
                "intelligent_modules_used": INTELLIGENT_MODULES_AVAILABLE
            },
            "model_info": {
                "model_type": training_info.get("model_type", "unknown"),
                "version": "3.0.0",
                "intelligence_level": data.analysis_level
            },
            "suggestions": suggestions
        }

        logger.info(f"Completed {data.analysis_level} analysis in {processing_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f"Error in intelligent parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


def _perform_standard_analysis(text: str) -> Dict:
    """Standard analysis with structured data but limited intelligence"""
    try:
        context_results = safe_context_extraction(text)

        # Add basic relationship extraction if available
        if INTELLIGENT_MODULES_AVAILABLE:
            try:
                from relationship_extractor import IntelligentRelationshipExtractor
                rel_extractor = IntelligentRelationshipExtractor(nlp)
                relationship_results = rel_extractor.extract_relationships(text, context_results["entities"])

                # Ensure experience_metrics has average_tenure
                if "experience_metrics" in relationship_results:
                    relationship_results["experience_metrics"] = safe_get_experience_metrics(relationship_results)

                # Combine results
                combined_results = {**context_results, **relationship_results}
                combined_results["resume_analytics"] = {"completeness_score": 85, "ats_compatibility_score": 80}
                return combined_results

            except Exception as e:
                logger.warning(f"Relationship extraction failed: {e}")

        # Fallback: return context results with safe defaults
        context_results["work_experience"] = []
        context_results["education"] = []
        context_results["skills"] = {}
        context_results["achievements"] = []
        context_results["experience_metrics"] = {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0.0}
        context_results["career_progression"] = {}
        context_results["skill_evolution"] = {}
        context_results["resume_analytics"] = {"completeness_score": 70, "ats_compatibility_score": 75}

        return context_results

    except Exception as e:
        logger.error(f"Standard analysis failed: {e}")
        return _fallback_basic_extraction(text)

@app.post("/parse-resume-hybrid")
def parse_resume_hybrid(data: ResumeText):
    """
    Combined spaCy + semantic parsing for optimal results
    """
    start_time = time.time()

    try:
        text = data.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        logger.info("Processing resume with hybrid extraction")

        # Get spaCy results
        spacy_results = safe_context_extraction(text)

        # Get semantic results
        semantic_results = semantic_extractor.extract_semantic_entities(text)

        # Merge results
        merged_results = merge_extraction_results(spacy_results, semantic_results, text)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "method": "hybrid_extraction",
            "entities": merged_results.get("entities", []),
            "structured_data": {
                "personal_info": merged_results.get("personal_info", {}),
                "work_experience": merged_results.get("work_experience", []),
                "education": merged_results.get("education", []),
                "skills": merged_results.get("skills", {})
            },
            "processing_time": processing_time,
            "total_entities": len(merged_results.get("entities", [])),
            "components": {
                "spacy_entities": len(spacy_results.get("entities", [])),
                "semantic_entities": len(semantic_results.get("entities", []))
            }
        }

    except Exception as e:
        logger.error(f"Error in hybrid parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid processing failed: {str(e)}")

@app.post("/parse-resume-semantic")
def parse_resume_semantic(data: ResumeText):
    """
    Semantic-based resume parsing using pattern matching
    """
    start_time = time.time()

    try:
        text = data.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        logger.info("Processing resume with semantic extraction")

        # Extract using semantic approach
        results = semantic_extractor.extract_semantic_entities(text)

        processing_time = time.time() - start_time

        return {
            "success": True,
            "method": "semantic_extraction",
            "entities": results["entities"],
            "structured_data": results.get("structured_data", {}),
            "confidence": results.get("confidence", 0.0),
            "processing_time": processing_time,
            "total_entities": len(results["entities"]),
            "experience_analysis": {"average_tenure": 0.0, "total_jobs": 0}
        }

    except Exception as e:
        logger.error(f"Error in semantic parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Semantic processing failed: {str(e)}")


@app.get("/test-response")
def test_response():
    """Test endpoint to verify response format"""
    return {
        "entities": [
            {"text": "John Doe", "label": "NAME", "confidence": 0.9},
            {"text": "Software Engineer", "label": "TITLE", "confidence": 0.8}
        ],
        "message": "Test successful"
    }

# endpoint to test all importers
@app.post("/admin/test-all-importers")
def test_all_importers():
    """Tests the connection for all available job importers."""
    results = {}

    # Test The Muse
    try:
        # The Muse doesn't have an explicit test, so we assume it's okay if the class inits
        results['muse'] = {'status': 'ok', 'message': 'Assumed OK. No API key needed.'}
    except Exception as e:
        results['muse'] = {'status': 'error', 'message': str(e)}

    # Test Adzuna
    try:
        adzuna_importer = AdzunaJobImporter()
        if adzuna_importer.test_api_connection():
            results['adzuna'] = {'status': 'ok', 'message': 'Connection successful.'}
        else:
            results['adzuna'] = {'status': 'error', 'message': 'Connection test failed.'}
    except Exception as e:
        results['adzuna'] = {'status': 'error', 'message': str(e)}

    # Test JSearch
    try:
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        if not rapidapi_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        jsearch_importer = JSearchJobImporter(rapidapi_key)
        if jsearch_importer.test_api_connection():
            results['jsearch'] = {'status': 'ok', 'message': 'Connection successful.'}
        else:
            results['jsearch'] = {'status': 'error', 'message': 'Connection test failed.'}
    except Exception as e:
        results['jsearch'] = {'status': 'error', 'message': str(e)}

    # Test Remotive
    try:
        # Remotive is simple, we'll just try a quick fetch
        response = requests.get("https://remotive.com/api/remote-jobs?limit=1", timeout=10)
        response.raise_for_status()
        results['remotive'] = {'status': 'ok', 'message': 'Connection successful.'}
    except Exception as e:
        results['remotive'] = {'status': 'error', 'message': str(e)}

    return results


def import_all_jobs_direct(max_jobs_per_source: int = 25):  # Reduced from potentially unlimited
    """Direct function to run all job imports (for scheduler use)"""
    summaries = {}

    # Muse Importer
    try:
        muse_importer = MuseJobImporter()
        muse_importer.import_jobs(max_jobs=max_jobs_per_source)
        summaries['muse'] = muse_importer.get_import_summary()
    except Exception as e:
        logger.error(f"Muse import failed: {e}")
        summaries['muse'] = {'error': str(e)}

    # Adzuna Importer (with fixed limits)
    try:
        adzuna_importer = AdzunaJobImporter()
        adzuna_importer.import_jobs(max_jobs=max_jobs_per_source)  # Now has proper limits
        summaries['adzuna'] = adzuna_importer.get_import_summary()
    except Exception as e:
        logger.error(f"Adzuna import failed: {e}")
        summaries['adzuna'] = {'error': str(e)}

    # JSearch Importer
    try:
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        if rapidapi_key:
            jsearch_importer = JSearchJobImporter(rapidapi_key)
            jsearch_importer.import_jobs(max_jobs=max_jobs_per_source)
            summaries['jsearch'] = jsearch_importer.get_import_summary()
        else:
            summaries['jsearch'] = {'error': 'RAPIDAPI_KEY not set.'}
    except Exception as e:
        logger.error(f"JSearch import failed: {e}")
        summaries['jsearch'] = {'error': str(e)}

    # Remotive Importer
    try:
        remotive_importer = RemotiveJobImporter()
        remotive_importer.import_jobs(limit=max_jobs_per_source)
        summaries['remotive'] = remotive_importer.get_import_summary()
    except Exception as e:
        logger.error(f"Remotive import failed: {e}")
        summaries['remotive'] = {'error': str(e)}

    return {"status": "completed", "summaries": summaries}


@app.post("/admin/test-job-apis-comprehensive")
def test_job_apis_comprehensive():
    """Comprehensive test of all job APIs with detailed logging"""
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "environment_check": {},
        "api_tests": {},
        "database_check": {},
        "recommendations": []
    }

    # Environment Check
    try:
        test_results["environment_check"]["rapidapi_key"] = bool(os.getenv('RAPIDAPI_KEY'))
        test_results["environment_check"]["adzuna_app_id"] = bool(os.getenv('ADZUNA_APP_ID', '091309e2'))
        test_results["environment_check"]["adzuna_app_key"] = bool(
            os.getenv('ADZUNA_APP_KEY', 'dc9d659bbbb55ce320190bf9954f8f06'))
    except Exception as e:
        test_results["environment_check"]["error"] = str(e)

    # Test each API individually with more details
    apis_to_test = [
        ("muse", "The Muse API", lambda: MuseJobImporter().test_api_connection() if hasattr(MuseJobImporter,
                                                                                            'test_api_connection') else "No test method"),
        ("adzuna", "Adzuna API", lambda: AdzunaJobImporter().test_api_connection()),
        ("jsearch", "JSearch API",
         lambda: JSearchJobImporter(os.getenv('RAPIDAPI_KEY', '')).test_api_connection() if os.getenv(
             'RAPIDAPI_KEY') else "No RAPIDAPI_KEY"),
        ("remotive", "Remotive API", lambda: test_remotive_api())
    ]

    for api_key, api_name, test_func in apis_to_test:
        try:
            logger.info(f"Testing {api_name}...")
            result = test_func()
            test_results["api_tests"][api_key] = {
                "name": api_name,
                "status": "success" if result else "failed",
                "result": str(result)
            }
            logger.info(f"{api_name}: {'SUCCESS' if result else 'FAILED'}")
        except Exception as e:
            test_results["api_tests"][api_key] = {
                "name": api_name,
                "status": "error",
                "error": str(e)
            }
            logger.error(f"{api_name} test error: {e}")

    # Test database connection
    try:
        db_status = db.test_connection()
        test_results["database_check"] = {
            "status": "connected" if db_status else "failed",
            "message": "Database connection successful" if db_status else "Database connection failed"
        }
    except Exception as e:
        test_results["database_check"] = {
            "status": "error",
            "error": str(e)
        }

    # Generate recommendations
    failed_apis = [k for k, v in test_results["api_tests"].items() if v.get("status") in ["failed", "error"]]
    if failed_apis:
        test_results["recommendations"].append(f"Fix these APIs: {', '.join(failed_apis)}")

    if not test_results["environment_check"].get("rapidapi_key"):
        test_results["recommendations"].append("Set RAPIDAPI_KEY environment variable for JSearch API")

    return test_results


def test_remotive_api():
    """Test Remotive API connection"""
    try:
        response = requests.get("https://remotive.com/api/remote-jobs?limit=1", timeout=10)
        return response.status_code == 200
    except Exception as e:
        return False

@app.post("/admin/import-jobs")
def import_jobs_from_muse(categories: List[str] = None, max_jobs: int = 50):
    """
    Import jobs from The Muse API
    Admin endpoint to populate job database
    """
    try:
        start_time = time.time()

        logger.info(" Starting job import from The Muse...")

        # Initialize importer
        importer = MuseJobImporter()

        # Use default categories if none provided
        if categories is None:
            categories = [
                'Software Engineer',
                'Data Science',
                'Product Management',
                'Engineering',
                'Design'
            ]

        # Import jobs
        importer.import_jobs(categories=categories, max_jobs=max_jobs)

        # Get summary
        summary = importer.get_import_summary()
        processing_time = time.time() - start_time

        logger.info(f" Job import completed in {processing_time:.2f}s")

        return {
            "success": True,
            "summary": summary,
            "processing_time": processing_time,
            "categories_processed": categories,
            "message": f"Successfully imported {summary['imported']} jobs from The Muse"
        }

    except Exception as e:
        logger.error(f" Job import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job import failed: {str(e)}")

@app.post("/admin/import-all-jobs")
def import_all_jobs(max_jobs_per_source: int = 25):
    """Import jobs from all available sources"""
    return import_all_jobs_direct(max_jobs_per_source)

@app.post("/admin/import-adzuna-jobs")
def import_adzuna_jobs(keywords: List[str] = None, max_jobs: int = 50, location: str = "United States"):
    """
    Import jobs from Adzuna API
    Admin endpoint with better direct apply links
    """
    try:
        start_time = time.time()
        logger.info(" Starting Adzuna job import...")

        # Initialize importer
        importer = AdzunaJobImporter()

        # Use default keywords if none provided
        if keywords is None:
            keywords = [
                'software engineer',
                'data scientist',
                'product manager',
                'full stack developer',
                'machine learning engineer'
            ]

        # Import jobs
        importer.import_jobs(keywords=keywords, max_jobs=max_jobs, location=location)

        # Get summary
        summary = importer.get_import_summary()
        processing_time = time.time() - start_time

        logger.info(f" Adzuna import completed in {processing_time:.2f}s")

        return {
            "success": True,
            "summary": summary,
            "processing_time": processing_time,
            "keywords_processed": keywords,
            "message": f"Successfully imported {summary['imported']} jobs from Adzuna"
        }

    except Exception as e:
        logger.error(f" Adzuna import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Adzuna import failed: {str(e)}")


@app.post("/admin/import-jsearch-jobs")
def import_jsearch_jobs(
        keywords: List[str] = None,
        max_jobs: int = 50,
        location: str = "United States"
):
    """
    Import jobs from JSearch API (aggregates Indeed, LinkedIn, etc.)
    Admin endpoint with direct apply links
    """
    try:
        # Get RapidAPI key from environment
        rapidapi_key = os.getenv('RAPIDAPI_KEY')
        if not rapidapi_key:
            raise HTTPException(
                status_code=500,
                detail="RAPIDAPI_KEY not found in environment variables"
            )

        start_time = time.time()
        logger.info(" Starting JSearch job import...")

        # Initialize importer
        importer = JSearchJobImporter(rapidapi_key)

        # Use default keywords if none provided
        if keywords is None:
            keywords = [
                'software engineer',
                'data scientist',
                'product manager',
                'full stack developer',
                'machine learning engineer',
                'frontend developer',
                'backend developer',
                'DevOps engineer'
            ]

        # Import jobs
        stats = importer.import_jobs(keywords=keywords, max_jobs=max_jobs, location=location)

        processing_time = time.time() - start_time

        logger.info(f" JSearch import completed in {processing_time:.2f}s")

        return {
            "success": True,
            "summary": stats,
            "processing_time": processing_time,
            "keywords_processed": keywords,
            "location": location,
            "message": f"Successfully imported {stats['imported']} jobs from JSearch (Indeed, LinkedIn, etc.)"
        }

    except Exception as e:
        logger.error(f" JSearch import failed: {e}")
        raise HTTPException(status_code=500, detail=f"JSearch import failed: {str(e)}")

@app.post("/admin/import-remotive-jobs")
def trigger_remotive_import():
    """Import jobs from Remotive API"""
    try:
        importer = RemotiveJobImporter()
        importer.import_jobs(limit=20) # Process up to 20 jobs
        summary = importer.get_import_summary()

        return {
            "success": True,
            "message": f"Successfully imported {summary['successfully_imported']} jobs from Remotive.",
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Remotive import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Remotive import failed: {str(e)}")

@app.get("/admin/jobs/stats")
def get_job_stats():
    """
    Get statistics about jobs in the database
    """
    try:
        # Get all jobs
        all_jobs = db.get_all_jobs_with_embeddings()

        # Calculate stats
        total_jobs = len(all_jobs)
        companies = set()
        sources = {}
        experience_levels = {}

        for job in all_jobs:
            companies.add(job.get('company', ''))

            source = job.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            exp_level = job.get('experience_level', 'unknown')
            experience_levels[exp_level] = experience_levels.get(exp_level, 0) + 1

        return {
            "total_jobs": total_jobs,
            "unique_companies": len(companies),
            "jobs_by_source": sources,
            "jobs_by_experience_level": experience_levels,
            "sample_companies": list(companies)[:10]  # Show first 10 companies
        }

    except Exception as e:
        logger.error(f" Failed to get job stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job stats: {str(e)}")

def merge_extraction_results(spacy_results: Dict, semantic_results: Dict, original_text: str) -> Dict:
    """
    Intelligently merge spaCy and semantic extraction results with comprehensive error handling
    """
    try:
        merged = {
            "entities": [],
            "personal_info": {},
            "work_experience": [],
            "education": [],
            "skills": {},
            "achievements": [],
            "resume_analytics": {},
            "experience_metrics": {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0.0}
        }

        # Start with spaCy results as base (with safe copying)
        if spacy_results:
            merged["entities"] = spacy_results.get("entities", []).copy()
            merged["personal_info"] = spacy_results.get("personal_info", {}).copy()
            merged["work_experience"] = spacy_results.get("work_experience", []).copy()
            merged["education"] = spacy_results.get("education", []).copy()
            merged["skills"] = spacy_results.get("skills", {}).copy()
            merged["achievements"] = spacy_results.get("achievements", []).copy()

            # Handle experience_metrics safely
            merged["experience_metrics"] = safe_get_experience_metrics(spacy_results)

            # Handle resume_analytics safely
            analytics = spacy_results.get("resume_analytics", {})
            if analytics:
                merged["resume_analytics"] = analytics.copy()

        # Enhance with semantic results
        semantic_entities = semantic_results.get("entities", [])
        semantic_structured = semantic_results.get("structured_data", {})

        # Merge entities (avoid duplicates)
        existing_entities = set()
        for e in merged["entities"]:
            if isinstance(e, dict) and "text" in e and "label" in e:
                existing_entities.add((e["text"].lower(), e["label"]))

        for entity in semantic_entities:
            if isinstance(entity, dict) and "text" in entity and "label" in entity:
                entity_key = (entity["text"].lower(), entity["label"])
                if entity_key not in existing_entities:
                    # Add semantic entity
                    entity_copy = entity.copy()
                    entity_copy["source"] = "semantic_enhancement"
                    merged["entities"].append(entity_copy)

        # Enhance personal info with semantic findings
        semantic_contact = semantic_structured.get("contact_info", {})
        for field, value in semantic_contact.items():
            if value and isinstance(value, str):
                if field not in merged["personal_info"] or not merged["personal_info"].get(field):
                    merged["personal_info"][field] = value

        # Enhance skills with semantic findings
        semantic_skills = semantic_structured.get("skills", [])
        for skill in semantic_skills:
            if isinstance(skill, dict) and "name" in skill:
                category = skill.get("category", "Other")
                if category not in merged["skills"]:
                    merged["skills"][category] = []

                # Check if skill already exists
                existing_skill_names = []
                for s in merged["skills"][category]:
                    if isinstance(s, dict):
                        existing_skill_names.append(s.get("name", "").lower())
                    elif isinstance(s, str):
                        existing_skill_names.append(s.lower())

                if skill["name"].lower() not in existing_skill_names:
                    merged["skills"][category].append(skill.copy())

        # Enhance work experience safely
        semantic_work = semantic_structured.get("work_experience", [])
        for work in semantic_work:
            if isinstance(work, dict) and work.get("company"):
                # Check if already exists
                company_name = work.get("company", "").lower()
                existing_companies = [w.get("company", "").lower() for w in merged["work_experience"]
                                      if isinstance(w, dict)]

                if company_name not in existing_companies:
                    merged["work_experience"].append(work.copy())

        # Enhance achievements
        semantic_achievements = semantic_structured.get("achievements", [])
        for achievement in semantic_achievements:
            if isinstance(achievement, str) and achievement not in merged["achievements"]:
                merged["achievements"].append(achievement)

        return merged

    except Exception as e:
        logger.error(f"Error in merge_extraction_results: {e}")
        # Return spaCy results as fallback with safe experience_metrics
        if spacy_results:
            spacy_results["experience_metrics"] = safe_get_experience_metrics(spacy_results)
            return spacy_results
        else:
            return {
                "entities": semantic_results.get("entities", []),
                "personal_info": semantic_results.get("structured_data", {}).get("contact_info", {}),
                "work_experience": [],
                "education": [],
                "skills": {},
                "achievements": [],
                "resume_analytics": {},
                "experience_metrics": {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0.0}
            }


@app.post("/store-resume")
def store_resume(request: StoreResumeRequest):
    """
    Store user resume for job matching
    """
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    try:
        start_time = time.time()

        logger.info(f"Storing resume for user: {request.user_email}")

        # Prepare resume data for embedding generation
        resume_data = request.resume_data.copy()

        # If structured_data is provided separately, merge it
        if request.structured_data:
            resume_data['structured_data'] = request.structured_data

        # Ensure we have the resume text for embedding
        if 'resume_text' not in resume_data:
            # Try to reconstruct from structured data if missing
            resume_data['resume_text'] = _reconstruct_resume_text(resume_data)

        # Generate embeddings
        logger.info("Generating resume embeddings...")

        # Full resume embedding
        full_resume_embedding = embedding_service.generate_resume_embedding(resume_data)

        # Skills-specific embedding
        skills_list = _extract_skills_list(resume_data)
        skills_embedding = embedding_service.generate_skills_embedding(skills_list)

        # Experience embedding (using work experience text)
        experience_text = embedding_service._extract_experience_text(resume_data)
        experience_embedding = embedding_service.model.encode(experience_text) if experience_text else np.zeros(
            embedding_service.embedding_dim)

        # Store in database
        logger.info("Storing resume in database...")
        resume_id = db.store_user_resume(
            request.user_email,
            resume_data,
            {
                'full_resume': full_resume_embedding,
                'skills': skills_embedding,
                'experience': experience_embedding
            }
        )

        processing_time = time.time() - start_time

        logger.info(f" Successfully stored resume for {request.user_email} (ID: {resume_id})")

        return {
            "success": True,
            "message": "Resume stored successfully",
            "resume_id": resume_id,
            "user_email": request.user_email,
            "processing_time": processing_time,
            "embeddings_generated": {
                "full_resume": list(full_resume_embedding.shape),
                "skills": list(skills_embedding.shape),
                "experience": list(experience_embedding.shape)
            }
        }

    except Exception as e:
        logger.error(f" Failed to store resume for {request.user_email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store resume: {str(e)}")


def _reconstruct_resume_text(resume_data: Dict) -> str:
    """Reconstruct resume text from structured data if original text is missing"""
    try:
        text_parts = []

        structured = resume_data.get('structured_data', {})

        # Add work experience
        work_exp = structured.get('work_experience', [])
        for exp in work_exp:
            if isinstance(exp, dict):
                if exp.get('title'):
                    text_parts.append(exp['title'])
                if exp.get('company'):
                    text_parts.append(exp['company'])
                if exp.get('achievements'):
                    text_parts.extend(exp['achievements'])

        # Add skills
        skills = structured.get('skills', {})
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                for skill in skill_list:
                    if isinstance(skill, dict):
                        text_parts.append(skill.get('name', ''))
                    else:
                        text_parts.append(str(skill))

        # Add education
        education = structured.get('education', [])
        for edu in education:
            if isinstance(edu, dict):
                if edu.get('degree'):
                    text_parts.append(edu['degree'])
                if edu.get('school'):
                    text_parts.append(edu['school'])

        # Add entities
        entities = resume_data.get('entities', [])  # Note: changed from 'extracted_entities'
        for entity in entities:
            if isinstance(entity, dict):
                text_parts.append(entity.get('text', ''))

        return " ".join(filter(None, text_parts))

    except Exception as e:
        logger.error(f"Failed to reconstruct resume text: {e}")
        return "Resume content"


def _extract_skills_list(resume_data: Dict) -> List[str]:
    """Extract a simple list of skills from resume data"""
    try:
        skills_list = []

        # From structured data
        structured = resume_data.get('structured_data', {})
        skills = structured.get('skills', {})

        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                for skill in skill_list:
                    if isinstance(skill, dict):
                        skill_name = skill.get('name', '')
                        if skill_name:
                            skills_list.append(skill_name)
                    else:
                        skills_list.append(str(skill))

        # From work experience
        work_exp = structured.get('work_experience', [])
        for exp in work_exp:
            if isinstance(exp, dict) and exp.get('skills'):
                skills_list.extend(exp['skills'])

        # From entities (changed from 'extracted_entities')
        entities = resume_data.get('entities', [])
        for entity in entities:
            if isinstance(entity, dict) and entity.get('label') in ['SKILL', 'TECHNOLOGY', 'TOOL']:
                skill_text = entity.get('text', '')
                if skill_text:
                    skills_list.append(skill_text)

        # Remove duplicates and clean
        unique_skills = list(set([skill.strip() for skill in skills_list if skill.strip()]))

        return unique_skills

    except Exception as e:
        logger.error(f"Failed to extract skills list: {e}")
        return []

def _generate_improvement_suggestions(results: Dict) -> List[str]:
    """Generate personalized improvement suggestions with error handling"""
    try:
        suggestions = []
        analytics = results.get("resume_analytics", {})

        # Based on completeness score
        if analytics.get("completeness_score", 0) < 80:
            if not results.get("work_experience"):
                suggestions.append("Add detailed work experience with specific achievements")
            if not results.get("skills"):
                suggestions.append("Include a dedicated skills section with relevant technologies")

            # Check for missing contact info
            entities = results.get("entities", [])
            has_email = any(e.get("label") == "EMAIL" for e in entities if isinstance(e, dict))
            has_phone = any(e.get("label") == "PHONE" for e in entities if isinstance(e, dict))

            if not has_email:
                suggestions.append("Add a professional email address")
            if not has_phone:
                suggestions.append("Include your phone number for easy contact")

        # Based on ATS compatibility
        if analytics.get("ats_compatibility_score", 0) < 85:
            suggestions.append("Use standard section headers (Experience, Education, Skills)")
            suggestions.append("Include relevant keywords from your target job descriptions")
            suggestions.append("Use simple, clean formatting without complex graphics")

        # Based on career progression
        career_prog = results.get("career_progression", {})
        if career_prog.get("trend") == "lateral":
            suggestions.append("Highlight leadership responsibilities and increasing scope of work")

        # Based on achievements
        if not results.get("achievements"):
            suggestions.append("Quantify your accomplishments with specific numbers and metrics")

        return suggestions[:5] if suggestions else ["Resume analysis completed successfully"]

    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return ["Enable intelligent analysis for personalized suggestions"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)