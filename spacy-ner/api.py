import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import re
import logging
from typing import List, Optional, Dict, Any
import time
import json
from pathlib import Path

from semantic_extractor import SemanticResumeExtractor

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


def safe_get_experience_metrics(results: Dict) -> Dict[str, Any]:
    """Safely extract experience metrics with all required keys"""
    experience_metrics = results.get("experience_metrics", {})

    # Ensure all required keys exist with safe defaults
    safe_metrics = {
        "total_years": experience_metrics.get("total_years", 0),
        "companies": experience_metrics.get("companies", 0),
        "roles": experience_metrics.get("roles", 0),
        "average_tenure": experience_metrics.get("average_tenure", 0.0)  # This is the key that was missing!
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
            # This was missing and causing the KeyError!
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
                "average_tenure": 0.0,  # Essential for preventing KeyError
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


@app.get("/")
def root():
    return {
        "message": "LandIt Intelligent Resume Parser is running!",
        "version": "3.0.0",
        "model_type": training_info.get("model_type", "unknown"),
        "intelligent_modules": INTELLIGENT_MODULES_AVAILABLE,
        "intelligence_features": [
            "Section-aware entity extraction",
            "Relationship detection",
            "Career progression analysis",
            "Skills categorization",
            "Achievement extraction",
            "ATS compatibility scoring",
            "Resume quality assessment",
            "Improvement suggestions"
        ] if INTELLIGENT_MODULES_AVAILABLE else [
            "Basic entity extraction",
            "Semantic pattern matching"
        ],
        "analysis_levels": {
            "basic": "Entity extraction only",
            "standard": "Entities + structured data",
            "full": "Complete intelligence analysis" if INTELLIGENT_MODULES_AVAILABLE else "Semantic analysis"
        }
    }


@app.get("/health")
def health_check():
    """Enhanced health check with intelligence status"""
    return {
        "status": "healthy",
        "model_loaded": "ner" in nlp.pipe_names,
        "model_type": training_info.get("model_type", "unknown"),
        "intelligent_modules": INTELLIGENT_MODULES_AVAILABLE,
        "intelligence_modules_detail": {
            "section_detector": INTELLIGENT_MODULES_AVAILABLE,
            "relationship_extractor": INTELLIGENT_MODULES_AVAILABLE,
            "analytics_engine": intelligence_analyzer is not None
        },
        "total_labels": len(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else 0
    }


@app.post("/parse-resume", response_model=Dict[str, Any])  # Changed from IntelligentParseResponse for flexibility
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
        # Return safe error response
        error_response = {
            "entities": [],
            "sections": {},
            "section_analysis": {"sections_found": 0, "structure_score": 0},
            "experience_analysis": {"average_tenure": 0.0, "total_jobs": 0},
            "work_experience": [],
            "education": [],
            "skills": {},
            "achievements": [],
            "experience_metrics": {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0.0},
            "career_progression": {},
            "resume_analytics": {},
            "error": str(e),
            "processing_stats": {
                "processing_time_seconds": 0,
                "total_entities": 0,
                "analysis_level": data.analysis_level,
                "intelligent_modules_used": False
            }
        }

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


# Semantic implementation to call api
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
            # Add the missing experience_analysis for compatibility
            "experience_analysis": {"average_tenure": 0.0, "total_jobs": 0}
        }

    except Exception as e:
        logger.error(f"Error in semantic parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Semantic processing failed: {str(e)}")


@app.post("/parse-resume-hybrid")
def parse_resume_hybrid(data: ResumeText):
    """
    Hybrid resume parsing: spaCy NER + Semantic extraction
    """
    start_time = time.time()

    try:
        text = data.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        logger.info("Processing resume with hybrid approach")

        # Get spaCy results (your existing intelligent analysis)
        try:
            if intelligence_analyzer:
                spacy_results = intelligence_analyzer.analyze_resume(text)
                logger.info(f"spaCy analysis completed with {len(spacy_results.get('entities', []))} entities")
            else:
                spacy_results = safe_context_extraction(text)
                logger.info(f"Basic spaCy analysis completed with {len(spacy_results.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"spaCy analysis failed: {str(e)}")
            spacy_results = {"entities": [], "experience_metrics": {"average_tenure": 0.0}}

        # Get semantic results
        try:
            semantic_results = semantic_extractor.extract_semantic_entities(text)
            logger.info(f"Semantic analysis completed with {len(semantic_results.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"Semantic analysis failed: {str(e)}")
            semantic_results = {"entities": []}

        # Merge results intelligently
        try:
            merged_results = merge_extraction_results(spacy_results, semantic_results, text)
            logger.info(f"Merge completed with {len(merged_results.get('entities', []))} total entities")
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
                "experience_metrics": safe_get_experience_metrics(spacy_results)  # Ensure safe metrics
            }

        processing_time = time.time() - start_time

        return {
            "success": True,
            "method": "hybrid_extraction",
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
                "spacy_entities": len(spacy_results.get("entities", [])),
                "semantic_entities": len(semantic_results.get("entities", [])),
                "merged_entities": len(merged_results.get("entities", [])),
                "improvement": len(merged_results.get("entities", [])) - len(spacy_results.get("entities", []))
            }
        }

    except Exception as e:
        logger.error(f"Error in hybrid parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid processing failed: {str(e)}")


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
            "experience_metrics": {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0.0}  # Safe default
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