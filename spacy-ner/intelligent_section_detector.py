import spacy
import re
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ResumeSection(Enum):
    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    CONTACT = "contact"
    OTHER = "other"


class IntelligentSectionDetector:
    """
    Detects resume sections using pattern matching and context clues
    This provides structure context to improve entity extraction
    """

    def __init__(self):
        # Section header patterns (order matters - most specific first)
        self.section_patterns = {
            ResumeSection.EXPERIENCE: [
                r'\b(?:work\s+)?experience\b',
                r'\bemployment\s+history\b',
                r'\bprofessional\s+experience\b',
                r'\bcareer\s+history\b',
                r'\bwork\s+history\b',
                r'\bjob\s+history\b'
            ],
            ResumeSection.EDUCATION: [
                r'\beducation(?:al\s+background)?\b',
                r'\bacademic\s+(?:background|history|qualifications)\b',
                r'\bschooling\b',
                r'\buniversity\b',
                r'\bcollege\b',
                r'\bdegree(?:s)?\b'
            ],
            ResumeSection.SKILLS: [
                r'\b(?:technical\s+)?skills\b',
                r'\bcompetencies\b',
                r'\bexpertise\b',
                r'\bproficiencies\b',
                r'\btechnologies\b',
                r'\btools\s+(?:and\s+technologies|&\s+technologies)\b'
            ],
            ResumeSection.PROJECTS: [
                r'\bprojects?\b',
                r'\bportfolio\b',
                r'\bside\s+projects\b',
                r'\bpersonal\s+projects\b',
                r'\bnotable\s+projects\b'
            ],
            ResumeSection.CERTIFICATIONS: [
                r'\bcertifications?\b',
                r'\blicenses?\b',
                r'\bcredentials\b',
                r'\bprofessional\s+certifications\b'
            ],
            ResumeSection.SUMMARY: [
                r'\bsummary\b',
                r'\bprofile\b',
                r'\bobject(?:ive)?\b',
                r'\babout\s+me\b',
                r'\bprofessional\s+summary\b',
                r'\bcareer\s+(?:summary|objective)\b'
            ],
            ResumeSection.CONTACT: [
                r'\bcontact\s+(?:information|details)\b',
                r'\bpersonal\s+(?:information|details)\b',
                r'\bget\s+in\s+touch\b'
            ]
        }

        # Contextual indicators that suggest section boundaries
        self.section_indicators = {
            ResumeSection.EXPERIENCE: [
                r'\b\d{4}\s*[-–—]\s*(?:\d{4}|present|current)\b',  # Date ranges
                r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b',  # Dates
                r'\b(?:manager|engineer|analyst|director|coordinator|specialist)\b',  # Job titles
                r'\b(?:developed|managed|led|created|implemented|designed)\b'  # Action verbs
            ],
            ResumeSection.EDUCATION: [
                r'\b(?:bachelor|master|phd|doctorate|associates?|b\.?[sa]\.?|m\.?[sa]\.?)\b',
                r'\b(?:university|college|institute|school)\b',
                r'\bgpa\s*:?\s*\d+\.?\d*\b',
                r'\b(?:graduated|degree|major|minor)\b'
            ],
            ResumeSection.SKILLS: [
                r'\b(?:python|java|javascript|react|node|sql|aws|docker|kubernetes)\b',
                r'\b(?:programming|software|technical|analytical)\b',
                r'\b(?:languages?|frameworks?|libraries|tools)\b'
            ]
        }

    def detect_sections(self, text: str) -> Dict[ResumeSection, List[Tuple[int, int, str]]]:
        """
        Detect resume sections and return their positions and content
        Returns: {section_type: [(start_pos, end_pos, content), ...]}
        """
        sections = {section: [] for section in ResumeSection}

        # Split text into lines for analysis
        lines = text.split('\n')
        current_position = 0

        # Track current section context
        current_section = ResumeSection.OTHER
        section_start = 0

        for i, line in enumerate(lines):
            line_start = current_position
            line_end = current_position + len(line)

            # Check if this line indicates a new section
            detected_section = self._detect_section_header(line)

            if detected_section and detected_section != current_section:
                # Save previous section if it has content
                if current_section != ResumeSection.OTHER and section_start < line_start:
                    section_content = text[section_start:line_start].strip()
                    if section_content:
                        sections[current_section].append((section_start, line_start, section_content))

                # Start new section
                current_section = detected_section
                section_start = line_start

            # Also detect sections by content patterns
            elif current_section == ResumeSection.OTHER:
                content_section = self._detect_section_by_content(line)
                if content_section:
                    current_section = content_section
                    section_start = line_start

            current_position = line_end + 1  # +1 for newline

        # Don't forget the last section
        if current_section != ResumeSection.OTHER and section_start < len(text):
            section_content = text[section_start:].strip()
            if section_content:
                sections[current_section].append((section_start, len(text), section_content))

        return sections

    def _detect_section_header(self, line: str) -> Optional[ResumeSection]:
        """Detect if a line is a section header"""
        line_lower = line.lower().strip()

        # Skip very short lines or lines with too much content
        if len(line_lower) < 3 or len(line_lower) > 50:
            return None

        # Check against section patterns
        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    return section

        return None

    def _detect_section_by_content(self, line: str) -> Optional[ResumeSection]:
        """Detect section by content patterns"""
        line_lower = line.lower().strip()

        # Check for strong contextual indicators
        for section, indicators in self.section_indicators.items():
            matches = 0
            for indicator in indicators:
                if re.search(indicator, line_lower, re.IGNORECASE):
                    matches += 1

            # If multiple indicators match, likely this section
            if matches >= 2:
                return section
            # Or if one very strong indicator matches
            elif matches == 1 and section == ResumeSection.EXPERIENCE:
                if re.search(r'\b(?:manager|engineer|analyst|director)\b', line_lower):
                    return section

        return None

    def get_section_context(self, sections: Dict[ResumeSection, List], position: int) -> ResumeSection:
        """Get the section context for a given text position"""
        for section, section_list in sections.items():
            for start, end, _ in section_list:
                if start <= position <= end:
                    return section
        return ResumeSection.OTHER


class ContextAwareEntityExtractor:
    """
    Enhances entity extraction using section context
    """

    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.section_detector = IntelligentSectionDetector()

        # Section-specific entity preferences
        self.section_entity_preferences = {
            ResumeSection.HEADER: {
                "prefer": ["NAME", "EMAIL", "PHONE", "LOCATION"],
                "boost_confidence": 0.2
            },
            ResumeSection.EXPERIENCE: {
                "prefer": ["TITLE", "COMPANY", "DATE", "SKILL"],
                "boost_confidence": 0.15,
                "suppress": ["NAME"]  # Names in experience are usually company names
            },
            ResumeSection.EDUCATION: {
                "prefer": ["EDUCATION", "DEGREE", "DATE", "GPA"],
                "boost_confidence": 0.15
            },
            ResumeSection.SKILLS: {
                "prefer": ["SKILL", "TECHNOLOGY"],
                "boost_confidence": 0.25,
                "suppress": ["PERSON", "ORG"]  # These are usually skill names, not people/orgs
            },
            ResumeSection.CONTACT: {
                "prefer": ["EMAIL", "PHONE", "LOCATION", "NAME"],
                "boost_confidence": 0.3
            }
        }

    def extract_with_context(self, text: str) -> Dict:
        """
        Extract entities with section context awareness
        """
        # First, detect sections
        sections = self.section_detector.detect_sections(text)

        # Then extract entities with spaCy
        doc = self.nlp(text)

        # Enhance entities with context
        enhanced_entities = []

        for ent in doc.ents:
            # Determine which section this entity is in
            entity_section = self.section_detector.get_section_context(sections, ent.start_char)

            # Get base confidence
            base_confidence = self._estimate_confidence(ent)

            # Adjust confidence based on section context
            adjusted_confidence = self._adjust_confidence_by_context(
                ent, entity_section, base_confidence
            )

            # Determine if we should suppress this entity
            if self._should_suppress_entity(ent, entity_section):
                continue

            enhanced_entities.append({
                "text": ent.text.strip(),
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": adjusted_confidence,
                "section": entity_section.value,
                "section_boost": adjusted_confidence > base_confidence
            })

        return {
            "entities": enhanced_entities,
            "sections": {
                section.value: [(start, end) for start, end, _ in section_list]
                for section, section_list in sections.items()
                if section_list
            },
            "section_analysis": self._analyze_sections(sections)
        }

    def _estimate_confidence(self, ent) -> float:
        """Base confidence estimation (same as before)"""
        confidence = 0.8

        if ent.label_ == "EMAIL" and "@" in ent.text and "." in ent.text:
            confidence = 0.95
        elif ent.label_ == "PHONE" and re.match(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', ent.text):
            confidence = 0.95
        elif ent.label_ in ["NAME", "PERSON"] and 2 <= len(ent.text.split()) <= 3:
            confidence = 0.9
        elif ent.label_ in ["SKILL", "TITLE", "COMPANY"] and len(ent.text.split()) <= 4:
            confidence = 0.85

        # Apply penalties
        if len(ent.text) > 50:
            confidence *= 0.7
        if len(ent.text.split()) > 6:
            confidence *= 0.8
        if len(ent.text.strip()) < 2:
            confidence *= 0.5

        return min(max(confidence, 0.1), 1.0)

    def _adjust_confidence_by_context(self, ent, section: ResumeSection, base_confidence: float) -> float:
        """Adjust confidence based on section context"""
        if section not in self.section_entity_preferences:
            return base_confidence

        prefs = self.section_entity_preferences[section]

        # Boost confidence for preferred entity types in this section
        if ent.label_ in prefs.get("prefer", []):
            boost = prefs.get("boost_confidence", 0.1)
            return min(base_confidence + boost, 1.0)

        return base_confidence

    def _should_suppress_entity(self, ent, section: ResumeSection) -> bool:
        """Determine if entity should be suppressed based on context"""
        if section not in self.section_entity_preferences:
            return False

        prefs = self.section_entity_preferences[section]
        suppress_list = prefs.get("suppress", [])

        return ent.label_ in suppress_list

    def _analyze_sections(self, sections: Dict) -> Dict:
        """Analyze the detected sections for insights"""
        analysis = {
            "sections_found": len([s for s in sections.values() if s]),
            "has_experience": bool(sections[ResumeSection.EXPERIENCE]),
            "has_education": bool(sections[ResumeSection.EDUCATION]),
            "has_skills": bool(sections[ResumeSection.SKILLS]),
            "structure_score": 0
        }

        # Calculate structure score (0-100)
        essential_sections = [
            ResumeSection.EXPERIENCE,
            ResumeSection.EDUCATION,
            ResumeSection.SKILLS
        ]

        found_essential = sum(1 for section in essential_sections if sections[section])
        analysis["structure_score"] = int((found_essential / len(essential_sections)) * 100)

        return analysis


# Usage example for testing
def test_intelligent_extraction():
    """Test the intelligent extraction system"""
    import spacy

    # Load your hybrid model
    try:
        nlp = spacy.load("output_hybrid")
    except:
        nlp = spacy.load("en_core_web_sm")

    extractor = ContextAwareEntityExtractor(nlp)

    # Test resume text
    test_resume = """
    John Smith
    Software Engineer
    john.smith@email.com | (555) 123-4567

    PROFESSIONAL SUMMARY
    Experienced software engineer with 5 years in backend development.

    WORK EXPERIENCE
    Senior Software Engineer | Google | 2021-2023
    • Developed scalable microservices using Python and Docker
    • Led team of 5 engineers on cloud migration project

    Software Developer | Microsoft | 2019-2021  
    • Built APIs using Node.js and Express
    • Worked with React and JavaScript frontend

    EDUCATION
    Bachelor of Science in Computer Science | MIT | 2019
    GPA: 3.8/4.0

    SKILLS
    Languages: Python, JavaScript, Java
    Technologies: AWS, Docker, Kubernetes, React
    """

    results = extractor.extract_with_context(test_resume)

    print("🔍 Intelligent Extraction Results:")
    print(f"Sections found: {results['section_analysis']['sections_found']}")
    print(f"Structure score: {results['section_analysis']['structure_score']}/100")

    for entity in results["entities"]:
        boost_indicator = "📈" if entity["section_boost"] else ""
        print(f"{boost_indicator} '{entity['text']}' → {entity['label']} "
              f"({entity['section']}) [{entity['confidence']:.2f}]")


if __name__ == "__main__":
    test_intelligent_extraction()