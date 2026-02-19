import re
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import spacy
from spacy.matcher import Matcher

STANDARD_SECTION_HEADERS = [
    r"work\s+experience", r"professional\s+experience", r"employment", r"experience",
    r"education", r"academic", r"skills", r"technical\s+skills", r"competencies",
    r"summary", r"professional\s+summary", r"objective", r"career\s+summary",
]
NON_STANDARD_HEADER_HINTS = ["journey", "story", "about me", "my background", "where i've", "life so far"]
DATE_YEAR = re.compile(r"\b(19|20)\d{2}\b")
DATE_MONTH_YEAR = re.compile(
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*(\.?\s*)?\d{4}",
    re.IGNORECASE,
)

@dataclass
class WorkExperience:
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    skills: List[str] = None
    achievements: List[str] = None
    location: Optional[str] = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.achievements is None:
            self.achievements = []


@dataclass
class EducationRecord:
    degree: str
    field: Optional[str] = None
    school: str = None
    year: Optional[str] = None
    gpa: Optional[str] = None
    location: Optional[str] = None


@dataclass
class SkillGroup:
    category: str
    skills: List[str]
    proficiency: Optional[str] = None
    years_experience: Optional[int] = None


class IntelligentRelationshipExtractor:
    """
    Extracts relationships between entities and builds structured resume data
    """

    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.matcher = Matcher(nlp_model.vocab)
        self._setup_patterns()

        # Skill categories for intelligent grouping
        self.skill_categories = {
            "Programming Languages": [
                "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
                "rust", "php", "swift", "kotlin", "scala", "r", "matlab"
            ],
            "Web Technologies": [
                "react", "angular", "vue", "html", "css", "sass", "bootstrap", "jquery",
                "nodejs", "express", "django", "flask", "spring", "rails"
            ],
            "Databases": [
                "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "sqlite",
                "oracle", "sql server", "dynamodb", "cassandra"
            ],
            "Cloud & DevOps": [
                "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "gitlab",
                "terraform", "ansible", "prometheus", "grafana"
            ],
            "Data & Analytics": [
                "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark",
                "hadoop", "tableau", "power bi", "excel"
            ],
            "Tools & Frameworks": [
                "git", "jira", "confluence", "slack", "figma", "photoshop", "linux"
            ]
        }

    def _setup_patterns(self):
        """Setup spaCy patterns for relationship extraction"""

        # Job title + company patterns
        job_company_patterns = [
            [{"LOWER": {"IN": ["software", "senior", "junior", "lead", "principal"]}},
             {"LOWER": {"IN": ["engineer", "developer", "analyst", "manager"]}},
             {"LOWER": "at"},
             {"ENT_TYPE": {"IN": ["ORG", "COMPANY"]}}],

            [{"ENT_TYPE": {"IN": ["TITLE", "JOB"]}},
             {"LOWER": "|"},
             {"ENT_TYPE": {"IN": ["ORG", "COMPANY"]}}],

            [{"ENT_TYPE": {"IN": ["TITLE", "JOB"]}},
             {"LOWER": "with"},
             {"ENT_TYPE": {"IN": ["ORG", "COMPANY"]}}]
        ]

        # Date range patterns
        date_range_patterns = [
            [{"SHAPE": "dddd"}, {"LOWER": "-"}, {"SHAPE": "dddd"}],  # 2020-2023
            [{"SHAPE": "dddd"}, {"LOWER": "to"}, {"SHAPE": "dddd"}],  # 2020 to 2023
            [{"LOWER": {"REGEX": r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"}},
             {"SHAPE": "dddd"}, {"LOWER": "-"},
             {"LOWER": {"REGEX": r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"}},
             {"SHAPE": "dddd"}]  # Jan 2020 - Mar 2023
        ]

        # Degree + school patterns
        education_patterns = [
            [{"LOWER": {"IN": ["bachelor", "master", "phd", "doctorate"]}},
             {"LOWER": {"IN": ["of", "in"]}},
             {"ENT_TYPE": "FIELD"},
             {"LOWER": {"IN": ["from", "at"]}},
             {"ENT_TYPE": {"IN": ["ORG", "EDUCATION"]}}]
        ]

        self.matcher.add("JOB_COMPANY", job_company_patterns)
        self.matcher.add("DATE_RANGE", date_range_patterns)
        self.matcher.add("EDUCATION", education_patterns)

    def extract_relationships(self, text: str, entities: List[Dict]) -> Dict:
        """
        Extract relationships between entities and build structured data
        """
        doc = self.nlp(text)

        # Find pattern matches
        matches = self.matcher(doc)

        # Extract structured data
        work_experience = self._extract_work_experience(text, entities, doc)
        education = self._extract_education(text, entities, doc)
        skills = self._extract_and_categorize_skills(text, entities)

        # Extract achievements and responsibilities
        achievements = self._extract_achievements(text, doc)

        # Calculate experience metrics
        experience_metrics = self._calculate_experience_metrics(work_experience)

        return {
            "work_experience": [self._work_exp_to_dict(exp) for exp in work_experience],
            "education": [self._education_to_dict(edu) for edu in education],
            "skills": skills,
            "achievements": achievements,
            "experience_metrics": experience_metrics,
            "career_progression": self._analyze_career_progression(work_experience),
            "skill_evolution": self._analyze_skill_evolution(work_experience)
        }

    def _extract_work_experience(self, text: str, entities: List[Dict], doc) -> List[WorkExperience]:
        """Extract structured work experience"""
        work_experiences = []

        # Find job titles and companies
        titles = [e for e in entities if e["label"] in ["TITLE", "JOB"]]
        companies = [e for e in entities if e["label"] in ["COMPANY", "ORG"]]
        dates = [e for e in entities if e["label"] in ["DATE", "DURATION"]]

        # Group by proximity (entities close to each other likely belong together)
        for title in titles:
            # Find closest company
            closest_company = self._find_closest_entity(title, companies, max_distance=200)

            # Find associated dates
            associated_dates = self._find_nearby_entities(title, dates, max_distance=300)

            # Extract skills mentioned near this job
            job_skills = self._extract_contextual_skills(text, title["start"], title["end"])

            if closest_company:
                work_exp = WorkExperience(
                    title=title["text"],
                    company=closest_company["text"],
                    skills=job_skills,
                    start_date=associated_dates[0]["text"] if len(associated_dates) > 0 else None,
                    end_date=associated_dates[1]["text"] if len(associated_dates) > 1 else None
                )
                work_experiences.append(work_exp)

        return work_experiences

    def _extract_education(self, text: str, entities: List[Dict], doc) -> List[EducationRecord]:
        """Extract structured education records"""
        education_records = []

        degrees = [e for e in entities if e["label"] in ["EDUCATION", "DEGREE"]]
        schools = [e for e in entities if e["label"] in ["ORG", "EDUCATION"]
                   and any(keyword in e["text"].lower()
                           for keyword in ["university", "college", "institute", "school"])]

        for degree in degrees:
            closest_school = self._find_closest_entity(degree, schools, max_distance=300)

            # Extract year
            year_match = re.search(r'\b(19|20)\d{2}\b', text[max(0, degree["start"] - 100):degree["end"] + 100])
            year = year_match.group() if year_match else None

            # Extract GPA
            gpa_match = re.search(r'\bgpa\s*:?\s*(\d+\.?\d*)\b',
                                  text[max(0, degree["start"] - 50):degree["end"] + 50], re.IGNORECASE)
            gpa = gpa_match.group(1) if gpa_match else None

            education_record = EducationRecord(
                degree=degree["text"],
                school=closest_school["text"] if closest_school else None,
                year=year,
                gpa=gpa
            )
            education_records.append(education_record)

        return education_records

    def _extract_and_categorize_skills(self, text: str, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """Extract and intelligently categorize skills"""
        skill_entities = [e for e in entities if e["label"] in ["SKILL", "TECHNOLOGY", "TOOL"]]

        categorized_skills = {}
        uncategorized_skills = []

        for skill_entity in skill_entities:
            skill_name = skill_entity["text"].lower().strip()
            category_found = False

            # Try to categorize the skill
            for category, category_skills in self.skill_categories.items():
                if any(cat_skill in skill_name or skill_name in cat_skill
                       for cat_skill in category_skills):
                    if category not in categorized_skills:
                        categorized_skills[category] = []

                    # Try to extract proficiency level
                    proficiency = self._extract_skill_proficiency(text, skill_entity)

                    categorized_skills[category].append({
                        "name": skill_entity["text"],
                        "proficiency": proficiency,
                        "confidence": skill_entity.get("confidence", 0.8)
                    })
                    category_found = True
                    break

            if not category_found:
                uncategorized_skills.append({
                    "name": skill_entity["text"],
                    "proficiency": None,
                    "confidence": skill_entity.get("confidence", 0.8)
                })

        if uncategorized_skills:
            categorized_skills["Other"] = uncategorized_skills

        return categorized_skills

    def _extract_skill_proficiency(self, text: str, skill_entity: Dict) -> Optional[str]:
        """Try to extract proficiency level for a skill"""
        # Look for proficiency indicators near the skill
        context = text[max(0, skill_entity["start"] - 50):skill_entity["end"] + 50].lower()

        proficiency_patterns = {
            "Expert": ["expert", "advanced", "senior level", "10+ years", "5+ years"],
            "Proficient": ["proficient", "experienced", "strong", "solid", "3+ years"],
            "Intermediate": ["intermediate", "familiar", "working knowledge", "1+ years"],
            "Beginner": ["beginner", "basic", "learning", "exposure", "familiar with"]
        }

        for level, indicators in proficiency_patterns.items():
            if any(indicator in context for indicator in indicators):
                return level

        return None

    def _extract_achievements(self, text: str, doc) -> List[str]:
        """Extract achievements and accomplishments using NLP patterns"""
        achievements = []

        # Achievement indicator patterns
        achievement_patterns = [
            r'(?:achieved|accomplished|delivered|increased|decreased|improved|reduced|built|created|developed|led|managed)\s+[^.!?]*(?:\d+%|\$\d+|by \d+)',
            r'(?:winner|recipient|awarded|recognized)\s+[^.!?]*',
            r'(?:successfully|effectively)\s+(?:led|managed|delivered|implemented)\s+[^.!?]*'
        ]

        for pattern in achievement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                achievement = match.group().strip()
                if len(achievement) > 20 and achievement not in achievements:
                    achievements.append(achievement)

        return achievements[:10]  # Limit to top 10

    def _calculate_experience_metrics(self, work_experiences: List[WorkExperience]) -> Dict:
        """Calculate experience-related metrics"""
        if not work_experiences:
            return {"total_years": 0, "companies": 0, "roles": 0, "average_tenure": 0}

        total_years = 0
        companies = set()
        roles = set()

        for exp in work_experiences:
            if exp.company:
                companies.add(exp.company.lower())
            if exp.title:
                roles.add(exp.title.lower())

            # Try to calculate duration
            if exp.start_date and exp.end_date:
                # Simple year extraction for now
                start_year = self._extract_year(exp.start_date)
                end_year = self._extract_year(exp.end_date)

                if start_year and end_year:
                    total_years += max(0, end_year - start_year)

        # Safe average tenure calculation
        average_tenure = 0
        if work_experiences:
            try:
                average_tenure = round(total_years / len(work_experiences), 1)
            except (ZeroDivisionError, TypeError):
                average_tenure = 0

        return {
            "total_years": total_years,
            "companies": len(companies),
            "roles": len(roles),
            "average_tenure": average_tenure
        }

    def _analyze_career_progression(self, work_experiences: List[WorkExperience]) -> Dict:
        """Analyze career progression patterns"""
        if len(work_experiences) < 2:
            return {"progression_score": 0, "trend": "insufficient_data"}

        # Seniority indicators in job titles
        seniority_levels = {
            "intern": 1, "junior": 2, "associate": 3, "mid": 4, "senior": 5,
            "staff": 6, "principal": 7, "lead": 8, "manager": 9, "director": 10, "vp": 11
        }

        progression_scores = []
        for exp in work_experiences:
            title_lower = exp.title.lower()
            score = 4  # Default mid-level

            for level, level_score in seniority_levels.items():
                if level in title_lower:
                    score = level_score
                    break

            progression_scores.append(score)

        # Calculate progression trend
        if len(progression_scores) >= 2:
            trend_slope = (progression_scores[-1] - progression_scores[0]) / (len(progression_scores) - 1)

            if trend_slope > 0.5:
                trend = "upward"
            elif trend_slope < -0.5:
                trend = "downward"
            else:
                trend = "lateral"
        else:
            trend = "stable"

        return {
            "progression_score": max(progression_scores) if progression_scores else 0,
            "trend": trend,
            "seniority_growth": progression_scores[-1] - progression_scores[0] if len(progression_scores) >= 2 else 0
        }

    def _analyze_skill_evolution(self, work_experiences: List[WorkExperience]) -> Dict:
        """Analyze how skills evolved across jobs"""
        skill_timeline = {}
        all_skills = set()

        for i, exp in enumerate(work_experiences):
            for skill in exp.skills:
                skill_lower = skill.lower()
                all_skills.add(skill_lower)

                if skill_lower not in skill_timeline:
                    skill_timeline[skill_lower] = []

                skill_timeline[skill_lower].append({
                    "job_index": i,
                    "company": exp.company,
                    "title": exp.title
                })

        # Find skills that appear across multiple jobs (core skills)
        core_skills = []
        emerging_skills = []

        for skill, appearances in skill_timeline.items():
            if len(appearances) >= 2:
                core_skills.append({
                    "skill": skill,
                    "frequency": len(appearances),
                    "span": max(app["job_index"] for app in appearances) - min(
                        app["job_index"] for app in appearances) + 1
                })
            elif appearances[-1]["job_index"] == len(work_experiences) - 1:  # Appears in most recent job
                emerging_skills.append(skill)

        return {
            "total_unique_skills": len(all_skills),
            "core_skills": sorted(core_skills, key=lambda x: x["frequency"], reverse=True)[:5],
            "emerging_skills": emerging_skills[:5],
            "skill_diversity_score": len(all_skills) / len(work_experiences) if work_experiences else 0
        }

    def _find_closest_entity(self, target_entity: Dict, candidate_entities: List[Dict], max_distance: int = 100) -> \
    Optional[Dict]:
        """Find the closest entity to a target entity"""
        if not candidate_entities:
            return None

        target_pos = (target_entity["start"] + target_entity["end"]) / 2

        closest_entity = None
        min_distance = float('inf')

        for candidate in candidate_entities:
            candidate_pos = (candidate["start"] + candidate["end"]) / 2
            distance = abs(target_pos - candidate_pos)

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                closest_entity = candidate

        return closest_entity

    def _find_nearby_entities(self, target_entity: Dict, candidate_entities: List[Dict], max_distance: int = 200) -> \
    List[Dict]:
        """Find entities near a target entity"""
        target_pos = (target_entity["start"] + target_entity["end"]) / 2
        nearby_entities = []

        for candidate in candidate_entities:
            candidate_pos = (candidate["start"] + candidate["end"]) / 2
            distance = abs(target_pos - candidate_pos)

            if distance <= max_distance:
                nearby_entities.append(candidate)

        return sorted(nearby_entities, key=lambda x: abs((x["start"] + x["end"]) / 2 - target_pos))

    def _extract_contextual_skills(self, text: str, start_pos: int, end_pos: int, context_window: int = 300) -> List[
        str]:
        """Extract skills mentioned near a specific position in text"""
        context_start = max(0, start_pos - context_window)
        context_end = min(len(text), end_pos + context_window)
        context = text[context_start:context_end].lower()

        found_skills = []

        # Check against known skill categories
        for category_skills in self.skill_categories.values():
            for skill in category_skills:
                if skill in context and skill not in found_skills:
                    found_skills.append(skill.title())

        return found_skills

    def _extract_year(self, date_string: str) -> Optional[int]:
        """Extract year from a date string"""
        if not date_string:
            return None

        year_match = re.search(r'\b(19|20)\d{2}\b', date_string)
        return int(year_match.group()) if year_match else None

    def _work_exp_to_dict(self, work_exp: WorkExperience) -> Dict:
        """Convert WorkExperience to dictionary"""
        return {
            "title": work_exp.title,
            "company": work_exp.company,
            "start_date": work_exp.start_date,
            "end_date": work_exp.end_date,
            "duration": work_exp.duration,
            "skills": work_exp.skills,
            "achievements": work_exp.achievements,
            "location": work_exp.location
        }

    def _education_to_dict(self, education: EducationRecord) -> Dict:
        """Convert EducationRecord to dictionary"""
        return {
            "degree": education.degree,
            "field": education.field,
            "school": education.school,
            "year": education.year,
            "gpa": education.gpa,
            "location": education.location
        }


def _infer_context_for_ats(text: str, structured_data: Dict) -> Dict:
    """Build minimal context_results from text and structured_data when not provided."""
    text_lower = text.lower()
    entities = []
    personal = structured_data.get("personal_info") or {}
    if isinstance(personal, dict):
        if personal.get("email") and "@" in str(personal.get("email", "")):
            entities.append({"label": "EMAIL", "text": str(personal["email"])})
        if personal.get("phone"):
            entities.append({"label": "PHONE", "text": str(personal["phone"])})
        if personal.get("name"):
            entities.append({"label": "NAME", "text": str(personal["name"])})
    if not entities and re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text):
        entities.append({"label": "EMAIL", "text": "found"})
    section_analysis = {
        "has_experience": "experience" in text_lower or "employment" in text_lower,
        "has_education": "education" in text_lower or "academic" in text_lower,
        "has_skills": "skills" in text_lower or "competencies" in text_lower,
        "structure_score": 0,
    }
    return {"entities": entities, "section_analysis": section_analysis}


def _extract_year_from_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    m = re.search(r"\b(19|20)\d{2}\b", str(date_str))
    return int(m.group()) if m else None


def _run_ats_engine(
    text: str,
    context_results: Dict,
    structured_data: Dict,
    jd_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Core ATS scoring: returns score (0-100), breakdown dict, and issues list.
    When jd_keywords is provided, adds keyword_coverage to breakdown and JD-related issues.
    """
    breakdown = {}
    issues: List[str] = []
    text_lower = text.lower()
    entities = context_results.get("entities") or []
    section_analysis = context_results.get("section_analysis") or {}

    if jd_keywords:
        weights = {
            "sections": 20,
            "contact": 20,
            "dates": 10,
            "formatting": 10,
            "work_experience": 15,
            "education": 5,
            "skills": 5,
            "section_order": 5,
            "keyword_coverage": 10,
        }
    else:
        weights = {
            "sections": 25,
            "contact": 20,
            "dates": 15,
            "formatting": 15,
            "work_experience": 15,
            "education": 5,
            "skills": 5,
        }

    has_email = any(e.get("label") == "EMAIL" and "@" in str(e.get("text", "")) for e in entities)
    has_phone = any(e.get("label") == "PHONE" for e in entities)
    has_name = any(e.get("label") in ("NAME", "PERSON") for e in entities)
    contact_pts = (40 if has_email else 0) + (30 if has_phone else 0) + (30 if has_name else 0)
    breakdown["contact"] = min(100, contact_pts)
    if not has_email:
        issues.append("Email missing")
    if not has_phone:
        issues.append("Phone number missing")
    if not has_name:
        issues.append("Name or contact block unclear")

    standard_sections = ["experience", "education", "skills", "summary"]
    found_sections = sum(1 for s in standard_sections if s in text_lower)
    breakdown["sections"] = min(100, int((found_sections / 4) * 100))
    if "summary" not in text_lower and "objective" not in text_lower:
        issues.append("Summary section missing")

    header_lines = [ln.strip() for ln in text.split("\n") if 5 <= len(ln.strip()) <= 60]
    for line in header_lines:
        line_lower = line.lower()
        if any(re.search(p, line_lower) for p in STANDARD_SECTION_HEADERS):
            continue
        if line_lower.replace(" ", "").isalpha() or (len(line) < 40 and line[0].isupper()):
            if any(h in line_lower for h in NON_STANDARD_HEADER_HINTS):
                issues.append(f"Non-standard section header: \"{line[:50]}\"")
                break

    has_years = bool(DATE_YEAR.search(text))
    month_year = bool(DATE_MONTH_YEAR.search(text_lower))
    date_formats_consistent = has_years and (month_year or re.search(r"\b\d{1,2}/\d{4}\b|\b\d{4}\b", text))
    breakdown["dates"] = 100 if (has_years and month_year) else (80 if has_years else 0)
    if has_years and not date_formats_consistent:
        issues.append("Date format inconsistent; use Month YYYY or YYYY consistently")

    special_count = len(re.findall(r"[^\w\s\-.,()@\n]", text))
    excess_special = special_count > len(text) * 0.02
    excess_newlines = len(re.findall(r"\n\s*\n\s*\n", text)) > 3
    formatting_penalty = (15 if excess_special else 0) + (15 if excess_newlines else 0)
    breakdown["formatting"] = max(0, 100 - formatting_penalty)
    if excess_special:
        issues.append("Excessive special characters may hurt ATS parsing")
    if excess_newlines:
        issues.append("Inconsistent formatting or too many blank lines")

    work_exp = structured_data.get("work_experience") or []
    if not work_exp:
        breakdown["work_experience"] = 0
    else:
        with_structure = sum(
            1 for exp in work_exp
            if (exp.get("title") or exp.get("company")) and (exp.get("start_date") or exp.get("end_date"))
        )
        breakdown["work_experience"] = min(100, int((with_structure / len(work_exp)) * 100))

    education = structured_data.get("education") or []
    if not education:
        breakdown["education"] = 0
    else:
        with_school = sum(1 for edu in education if edu.get("degree") and edu.get("school"))
        breakdown["education"] = min(100, int((with_school / len(education)) * 100))

    skills_dict = structured_data.get("skills") or {}
    total_skills = sum(len(slist) for slist in skills_dict.values() if isinstance(slist, list))
    breakdown["skills"] = min(100, total_skills * 5) if total_skills else 0

    exp_pos = text_lower.find("experience") if "experience" in text_lower else len(text) + 1
    edu_pos = text_lower.find("education") if "education" in text_lower else len(text) + 1
    work_before_edu = exp_pos <= edu_pos or not work_exp
    if "section_order" in weights:
        breakdown["section_order"] = 100 if work_before_edu else 50
    if work_exp and not work_before_edu:
        issues.append("Work experience should appear before education for experienced candidates")

    job_start_years = []
    for exp in work_exp:
        y = _extract_year_from_date(exp.get("start_date") or exp.get("end_date"))
        if y is not None:
            job_start_years.append(y)
    reverse_chron = True
    if len(job_start_years) >= 2:
        reverse_chron = job_start_years == sorted(job_start_years, reverse=True)
    if not reverse_chron and len(job_start_years) >= 2:
        issues.append("Dates should be reverse chronological (most recent first)")

    if jd_keywords:
        keywords_lower = [k.lower().strip() for k in jd_keywords if k and isinstance(k, str)]
        if keywords_lower:
            idxs = [text_lower.find(w) for w in ("experience", "education", "skills")]
            summary_end = min(400, *(i if i >= 0 else len(text_lower) for i in idxs), len(text_lower))
            summary_zone = text_lower[:summary_end]
            titles_zone = " ".join([str(e.get("title") or "") for e in work_exp]).lower()
            skills_text = " ".join(
                str(s.get("name", s) if isinstance(s, dict) else s).lower()
                for slist in skills_dict.values() for s in (slist if isinstance(slist, list) else [])
            )
            body_zone = text_lower
            def count_in_zone(zone: str) -> int:
                return sum(1 for kw in keywords_lower if kw in zone)
            summary_hits = count_in_zone(summary_zone)
            title_hits = count_in_zone(titles_zone)
            body_hits = count_in_zone(body_zone)
            skill_hits = count_in_zone(skills_text)
            total_hits = summary_hits * 4 + title_hits * 3 + body_hits * 2 + skill_hits
            max_possible = len(keywords_lower) * (4 + 3 + 2 + 1)
            breakdown["keyword_coverage"] = min(100, int((total_hits / max_possible * 100))) if max_possible else 0
            if skill_hits == 0 and keywords_lower:
                issues.append("Skills section contains no JD keywords")
    else:
        breakdown["keyword_coverage"] = 0

    total = sum(
        (breakdown.get(key) or 0) / 100.0 * w
        for key, w in weights.items()
        if w and key in breakdown
    )
    score = max(0, min(100, int(round(total))))
    return {"score": score, "breakdown": breakdown, "issues": issues}


def calculate_ats_score(
    resume_text: str,
    structured_data: Dict,
    context_results: Optional[Dict] = None,
    jd_keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Public ATS scorer for resume text and structured data. Use from enhance endpoint
    for before/after scoring (ats_score_original, ats_score_enhanced).
    Returns dict with score (0-100), breakdown, and issues.
    """
    if context_results is None:
        context_results = _infer_context_for_ats(resume_text, structured_data)
    return _run_ats_engine(resume_text, context_results, structured_data, jd_keywords=jd_keywords)


class ResumeIntelligenceAnalyzer:
    """
    Main class that combines section detection and relationship extraction
    for comprehensive resume intelligence
    """

    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.context_extractor = None  # Will be set from section detector
        self.relationship_extractor = IntelligentRelationshipExtractor(nlp_model)

    def analyze_resume(self, text: str) -> Dict:
        """
        Perform comprehensive resume analysis combining all intelligence layers
        """
        # Import here to avoid circular imports
        from intelligent_section_detector import ContextAwareEntityExtractor

        if not self.context_extractor:
            self.context_extractor = ContextAwareEntityExtractor(self.nlp)

        # Layer 1: Context-aware entity extraction
        context_results = self.context_extractor.extract_with_context(text)
        entities = context_results["entities"]

        # Layer 2: Relationship extraction
        relationship_results = self.relationship_extractor.extract_relationships(text, entities)

        # Layer 3: Advanced analytics
        analytics = self._perform_advanced_analytics(context_results, relationship_results, text)

        return {
            "entities": entities,
            "sections": context_results["sections"],
            "section_analysis": context_results["section_analysis"],
            "work_experience": relationship_results["work_experience"],
            "education": relationship_results["education"],
            "skills": relationship_results["skills"],
            "achievements": relationship_results["achievements"],
            "experience_metrics": relationship_results["experience_metrics"],
            "career_progression": relationship_results["career_progression"],
            "skill_evolution": relationship_results["skill_evolution"],
            "resume_analytics": analytics
        }

    def _perform_advanced_analytics(self, context_results: Dict, relationship_results: Dict, text: str) -> Dict:
        """Perform advanced resume analytics"""

        # Resume completeness score
        completeness_score = self._calculate_completeness_score(context_results, relationship_results)

        ats_result = self._calculate_ats_compatibility(text, context_results, relationship_results)
        ats_score = ats_result["score"]
        ats_breakdown = ats_result["breakdown"]
        ats_issues = ats_result.get("issues") or []

        skills_analysis = self._analyze_skills_depth(relationship_results["skills"])
        red_flags = self._detect_red_flags(relationship_results, text)
        strengths = self._identify_strengths(relationship_results, context_results)

        return {
            "completeness_score": completeness_score,
            "ats_compatibility_score": ats_score,
            "ats_breakdown": ats_breakdown,
            "ats_issues": ats_issues,
            "skills_analysis": skills_analysis,
            "red_flags": red_flags,
            "strengths": strengths,
            "overall_quality_score": self._calculate_overall_quality(completeness_score, ats_score, len(red_flags))
        }

    def _calculate_completeness_score(self, context_results: Dict, relationship_results: Dict) -> int:
        """Calculate how complete the resume is (0-100)"""
        score = 0

        # Essential sections (40 points)
        if context_results["section_analysis"]["has_experience"]:
            score += 15
        if context_results["section_analysis"]["has_education"]:
            score += 15
        if context_results["section_analysis"]["has_skills"]:
            score += 10

        # Contact information (20 points)
        has_email = any(e["label"] == "EMAIL" for e in context_results["entities"])
        has_phone = any(e["label"] == "PHONE" for e in context_results["entities"])
        has_name = any(e["label"] in ["NAME", "PERSON"] for e in context_results["entities"])

        score += 8 if has_email else 0
        score += 6 if has_phone else 0
        score += 6 if has_name else 0

        # Work experience details (25 points)
        work_exp = relationship_results["work_experience"]
        if work_exp:
            score += 10 if any(exp["company"] for exp in work_exp) else 0
            score += 10 if any(exp["start_date"] or exp["end_date"] for exp in work_exp) else 0
            score += 5 if any(exp["skills"] for exp in work_exp) else 0

        # Skills categorization (10 points)
        skills = relationship_results["skills"]
        if skills and len(skills) > 1:  # Multiple skill categories
            score += 10
        elif skills:
            score += 5

        # Achievements (5 points)
        if relationship_results["achievements"]:
            score += 5

        return min(100, score)

    def _calculate_ats_compatibility(self, text: str, context_results: Dict, relationship_results: Dict) -> Dict:
        """
        Calculate ATS compatibility via full engine; returns score, breakdown, and issues.
        Existing callers still get numeric score from result["score"].
        """
        return _run_ats_engine(
            text, context_results, relationship_results, jd_keywords=None
        )

    def _analyze_skills_depth(self, skills_dict: Dict) -> Dict:
        """Analyze the depth and breadth of skills"""
        total_skills = sum(len(skill_list) for skill_list in skills_dict.values())
        categories = len(skills_dict)

        # Find skills with proficiency levels
        skills_with_proficiency = 0
        for skill_list in skills_dict.values():
            for skill in skill_list:
                if skill.get("proficiency"):
                    skills_with_proficiency += 1

        return {
            "total_skills": total_skills,
            "skill_categories": categories,
            "skills_with_proficiency": skills_with_proficiency,
            "breadth_score": min(100, categories * 20),  # Max 5 categories
            "depth_score": min(100, (skills_with_proficiency / max(1, total_skills)) * 100)
        }

    def _detect_red_flags(self, relationship_results: Dict, text: str) -> List[str]:
        """Detect potential red flags in the resume"""
        red_flags = []

        # Employment gaps (simplified check)
        work_exp = relationship_results["work_experience"]
        if len(work_exp) > 1:
            years = []
            for exp in work_exp:
                if exp["start_date"]:
                    year = self.relationship_extractor._extract_year(exp["start_date"])
                    if year:
                        years.append(year)

            if len(years) > 1:
                years.sort()
                for i in range(len(years) - 1):
                    if years[i + 1] - years[i] > 2:  # Gap > 2 years
                        red_flags.append("Potential employment gap detected")
                        break

        # Very short tenure pattern
        experience_metrics = relationship_results["experience_metrics"]
        if experience_metrics["average_tenure"] < 1 and experience_metrics["companies"] > 2:
            red_flags.append("Pattern of short job tenure")

        # Missing contact information
        if not any("@" in text for line in text.split("\n")[:5]):  # No email in first 5 lines
            red_flags.append("Contact information may be unclear")

        # Inconsistent formatting
        if len(re.findall(r'\n\s*\n\s*\n', text)) > 3:  # Too many blank lines
            red_flags.append("Inconsistent formatting detected")

        return red_flags

    def _identify_strengths(self, relationship_results: Dict, context_results: Dict) -> List[str]:
        """Identify resume strengths"""
        strengths = []

        # Career progression
        career_prog = relationship_results["career_progression"]
        if career_prog["trend"] == "upward":
            strengths.append("Clear career progression")

        # Skill diversity
        skill_evolution = relationship_results["skill_evolution"]
        if skill_evolution["skill_diversity_score"] > 3:
            strengths.append("Diverse technical skill set")

        # Experience breadth
        exp_metrics = relationship_results["experience_metrics"]
        if exp_metrics["companies"] >= 3:
            strengths.append("Broad industry experience")

        # Quantified achievements
        achievements = relationship_results["achievements"]
        if any(re.search(r'\d+[%$]|\d+\s*(?:years?|months?)', ach) for ach in achievements):
            strengths.append("Quantified achievements")

        # Strong section organization
        if context_results["section_analysis"]["structure_score"] >= 80:
            strengths.append("Well-organized resume structure")

        return strengths

    def _calculate_overall_quality(self, completeness: int, ats_score: int, red_flag_count: int) -> int:
        """Calculate overall resume quality score"""
        base_score = (completeness * 0.5) + (ats_score * 0.3)

        # Penalty for red flags
        red_flag_penalty = min(30, red_flag_count * 10)

        # Bonus for high scores
        bonus = 0
        if completeness >= 90 and ats_score >= 90:
            bonus = 20

        return max(0, min(100, int(base_score + bonus - red_flag_penalty)))


# Usage example
def test_intelligent_resume_analysis():
    """Test the complete intelligent resume analysis"""
    import spacy

    try:
        nlp = spacy.load("output_hybrid")
    except:
        nlp = nlp = spacy.load("en_core_web_lg")

    analyzer = ResumeIntelligenceAnalyzer(nlp)

    test_resume = """
    John Smith
    Senior Software Engineer
    john.smith@email.com | (555) 123-4567 | San Francisco, CA

    PROFESSIONAL SUMMARY
    Experienced software engineer with 8 years in full-stack development and team leadership.

    WORK EXPERIENCE

    Senior Software Engineer | Google | 2021-2023
    • Led development of microservices architecture serving 10M+ users
    • Mentored team of 5 junior engineers, improving code quality by 40%
    • Implemented CI/CD pipeline reducing deployment time by 60%
    • Technologies: Python, Docker, Kubernetes, React, PostgreSQL

    Software Engineer | Microsoft | 2019-2021  
    • Built scalable APIs handling 1M+ requests per day
    • Collaborated with product team to deliver 3 major features
    • Improved application performance by 30% through optimization
    • Technologies: Node.js, Express, MongoDB, React, Azure

    Junior Developer | Startup Inc | 2017-2019
    • Developed full-stack web applications using modern frameworks
    • Participated in agile development process and code reviews
    • Technologies: JavaScript, Vue.js, MySQL, AWS

    EDUCATION
    Bachelor of Science in Computer Science | Stanford University | 2017
    GPA: 3.8/4.0

    SKILLS
    Programming Languages: Python, JavaScript, TypeScript, Java
    Web Technologies: React, Vue.js, Node.js, Express, Django
    Cloud & DevOps: AWS, Azure, Docker, Kubernetes, Jenkins
    Databases: PostgreSQL, MongoDB, MySQL, Redis
    """

    results = analyzer.analyze_resume(test_resume)

    print(" INTELLIGENT RESUME ANALYSIS")
    print("=" * 50)

    print(f"\n OVERALL SCORES:")
    analytics = results["resume_analytics"]
    print(f"   Overall Quality: {analytics['overall_quality_score']}/100")
    print(f"   Completeness: {analytics['completeness_score']}/100")
    print(f"   ATS Compatibility: {analytics['ats_compatibility_score']}/100")

    print(f"\ WORK EXPERIENCE ({len(results['work_experience'])} jobs):")
    for exp in results["work_experience"]:
        print(f"   • {exp['title']} at {exp['company']} ({exp['start_date']}-{exp['end_date']})")
        if exp["skills"]:
            print(f"     Skills: {', '.join(exp['skills'][:3])}{'...' if len(exp['skills']) > 3 else ''}")

    print(f"\ EDUCATION:")
    for edu in results["education"]:
        print(f"   • {edu['degree']} from {edu['school']} ({edu['year']})")
        if edu["gpa"]:
            print(f"     GPA: {edu['gpa']}")

    print(f"\n SKILLS BY CATEGORY:")
    for category, skills in results["skills"].items():
        print(f"   {category}: {len(skills)} skills")
        for skill in skills[:3]:  # Show first 3
            proficiency = f" ({skill['proficiency']})" if skill.get('proficiency') else ""
            print(f"     • {skill['name']}{proficiency}")

    print(f"\n CAREER INSIGHTS:")
    exp_metrics = results["experience_metrics"]
    career_prog = results["career_progression"]
    print(f"   • Total Experience: {exp_metrics['total_years']} years")
    print(f"   • Companies: {exp_metrics['companies']}")
    print(f"   • Career Trend: {career_prog['trend']}")
    print(f"   • Progression Score: {career_prog['progression_score']}/10")

    print(f"\n STRENGTHS:")
    for strength in analytics["strengths"]:
        print(f"   • {strength}")

    if analytics["red_flags"]:
        print(f"\n AREAS FOR IMPROVEMENT:")
        for flag in analytics["red_flags"]:
            print(f"   • {flag}")

    print(f"\n ACHIEVEMENTS:")
    for achievement in results["achievements"][:3]:
        print(f"   • {achievement}")


if __name__ == "__main__":
    test_intelligent_resume_analysis()