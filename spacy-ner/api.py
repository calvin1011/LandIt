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

# Import our intelligence modules
from intelligent_section_detector import ContextAwareEntityExtractor, IntelligentSectionDetector
from relationship_extractor import ResumeIntelligenceAnalyzer

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

# Initialize intelligence analyzer
intelligence_analyzer = ResumeIntelligenceAnalyzer(nlp)

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


@app.get("/")
def root():
    return {
        "message": "LandIt Intelligent Resume Parser is running!",
        "version": "3.0.0",
        "model_type": training_info.get("model_type", "unknown"),
        "intelligence_features": [
            "Section-aware entity extraction",
            "Relationship detection",
            "Career progression analysis",
            "Skills categorization",
            "Achievement extraction",
            "ATS compatibility scoring",
            "Resume quality assessment",
            "Improvement suggestions"
        ],
        "analysis_levels": {
            "basic": "Entity extraction only",
            "standard": "Entities + structured data",
            "full": "Complete intelligence analysis"
        }
    }


@app.get("/health")
def health_check():
    """Enhanced health check with intelligence status"""
    return {
        "status": "healthy",
        "model_loaded": "ner" in nlp.pipe_names,
        "model_type": training_info.get("model_type", "unknown"),
        "intelligence_modules": {
            "section_detector": True,
            "relationship_extractor": True,
            "analytics_engine": True
        },
        "total_labels": len(nlp.get_pipe('ner').labels) if "ner" in nlp.pipe_names else 0
    }


@app.post("/parse-resume", response_model=IntelligentParseResponse)
def parse_resume_intelligent(data: ResumeText):
    """
    Intelligent resume parsing with multiple analysis levels
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

        # Perform analysis based on requested level
        if data.analysis_level == "basic":
            results = _perform_basic_analysis(text)
        elif data.analysis_level == "standard":
            results = _perform_standard_analysis(text)
        else:  # full
            results = intelligence_analyzer.analyze_resume(text)

        processing_time = time.time() - start_time

        # Generate suggestions if requested
        suggestions = None
        if data.include_suggestions and data.analysis_level == "full":
            suggestions = _generate_improvement_suggestions(results)

        # Format response
        response = _format_intelligent_response(results, processing_time, suggestions)

        logger.info(f"Completed {data.analysis_level} analysis in {processing_time:.2f}s")
        return response

    except Exception as e:
        logger.error(f"Error in intelligent parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/analyze-skills")
def analyze_skills_endpoint(data: ResumeText):
    """
    Focused skill analysis endpoint
    """
    try:
        results = intelligence_analyzer.analyze_resume(data.text)

        skills_analysis = {
            "skills_by_category": results["skills"],
            "skill_evolution": results["skill_evolution"],
            "skills_analysis": results["resume_analytics"]["skills_analysis"],
            "recommendations": _generate_skill_recommendations(results["skills"])
        }

        return skills_analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill analysis failed: {str(e)}")


@app.post("/career-insights")
def career_insights_endpoint(data: ResumeText):
    """
    Focused career progression analysis
    """
    try:
        results = intelligence_analyzer.analyze_resume(data.text)

        career_insights = {
            "work_experience": results["work_experience"],
            "experience_metrics": results["experience_metrics"],
            "career_progression": results["career_progression"],
            "achievements": results["achievements"],
            "career_recommendations": _generate_career_recommendations(results)
        }

        return career_insights

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Career analysis failed: {str(e)}")


@app.post("/resume-score")
def resume_score_endpoint(data: ResumeText):
    """
    Resume quality scoring endpoint
    """
    try:
        results = intelligence_analyzer.analyze_resume(data.text)
        analytics = results["resume_analytics"]

        scoring = {
            "overall_score": analytics["overall_quality_score"],
            "completeness_score": analytics["completeness_score"],
            "ats_compatibility_score": analytics["ats_compatibility_score"],
            "strengths": analytics["strengths"],
            "red_flags": analytics["red_flags"],
            "improvement_areas": _identify_improvement_areas(analytics),
            "score_breakdown": {
                "contact_info": _score_contact_info(results),
                "work_experience": _score_work_experience(results),
                "education": _score_education(results),
                "skills": _score_skills(results),
                "achievements": _score_achievements(results)
            }
        }

        return scoring

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume scoring failed: {str(e)}")

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
            "total_entities": len(results["entities"])
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
            spacy_results = intelligence_analyzer.analyze_resume(text)
            logger.info(f"spaCy analysis completed with {len(spacy_results.get('entities', []))} entities")
        except Exception as e:
            logger.error(f"spaCy analysis failed: {str(e)}")
            spacy_results = {"entities": []}

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
                "resume_analytics": spacy_results.get("resume_analytics", {})
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
    Intelligently merge spaCy and semantic extraction results with error handling
    """
    try:
        merged = {
            "entities": [],
            "personal_info": {},
            "work_experience": [],
            "education": [],
            "skills": {},
            "achievements": [],
            "resume_analytics": {}
        }

        # Start with spaCy results as base (with safe copying)
        if spacy_results:
            merged["entities"] = spacy_results.get("entities", []).copy()
            merged["personal_info"] = spacy_results.get("personal_info", {}).copy()
            merged["work_experience"] = spacy_results.get("work_experience", []).copy()
            merged["education"] = spacy_results.get("education", []).copy()
            merged["skills"] = spacy_results.get("skills", {}).copy()
            merged["achievements"] = spacy_results.get("achievements", []).copy()

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
        logger.error(f"Error in merge_extraction_results: {str(e)}")
        # Return spaCy results as fallback
        if spacy_results:
            return spacy_results
        else:
            return {
                "entities": semantic_results.get("entities", []),
                "personal_info": semantic_results.get("structured_data", {}).get("contact_info", {}),
                "work_experience": [],
                "education": [],
                "skills": {},
                "achievements": [],
                "resume_analytics": {}
            }

def _perform_basic_analysis(text: str) -> Dict:
    """Basic entity extraction only"""
    context_extractor = ContextAwareEntityExtractor(nlp)
    return context_extractor.extract_with_context(text)


def _perform_standard_analysis(text: str) -> Dict:
    """Standard analysis with structured data but limited intelligence"""
    context_results = _perform_basic_analysis(text)

    # Add basic relationship extraction
    from relationship_extractor import IntelligentRelationshipExtractor
    rel_extractor = IntelligentRelationshipExtractor(nlp)
    relationship_results = rel_extractor.extract_relationships(text, context_results["entities"])

    # Combine results
    return {
        **context_results,
        **relationship_results,
        "resume_analytics": {"completeness_score": 85, "ats_compatibility_score": 80}  # Simplified
    }


def _format_intelligent_response(results: Dict, processing_time: float,
                                 suggestions: Optional[List[str]]) -> IntelligentParseResponse:
    """Format results into response model"""

    # Convert entities
    entities = []
    for entity in results.get("entities", []):
        entities.append(EntityResponse(
            text=entity["text"],
            label=entity["label"],
            start=entity.get("start"),
            end=entity.get("end"),
            confidence=entity.get("confidence"),
            source=entity.get("source"),
            section=entity.get("section")
        ))

    # Convert work experience
    work_experience = []
    for exp in results.get("work_experience", []):
        work_experience.append(WorkExperienceResponse(
            title=exp["title"],
            company=exp["company"],
            start_date=exp.get("start_date"),
            end_date=exp.get("end_date"),
            skills=exp.get("skills", []),
            achievements=exp.get("achievements", [])
        ))

    # Convert education
    education = []
    for edu in results.get("education", []):
        education.append(EducationResponse(
            degree=edu["degree"],
            school=edu.get("school"),
            year=edu.get("year"),
            gpa=edu.get("gpa")
        ))

    # Convert skills
    skills = []
    for category, skill_list in results.get("skills", {}).items():
        skills.append(SkillCategoryResponse(
            category=category,
            skills=skill_list
        ))

    # Processing stats
    processing_stats = {
        "processing_time_seconds": round(processing_time, 3),
        "total_entities": len(entities),
        "work_experience_count": len(work_experience),
        "education_count": len(education),
        "skill_categories": len(skills),
        "achievements_count": len(results.get("achievements", []))
    }

    # Model info
    model_info = {
        "model_type": training_info.get("model_type", "unknown"),
        "version": "3.0.0",
        "intelligence_level": "full"
    }

    return IntelligentParseResponse(
        entities=entities,
        work_experience=work_experience,
        education=education,
        skills=skills,
        achievements=results.get("achievements", []),
        experience_metrics=results.get("experience_metrics", {}),
        career_progression=results.get("career_progression", {}),
        resume_analytics=results.get("resume_analytics", {}),
        processing_stats=processing_stats,
        model_info=model_info,
        suggestions=suggestions
    )


def _generate_improvement_suggestions(results: Dict) -> List[str]:
    """Generate personalized improvement suggestions"""
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
        has_email = any(e["label"] == "EMAIL" for e in entities)
        has_phone = any(e["label"] == "PHONE" for e in entities)

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

    # Based on skills analysis
    skills_analysis = analytics.get("skills_analysis", {})
    if skills_analysis.get("skills_with_proficiency", 0) == 0:
        suggestions.append("Indicate your proficiency level for key skills (e.g., Expert, Proficient)")

    return suggestions[:5]  # Limit to top 5 suggestions


def _generate_skill_recommendations(skills: Dict) -> List[str]:
    """Generate skill-specific recommendations"""
    recommendations = []

    # Check for trending skills in each category
    trending_skills = {
        "Programming Languages": ["Python", "TypeScript", "Go", "Rust"],
        "Web Technologies": ["React", "Next.js", "GraphQL", "Svelte"],
        "Cloud & DevOps": ["Kubernetes", "Terraform", "Docker", "AWS Lambda"],
        "Data & Analytics": ["Apache Spark", "dbt", "Airflow", "Snowflake"]
    }

    for category, category_skills in skills.items():
        if category in trending_skills:
            current_skills = [skill["name"].lower() for skill in category_skills]
            missing_trending = []

            for trending in trending_skills[category]:
                if trending.lower() not in current_skills:
                    missing_trending.append(trending)

            if missing_trending and len(missing_trending) <= 3:
                recommendations.append(
                    f"Consider adding trending {category.lower()}: {', '.join(missing_trending[:2])}")

    return recommendations[:3]


def _generate_career_recommendations(results: Dict) -> List[str]:
    """Generate career-focused recommendations"""
    recommendations = []

    exp_metrics = results.get("experience_metrics", {})
    career_prog = results.get("career_progression", {})

    # Experience level recommendations
    total_years = exp_metrics.get("total_years", 0)
    if total_years < 2:
        recommendations.append("Focus on highlighting internships, projects, and relevant coursework")
    elif total_years > 10:
        recommendations.append("Consider emphasizing leadership and strategic contributions")

    # Career progression recommendations
    if career_prog.get("trend") == "upward":
        recommendations.append("Excellent career progression - continue highlighting increasing responsibilities")
    elif career_prog.get("seniority_growth", 0) < 0:
        recommendations.append("Consider emphasizing skill development and expanded scope of work")

    # Company diversity
    if exp_metrics.get("companies", 0) == 1:
        recommendations.append("Consider highlighting diverse project experience within your organization")
    elif exp_metrics.get("companies", 0) > 5:
        recommendations.append("Focus on demonstrating consistency and deep impact at each role")

    return recommendations[:3]


def _identify_improvement_areas(analytics: Dict) -> List[str]:
    """Identify specific areas for improvement"""
    areas = []

    completeness = analytics.get("completeness_score", 0)
    ats_score = analytics.get("ats_compatibility_score", 0)

    if completeness < 70:
        areas.append("Resume completeness - add missing sections")
    if ats_score < 75:
        areas.append("ATS optimization - improve keyword usage and formatting")
    if analytics.get("red_flags"):
        areas.append("Address potential red flags identified")

    skills_analysis = analytics.get("skills_analysis", {})
    if skills_analysis.get("depth_score", 0) < 50:
        areas.append("Skill depth - add proficiency levels and years of experience")

    return areas


def _score_contact_info(results: Dict) -> int:
    """Score contact information completeness"""
    score = 0
    entities = results.get("entities", [])

    has_name = any(e["label"] in ["NAME", "PERSON"] for e in entities)
    has_email = any(e["label"] == "EMAIL" for e in entities)
    has_phone = any(e["label"] == "PHONE" for e in entities)
    has_location = any(e["label"] in ["LOCATION", "GPE"] for e in entities)

    if has_name: score += 25
    if has_email: score += 30
    if has_phone: score += 25
    if has_location: score += 20

    return score


def _score_work_experience(results: Dict) -> int:
    """Score work experience section quality"""
    work_exp = results.get("work_experience", [])
    if not work_exp:
        return 0

    score = 0
    total_possible = len(work_exp) * 100

    for exp in work_exp:
        exp_score = 0
        if exp.get("title"): exp_score += 20
        if exp.get("company"): exp_score += 20
        if exp.get("start_date") or exp.get("end_date"): exp_score += 20
        if exp.get("skills"): exp_score += 20
        if exp.get("achievements"): exp_score += 20

        score += exp_score

    return min(100, (score / total_possible) * 100) if total_possible > 0 else 0


def _score_education(results: Dict) -> int:
    """Score education section quality"""
    education = results.get("education", [])
    if not education:
        return 50  # Not everyone needs education

    score = 0
    for edu in education:
        edu_score = 0
        if edu.get("degree"): edu_score += 40
        if edu.get("school"): edu_score += 30
        if edu.get("year"): edu_score += 20
        if edu.get("gpa"): edu_score += 10

        score = max(score, edu_score)  # Take best education entry

    return score


def _score_skills(results: Dict) -> int:
    """Score skills section quality"""
    skills = results.get("skills", {})
    if not skills:
        return 0

    total_skills = sum(len(skill_list) for skill_list in skills.values())
    categories = len(skills)

    # Base score for having skills
    score = 40

    # Bonus for multiple categories
    score += min(30, categories * 10)

    # Bonus for skill quantity
    score += min(20, total_skills * 2)

    # Bonus for proficiency levels
    skills_with_prof = 0
    for skill_list in skills.values():
        for skill in skill_list:
            if skill.get("proficiency"):
                skills_with_prof += 1

    if skills_with_prof > 0:
        score += min(10, skills_with_prof * 2)

    return min(100, score)


def _score_achievements(results: Dict) -> int:
    """Score achievements and quantified results"""
    achievements = results.get("achievements", [])
    if not achievements:
        return 0

    score = len(achievements) * 15  # 15 points per achievement

    # Bonus for quantified achievements
    quantified = sum(1 for ach in achievements if re.search(r'\d+[%$]|\d+\s*(?:years?|months?)', ach))
    score += quantified * 10

    return min(100, score)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)