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
from fastapi.middleware.cors import CORSMiddleware

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

from embedding_service import ResumeJobEmbeddingService
from database import db
from typing import List, Optional, Dict, Any

# Import our intelligence modules with error handling
try:
    from intelligent_section_detector import ContextAwareEntityExtractor, IntelligentSectionDetector
    from relationship_extractor import ResumeIntelligenceAnalyzer

    INTELLIGENT_MODULES_AVAILABLE = True
    print("✅ Intelligent modules loaded successfully")
except ImportError as e:
    print(f"⚠️ Intelligent modules not available: {e}")
    INTELLIGENT_MODULES_AVAILABLE = False

semantic_extractor = SemanticResumeExtractor()

try:
    embedding_service = ResumeJobEmbeddingService()
    logger.info("✅ Embedding service initialized for job matching")
except Exception as e:
    logger.error(f"❌ Failed to initialize embedding service: {e}")
    embedding_service = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load hybrid trained spaCy model
try:
    model_path = "output_hybrid"
    nlp = spacy.load(model_path)
    logger.info(f"✅ Successfully loaded HYBRID model from: {model_path}")

    metadata_path = Path(model_path) / "training_info.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            training_info = json.load(f)
        logger.info(
            f"📊 Model info: {training_info.get('model_type', 'unknown')} with {training_info.get('total_labels', 'unknown')} labels")
    else:
        training_info = {}

except Exception as e:
    logger.error(f"❌ Failed to load hybrid model: {e}")
    try:
        nlp = spacy.load("output")
        training_info = {"model_type": "custom_only"}
        logger.warning("⚠️ Using fallback custom model")
    except Exception as e2:
        logger.error(f"❌ Failed to load any model: {e2}")
        nlp = spacy.load("en_core_web_sm")
        training_info = {"model_type": "pretrained_only"}
        logger.warning("⚠️ Using pretrained model only")

app = FastAPI(title="LandIt Intelligent Resume Parser", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3003",
        "http://127.0.0.1:3003"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize intelligence analyzer with error handling
intelligence_analyzer = None
if INTELLIGENT_MODULES_AVAILABLE:
    try:
        intelligence_analyzer = ResumeIntelligenceAnalyzer(nlp)
        logger.info("✅ Intelligence analyzer initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize intelligence analyzer: {e}")
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
    top_k: int = 10
    min_similarity: float = 0.3

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
    Find job matches for a user's resume
    """
    if not embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not available")

    try:
        start_time = time.time()

        # Get user's resume
        user_resume = db.get_user_resume(match_request.user_email)
        if not user_resume:
            raise HTTPException(status_code=404, detail="User resume not found. Please upload a resume first.")

        # Get all active jobs
        all_jobs = db.get_all_jobs_with_embeddings()
        if not all_jobs:
            return {
                "matches": [],
                "total_found": 0,
                "message": "No active job postings available"
            }

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

            # Calculate experience match (simplified)
            user_years = user_resume.get('years_of_experience', 0)
            job_level = job.get('experience_level', 'mid')
            experience_match = calculate_experience_match(user_years, job_level)

            # Calculate location match
            location_match = calculate_location_match(
                user_resume.get('preferred_locations', []),
                job.get('location', ''),
                job.get('remote_allowed', False)
            )

            # Calculate overall score with improved weighting
            overall_score = (
                    semantic_similarity * 0.25 +
                    skills_similarity * 0.45 +  # Increased skills weight
                    experience_match * 0.20 +
                    location_match * 0.10
            )

            # Only include jobs above minimum similarity
            if overall_score >= match_request.min_similarity:
                # Extract matching skills
                user_skills = extract_user_skills(user_resume)
                job_skills = job.get('skills_required', [])
                skill_matches = list(set(user_skills) & set([s.lower() for s in job_skills]))
                skill_gaps = list(set([s.lower() for s in job_skills]) - set(user_skills))

                matches.append({
                    'job_id': job['id'],
                    'title': job['title'],
                    'company': job['company'],
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
                    'skill_gaps': skill_gaps[:5],  # Top 5 missing skills
                    'match_explanation': generate_match_explanation(
                        overall_score, skill_matches, skill_gaps, experience_match
                    )
                })

        # Sort by overall score
        matches.sort(key=lambda x: x['overall_score'], reverse=True)

        # Limit results
        matches = matches[:match_request.top_k]

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

        return {
            "matches": matches,
            "total_found": len(matches),
            "total_jobs_analyzed": len(all_jobs),
            "user_email": match_request.user_email,
            "processing_time": processing_time,
            "recommendation_ids": recommendation_ids
        }

    except Exception as e:
        logger.error(f"Job matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Job matching failed: {str(e)}")


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
        include_suggestions: bool = True
):
    """
    Parse resume from uploaded file (PDF, DOCX, TXT)
    This endpoint replaces your Node.js backend functionality
    """
    start_time = time.time()

    try:
        logger.info(f"📄 Processing file: {file.filename} ({file.content_type})")

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

        logger.info(f"✅ Extracted {len(text)} characters from {file.filename}")

        # Use your existing parsing logic
        data = ResumeText(text=text, analysis_level=analysis_level, include_suggestions=include_suggestions)
        result = parse_resume_intelligent(data)

        # Add file metadata to result
        result["file_info"] = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(file_content),
            "text_length": len(text)
        }

        logger.info(f"🎉 Successfully processed {file.filename} in {time.time() - start_time:.2f}s")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ File processing error: {e}")
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


@app.post("/parse-resume-file")
async def parse_resume_file(
        file: UploadFile = File(...)
):
    """
    Parse resume from uploaded file using optimal hybrid processing
    Automatically selects the best combination of AI techniques for maximum accuracy
    """
    start_time = time.time()

    try:
        logger.info(f"📄 Processing file: {file.filename} ({file.content_type})")

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

        logger.info(f"✅ Extracted {len(text)} characters from {file.filename}")

        # Use hybrid processing for optimal results
        logger.info("🔀 Using hybrid processing for optimal extraction")

        try:
            # Get spaCy results (intelligent analysis)
            if intelligence_analyzer:
                spacy_results = intelligence_analyzer.analyze_resume(text)
                logger.info(f"📊 spaCy analysis: {len(spacy_results.get('entities', []))} entities")
            else:
                spacy_results = safe_context_extraction(text)
                logger.info(f"📊 Basic spaCy analysis: {len(spacy_results.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"spaCy analysis failed: {str(e)}")
            spacy_results = {"entities": [], "experience_metrics": {"average_tenure": 0.0}}

        # Get semantic results
        try:
            semantic_results = semantic_extractor.extract_semantic_entities(text)
            logger.info(f"🎯 Semantic analysis: {len(semantic_results.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"Semantic analysis failed: {str(e)}")
            semantic_results = {"entities": []}

        # Merge results intelligently
        try:
            merged_results = merge_extraction_results(spacy_results, semantic_results, text)
            logger.info(f"✅ Hybrid merge: {len(merged_results.get('entities', []))} total entities")
        except Exception as e:
            logger.error(f"Merge failed: {str(e)}")
            # Fallback: combine entities directly
            merged_results = {
                "entities": spacy_results.get("entities", []) + semantic_results.get("entities", []),
                "personal_info": semantic_results.get("structured_data", {}).get("contact_info", {}),
                "work_experience": spacy_results.get("work_experience", []),
                "education": spacy_results.get("education", []),
                "skills": spacy_results.get("skills", {}),
                "achievements": spacy_results.get("achievements", []),
                "resume_analytics": spacy_results.get("resume_analytics", {}),
                "experience_metrics": safe_get_experience_metrics(spacy_results)
            }

        processing_time = time.time() - start_time

        # Build comprehensive response
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

        logger.info(f"🎉 Successfully processed {file.filename} in {processing_time:.2f}s using hybrid approach")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File processing error: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

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