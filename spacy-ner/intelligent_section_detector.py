import spacy
import re
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
import logging
from dataclasses import dataclass

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
    LANGUAGES = "languages"
    AWARDS = "awards"
    REFERENCES = "references"
    VOLUNTEERING = "volunteering"
    INTERESTS = "interests"
    OTHER = "other"


@dataclass
class SectionBoundary:
    section: ResumeSection
    start: int
    end: int
    content: str
    confidence: float = 1.0
    detected_by: str = "header"


class IntelligentSectionDetector:
    """
    Advanced resume section detector using pattern matching, contextual analysis,
    and structural cues to identify resume sections with high accuracy.
    """

    def __init__(self):
        # Load NLP model for advanced text analysis
        try:
            self.nlp = nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Using regex-only mode.")
            self.nlp = None

        # Comprehensive section header patterns with priority ordering
        self.section_patterns = {
            ResumeSection.EXPERIENCE: [
                r'^(?:\d+[\.\)]?\s*)?(?:work|professional|relevant)\s+experience(?:\s+&?\s+history)?$',
                r'^(?:\d+[\.\)]?\s*)?employment(?:\s+history)?$',
                r'^(?:\d+[\.\)]?\s*)?career(?:\s+(?:history|summary|highlights|progress))?$',
                r'^(?:\d+[\.\)]?\s*)?work(?:\s+history)?$',
                r'^(?:\d+[\.\)]?\s*)?professional(?:\s+background|history)?$',
                r'^(?:\d+[\.\)]?\s*)?job(?:\s+history)?$',
                r'^(?:\d+[\.\)]?\s*)?experience$',
                r'^(?:\d+[\.\)]?\s*)?positions?$',
                r'^(?:\d+[\.\)]?\s*)?employment\s+record$',
                r'^(?:\d+[\.\)]?\s*)?career\s+chronology$',
            ],
            ResumeSection.EDUCATION: [
                r'^(?:\d+[\.\)]?\s*)?education(?:\s+(?:background|history|qualifications|credentials))?$',
                r'^(?:\d+[\.\)]?\s*)?academic(?:\s+(?:background|history|qualifications|credentials))?$',
                r'^(?:\d+[\.\)]?\s*)?educational(?:\s+background|qualifications)?$',
                r'^(?:\d+[\.\)]?\s*)?schooling$',
                r'^(?:\d+[\.\)]?\s*)?(?:university|college)(?:\s+education)?$',
                r'^(?:\d+[\.\)]?\s*)?degrees?(?:\s+and\s+qualifications)?$',
                r'^(?:\d+[\.\)]?\s*)?academics$',
                r'^(?:\d+[\.\)]?\s*)?studies$',
                r'^(?:\d+[\.\)]?\s*)?qualifications$',
                r'^(?:\d+[\.\)]?\s*)?courses?$',
            ],
            ResumeSection.SKILLS: [
                r'^(?:\d+[\.\)]?\s*)?(?:technical\s+)?skills(?:\s+&?\s+(?:competencies|abilities))?$',
                r'^(?:\d+[\.\)]?\s*)?competencies$',
                r'^(?:\d+[\.\)]?\s*)?expertise$',
                r'^(?:\d+[\.\)]?\s*)?proficiencies$',
                r'^(?:\d+[\.\)]?\s*)?technologies$',
                r'^(?:\d+[\.\)]?\s*)?(?:technical\s+)?abilities$',
                r'^(?:\d+[\.\)]?\s*)?tools(?:\s+and\s+technologies)?$',
                r'^(?:\d+[\.\)]?\s*)?(?:software|programming)(?:\s+skills)?$',
                r'^(?:\d+[\.\)]?\s*)?key\s+skills$',
                r'^(?:\d+[\.\)]?\s*)?core\s+(?:competencies|skills)$',
            ],
            ResumeSection.PROJECTS: [
                r'^(?:\d+[\.\)]?\s*)?projects?(?:\s+portfolio)?$',
                r'^(?:\d+[\.\)]?\s*)?portfolio$',
                r'^(?:\d+[\.\)]?\s*)?(?:side|personal|notable|key)\s+projects$',
                r'^(?:\d+[\.\)]?\s*)?selected\s+projects$',
                r'^(?:\d+[\.\)]?\s*)?project\s+experience$',
                r'^(?:\d+[\.\)]?\s*)?project\s+portfolio$',
                r'^(?:\d+[\.\)]?\s*)?project\s+history$',
            ],
            ResumeSection.CERTIFICATIONS: [
                r'^(?:\d+[\.\)]?\s*)?certifications?(?:\s+and\s+licenses?)?$',
                r'^(?:\d+[\.\)]?\s*)?licenses?(?:\s+and\s+certifications?)?$',
                r'^(?:\d+[\.\)]?\s*)?credentials$',
                r'^(?:\d+[\.\)]?\s*)?professional(?:\s+development|certifications)?$',
                r'^(?:\d+[\.\)]?\s*)?certificates?$',
                r'^(?:\d+[\.\)]?\s*)?trainings?$',
                r'^(?:\d+[\.\)]?\s*)?professional\s+qualifications$',
                r'^(?:\d+[\.\)]?\s*)?accreditations?$',
            ],
            ResumeSection.SUMMARY: [
                r'^(?:\d+[\.\)]?\s*)?summary$',
                r'^(?:\d+[\.\)]?\s*)?profile$',
                r'^(?:\d+[\.\)]?\s*)?objective$',
                r'^(?:\d+[\.\)]?\s*)?about\s+me$',
                r'^(?:\d+[\.\)]?\s*)?professional(?:\s+summary|profile)?$',
                r'^(?:\d+[\.\)]?\s*)?career(?:\s+summary|objective|profile)?$',
                r'^(?:\d+[\.\)]?\s*)?executive\s+summary$',
                r'^(?:\d+[\.\)]?\s*)?personal(?:\s+statement|profile)?$',
                r'^(?:\d+[\.\)]?\s*)?overview$',
            ],
            ResumeSection.CONTACT: [
                r'^(?:\d+[\.\)]?\s*)?contact(?:\s+information|details)?$',
                r'^(?:\d+[\.\)]?\s*)?personal(?:\s+information|details)?$',
                r'^(?:\d+[\.\)]?\s*)?get\s+in\s+touch$',
                r'^(?:\d+[\.\)]?\s*)?connect$',
                r'^(?:\d+[\.\)]?\s*)?(?:how\s+to\s+)?reach\s+me$',
            ],
            ResumeSection.LANGUAGES: [
                r'^(?:\d+[\.\)]?\s*)?languages?$',
                r'^(?:\d+[\.\)]?\s*)?language\s+proficiency$',
                r'^(?:\d+[\.\)]?\s*)?linguistic\s+skills$',
                r'^(?:\d+[\.\)]?\s*)?(?:foreign\s+)?languages$',
            ],
            ResumeSection.AWARDS: [
                r'^(?:\d+[\.\)]?\s*)?awards?(?:\s+and\s+honors?)?$',
                r'^(?:\d+[\.\)]?\s*)?honors?(?:\s+and\s+awards?)?$',
                r'^(?:\d+[\.\)]?\s*)?achievements?$',
                r'^(?:\d+[\.\)]?\s*)?recognitions?$',
                r'^(?:\d+[\.\)]?\s*)?accolades?$',
            ],
            ResumeSection.REFERENCES: [
                r'^(?:\d+[\.\)]?\s*)?references?$',
                r'^(?:\d+[\.\)]?\s*)?professional\s+references$',
                r'^(?:\d+[\.\)]?\s*)?referees?$',
            ],
            ResumeSection.VOLUNTEERING: [
                r'^(?:\d+[\.\)]?\s*)?volunteer(?:\s+experience|work)?$',
                r'^(?:\d+[\.\)]?\s*)?community\s+service$',
                r'^(?:\d+[\.\)]?\s*)?volunteering$',
            ],
            ResumeSection.INTERESTS: [
                r'^(?:\d+[\.\)]?\s*)?interests?$',
                r'^(?:\d+[\.\)]?\s*)?hobbies?$',
                r'^(?:\d+[\.\)]?\s*)?personal\s+interests$',
            ]
        }

        # Contextual indicators with weighted scores
        self.section_indicators = {
            ResumeSection.EXPERIENCE: [
                (r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\s*[-–—]\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+)?\d{4}\b',
                 2.0),  # Date ranges with months
                (r'\b\d{4}\s*[-–—]\s*(?:\d{4}|present|current|now)\b', 1.5),  # Date ranges
                (r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b', 1.0),  # Dates
                (r'\b(?:manager|engineer|developer|analyst|director|coordinator|specialist|consultant|associate|officer|executive)\b',
                 1.0),  # Job titles
                (r'\b(?:developed|managed|led|created|implemented|designed|architected|spearheaded|oversaw|coordinated)\b',
                 0.8),  # Action verbs
                (r'\b(?:responsibilities|duties|achievements|key\s+accomplishments)\b', 0.7),
                (r'\b(?:company|corporation|firm|organization|llc|inc|corp|gmbh)\b', 0.5),
            ],
            ResumeSection.EDUCATION: [
                (r'\b(?:bachelor|master|ph\.?d|doctorate|associate|b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|mba|msc|bsc|ba)\b',
                 2.0),  # Degrees
                (r'\b(?:university|college|institute|academy|school|faculty|department)\b', 1.5),  # Institutions
                (r'\bgpa\s*:?\s*\d+\.\d+\b', 1.5),  # GPA
                (r'\b(?:graduated|degree|major|minor|concentration|thesis|dissertation)\b', 1.0),  # Keywords
                (r'\b(?:dean\'?s\s+list|honors?|magna\s+cum\s+laude|cum\s+laude)\b', 1.0),
                (r'\b(?:coursework|relevant\s+courses|classes)\b', 0.8),
            ],
            ResumeSection.SKILLS: [
                (r'\b(?:python|java|javascript|react|node\.?js|sql|aws|docker|kubernetes|c\+\+|c#|\.net|ruby|php|html|css)\b',
                 1.0),  # Tech skills
                (r'\b(?:programming|software|technical|analytical|communication|leadership|problem-solving)\b', 0.8),
                (r'\b(?:languages?|frameworks?|libraries|tools|platforms|databases|operating\s+systems)\b', 0.7),
                (r'\b(?:proficient|experienced|skilled|familiar|knowledgeable)\b', 0.6),
                (r'\b(?:expert|advanced|intermediate|beginner|novice)\s+level\b', 0.6),
            ],
            ResumeSection.PROJECTS: [
                (r'\b(?:github|gitlab|bitbucket|demo|live\s+demo|source\s+code)\b', 1.0),
                (r'\b(?:built|created|developed|designed|implemented)\s+[a-z]+\s+(?:application|system|tool|website)\b',
                 1.0),
                (r'\b(?:technologies? used|tools used|stack)\b', 0.8),
                (r'\b(?:project|application|system|website|tool|platform)\b', 0.5),
            ],
            ResumeSection.CERTIFICATIONS: [
                (r'\b(?:certified|licensed|accredited|credential|certification)\b', 1.0),
                (r'\b(?:aws|microsoft|google|cisco|comptia|pmi|pmp)\b', 1.0),  # Common cert providers
                (r'\b(?:expiration|valid\s+until|issued|completed)\b', 0.7),
            ],
            ResumeSection.LANGUAGES: [
                (r'\b(?:english|spanish|french|german|chinese|japanese|russian|arabic|portuguese|italian)\b', 1.5),
                (r'\b(?:native|fluent|proficient|intermediate|basic|beginner)\s+(?:speaker|level)\b', 1.0),
                (r'\b(?:cefr|ielts|toefl|toeic)\b', 1.0),  # Language proficiency tests
            ]
        }

        # Common false positives to avoid
        self.false_positives = [
            r'^[0-9\s\.\-\(\)]+$',  # Lines with only numbers and symbols
            r'^.{1,2}$',  # Very short lines
            r'^.{100,}$',  # Very long lines (unlikely to be headers)
            r'^(?:page|resume|cv|curriculum vitae)$',  # Document metadata
            r'^(?:phone|email|address|linkedin|github)$',  # Contact info elements
        ]

        # Structural patterns for detecting section boundaries
        self.structural_patterns = {
            'bullet_points': r'^(?:\s*[•\-*\d+\.\)]\s+)',  # Bullet points or numbered lists
            'all_caps': r'^[A-Z][A-Z\s]{5,}$',  # All caps lines (often headers)
            'underline': r'^.*\n[-=]{3,}\s*$',  # Underlined text
            'bold_italic': r'(\*\*.+\*\*|_.+_)',  # Markdown-style bold/italic
        }

    def detect_sections(self, text: str) -> Dict[ResumeSection, List[SectionBoundary]]:
        """
        Detect resume sections and return their positions, content, and confidence scores.
        Uses multiple strategies: header matching, content analysis, and structural cues.
        """
        sections = {section: [] for section in ResumeSection}

        # First pass: detect explicit section headers
        header_sections = self._detect_sections_by_headers(text)

        # Second pass: detect sections by content patterns
        content_sections = self._detect_sections_by_content(text)

        # Third pass: detect sections by structural patterns
        structural_sections = self._detect_sections_by_structure(text)

        # Merge results with confidence weighting
        merged_sections = self._merge_section_detections(
            header_sections, content_sections, structural_sections
        )

        # Fill in gaps for undetected sections
        final_sections = self._fill_section_gaps(merged_sections, text)

        return final_sections

    def _detect_sections_by_headers(self, text: str) -> Dict[ResumeSection, List[SectionBoundary]]:
        """Detect sections based on explicit header patterns"""
        sections = {section: [] for section in ResumeSection}
        lines = text.split('\n')
        current_position = 0

        for i, line in enumerate(lines):
            line_start = current_position
            line_end = current_position + len(line)

            # Skip lines that are likely false positives
            if self._is_false_positive(line):
                current_position = line_end + 1
                continue

            # Check if this line matches any section header pattern
            detected_section, confidence = self._detect_section_header(line)

            if detected_section and confidence > 0.7:
                # Look ahead to find the section content
                content_start = line_end + 1
                content_end = self._find_section_end(lines, i, text, content_start)

                section_content = text[content_start:content_end].strip()
                if section_content:
                    sections[detected_section].append(SectionBoundary(
                        section=detected_section,
                        start=content_start,
                        end=content_end,
                        content=section_content,
                        confidence=confidence,
                        detected_by="header"
                    ))

            current_position = line_end + 1

        return sections

    def _detect_sections_by_content(self, text: str) -> Dict[ResumeSection, List[SectionBoundary]]:
        """Detect sections based on content patterns and contextual clues"""
        sections = {section: [] for section in ResumeSection}

        if self.nlp:
            # Use spaCy for more sophisticated content analysis
            doc = self.nlp(text)
            for sent in doc.sents:
                sent_text = sent.text.strip()
                if len(sent_text) < 20:  # Skip very short sentences
                    continue

                detected_section, confidence = self._detect_section_by_content(sent_text)
                if detected_section and confidence > 0.6:
                    sections[detected_section].append(SectionBoundary(
                        section=detected_section,
                        start=sent.start_char,
                        end=sent.end_char,
                        content=sent_text,
                        confidence=confidence,
                        detected_by="content"
                    ))
        else:
            # Fallback to regex-based content analysis
            lines = text.split('\n')
            current_position = 0

            for line in lines:
                line_start = current_position
                line_end = current_position + len(line)

                if len(line.strip()) > 20:  # Only consider substantial lines
                    detected_section, confidence = self._detect_section_by_content(line)
                    if detected_section and confidence > 0.6:
                        sections[detected_section].append(SectionBoundary(
                            section=detected_section,
                            start=line_start,
                            end=line_end,
                            content=line,
                            confidence=confidence,
                            detected_by="content"
                        ))

                current_position = line_end + 1

        return sections

    def _detect_sections_by_structure(self, text: str) -> Dict[ResumeSection, List[SectionBoundary]]:
        """Detect sections based on structural patterns like bullet points, formatting, etc."""
        sections = {section: [] for section in ResumeSection}
        lines = text.split('\n')
        current_position = 0
        current_section = ResumeSection.OTHER
        section_start = 0

        for i, line in enumerate(lines):
            line_start = current_position
            line_end = current_position + len(line)

            # Detect structural patterns that indicate section boundaries
            structural_section = self._detect_section_by_structure(line, lines, i)

            if structural_section and structural_section != current_section:
                # Save previous section
                if current_section != ResumeSection.OTHER and section_start < line_start:
                    section_content = text[section_start:line_start].strip()
                    if section_content:
                        sections[current_section].append(SectionBoundary(
                            section=current_section,
                            start=section_start,
                            end=line_start,
                            content=section_content,
                            confidence=0.7,
                            detected_by="structure"
                        ))

                # Start new section
                current_section = structural_section
                section_start = line_start
            elif current_section == ResumeSection.OTHER:
                # Try to infer section from content patterns
                content_section, confidence = self._detect_section_by_content(line)
                if content_section and confidence > 0.5:
                    current_section = content_section
                    section_start = line_start

            current_position = line_end + 1

        # Save the final section
        if current_section != ResumeSection.OTHER and section_start < len(text):
            section_content = text[section_start:].strip()
            if section_content:
                sections[current_section].append(SectionBoundary(
                    section=current_section,
                    start=section_start,
                    end=len(text),
                    content=section_content,
                    confidence=0.7,
                    detected_by="structure"
                ))

        return sections

    def _detect_section_header(self, line: str) -> Tuple[Optional[ResumeSection], float]:
        """Detect if a line is a section header and return section type with confidence"""
        line_lower = line.lower().strip()

        # Skip lines that are likely false positives
        if self._is_false_positive(line):
            return None, 0.0

        # Check against section patterns with confidence scoring
        best_match = None
        highest_confidence = 0.0

        for section, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.fullmatch(pattern, line_lower, re.IGNORECASE):
                    # Calculate confidence based on match specificity
                    confidence = 1.0
                    if '.*' in pattern or '.+' in pattern:
                        confidence = 0.9  # Less specific patterns get slightly lower confidence
                    if len(line_lower) < 5:
                        confidence *= 0.8  # Very short headers get lower confidence

                    if confidence > highest_confidence:
                        best_match = section
                        highest_confidence = confidence

        return best_match, highest_confidence

    def _detect_section_by_content(self, text: str) -> Tuple[Optional[ResumeSection], float]:
        """Detect section by content patterns with weighted confidence scoring"""
        text_lower = text.lower()
        section_scores = {section: 0.0 for section in self.section_indicators.keys()}

        # Score based on contextual indicators
        for section, indicators in self.section_indicators.items():
            for pattern, weight in indicators:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                section_scores[section] += len(matches) * weight

        # Find the section with the highest score
        best_section = None
        highest_score = 0.0

        for section, score in section_scores.items():
            if score > highest_score:
                best_section = section
                highest_score = score

        # Normalize confidence score (0.0 to 1.0)
        confidence = min(1.0, highest_score / 5.0) if highest_score > 0 else 0.0

        return best_section, confidence

    def _detect_section_by_structure(self, line: str, all_lines: List[str], line_index: int) -> Optional[ResumeSection]:
        """Detect section based on structural patterns"""
        line_stripped = line.strip()

        # Check for all-caps lines (often section headers)
        if re.match(self.structural_patterns['all_caps'], line_stripped):
            # Try to match with section patterns
            section, confidence = self._detect_section_header(line_stripped)
            if section and confidence > 0.7:
                return section

        # Check for underlined text
        if line_index < len(all_lines) - 1:
            next_line = all_lines[line_index + 1].strip()
            if re.fullmatch(r'[-=]{3,}', next_line):
                section, confidence = self._detect_section_header(line_stripped)
                if section and confidence > 0.7:
                    return section

        # Check for bullet points that might indicate the start of a new section
        if re.match(self.structural_patterns['bullet_points'], line):
            # Look backward to find the most recent section header
            for i in range(line_index - 1, max(0, line_index - 5), -1):
                prev_line = all_lines[i].strip()
                section, confidence = self._detect_section_header(prev_line)
                if section and confidence > 0.7:
                    return section

        return None

    def _is_false_positive(self, line: str) -> bool:
        """Check if a line is likely a false positive for section headers"""
        line_stripped = line.strip()

        if not line_stripped:
            return True

        for pattern in self.false_positives:
            if re.fullmatch(pattern, line_stripped, re.IGNORECASE):
                return True

        return False

    def _find_section_end(self, lines: List[str], current_index: int, full_text: str, content_start: int) -> int:
        """Find the end of a section by looking for the next section header"""
        for i in range(current_index + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            # Check if this line is a new section header
            section, confidence = self._detect_section_header(line)
            if section and confidence > 0.7:
                # Calculate the position of this new header
                position = full_text.find(line, content_start)
                if position != -1:
                    return position

        # If no next section found, return end of text
        return len(full_text)

    def _merge_section_detections(self, *section_dicts: Dict[ResumeSection, List[SectionBoundary]]) -> Dict[
        ResumeSection, List[SectionBoundary]]:
        """Merge multiple section detection results with confidence weighting"""
        merged = {section: [] for section in ResumeSection}

        # Collect all boundaries from all detection methods
        all_boundaries = []
        for section_dict in section_dicts:
            for section, boundaries in section_dict.items():
                all_boundaries.extend(boundaries)

        # Sort by start position
        all_boundaries.sort(key=lambda x: x.start)

        # Merge overlapping sections
        i = 0
        while i < len(all_boundaries):
            current = all_boundaries[i]
            j = i + 1

            # Find all overlapping sections
            while j < len(all_boundaries) and all_boundaries[j].start < current.end:
                next_boundary = all_boundaries[j]

                # Merge based on confidence
                if next_boundary.confidence > current.confidence:
                    current = next_boundary

                j += 1

            # Add the merged section
            merged[current.section].append(current)
            i = j

        return merged

    def _fill_section_gaps(self, sections: Dict[ResumeSection, List[SectionBoundary]], text: str) -> Dict[
        ResumeSection, List[SectionBoundary]]:
        """Fill in gaps for undetected sections using contextual analysis"""
        # Identify covered ranges
        covered_ranges = []
        for section_boundaries in sections.values():
            for boundary in section_boundaries:
                covered_ranges.append((boundary.start, boundary.end))

        # Sort covered ranges
        covered_ranges.sort()

        # Find gaps between covered ranges
        gaps = []
        current_end = 0

        for start, end in covered_ranges:
            if start > current_end:
                gaps.append((current_end, start))
            current_end = max(current_end, end)

        # Check if there's a gap at the end
        if current_end < len(text):
            gaps.append((current_end, len(text)))

        # Analyze each gap to assign to a section
        for gap_start, gap_end in gaps:
            gap_text = text[gap_start:gap_end].strip()
            if not gap_text or len(gap_text) < 20:
                continue

            # Try to detect section by content
            section, confidence = self._detect_section_by_content(gap_text)
            if section and confidence > 0.5:
                sections[section].append(SectionBoundary(
                    start=gap_start,
                    end=gap_end,
                    content=gap_text,
                    confidence=confidence,
                    detected_by="gap_filling"
                ))
            else:
                # Assign to OTHER if no section detected
                sections[ResumeSection.OTHER].append(SectionBoundary(
                    start=gap_start,
                    end=gap_end,
                    content=gap_text,
                    confidence=0.3,
                    detected_by="gap_filling"
                ))

        return sections

    def get_section_context(self, sections: Dict[ResumeSection, List[SectionBoundary]], position: int) -> ResumeSection:
        """Get the section context for a given text position with confidence"""
        best_section = ResumeSection.OTHER
        highest_confidence = 0.0

        for section, boundaries in sections.items():
            for boundary in boundaries:
                if boundary.start <= position <= boundary.end:
                    if boundary.confidence > highest_confidence:
                        best_section = section
                        highest_confidence = boundary.confidence

        return best_section

    def visualize_sections(self, text: str, sections: Dict[ResumeSection, List[SectionBoundary]]):
        """Create a visual representation of detected sections (for debugging)"""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        fig, ax = plt.subplots(figsize=(12, 6))

        colors = plt.cm.Set3.colors
        section_colors = {section: colors[i % len(colors)] for i, section in enumerate(ResumeSection)}

        y_pos = 0
        for section, boundaries in sections.items():
            for boundary in boundaries:
                width = boundary.end - boundary.start
                ax.add_patch(patches.Rectangle(
                    (boundary.start, y_pos), width, 1,
                    facecolor=section_colors[section],
                    edgecolor='black',
                    alpha=0.7
                ))
                # Add section label
                ax.text(boundary.start + width / 2, y_pos + 0.5, section.value,
                        ha='center', va='center', fontsize=8)
            y_pos += 1.2

        ax.set_xlim(0, len(text))
        ax.set_ylim(0, y_pos)
        ax.set_xlabel('Text Position')
        ax.set_title('Detected Resume Sections')
        ax.yaxis.set_visible(False)

        plt.tight_layout()
        plt.show()

class ContextAwareEntityExtractor:
    """
    Enhanced entity extractor that uses section context to improve extraction accuracy.
    """

    def __init__(self, nlp_model):
        self.nlp = nlp_model
        self.section_detector = IntelligentSectionDetector()

    def extract_entities_with_context(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract entities with section context awareness for better accuracy.
        """
        # Detect sections first
        sections = self.section_detector.detect_sections(text)

        # Extract entities with section context
        doc = self.nlp(text)
        entities_by_section = {section.value: [] for section in ResumeSection}

        for ent in doc.ents:
            # Get the section context for this entity
            section = self.section_detector.get_section_context(sections, ent.start_char)

            entities_by_section[section.value].append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # You can add confidence scoring here
            })

        return entities_by_section

    def enhance_entity_extraction(self, text: str, raw_entities: List[Dict]) -> List[Dict]:
        """
        Enhance entity extraction using section context and validation rules.
        """
        sections = self.section_detector.detect_sections(text)
        enhanced_entities = []

        for entity in raw_entities:
            # Get section context
            section = self.section_detector.get_section_context(sections, entity['start'])

            # Apply section-specific validation rules
            entity = self._validate_entity_with_context(entity, section)

            if entity:  # Only include if validation passes
                entity['section'] = section.value
                enhanced_entities.append(entity)

        return enhanced_entities

    def _validate_entity_with_context(self, entity: Dict, section: ResumeSection) -> Optional[Dict]:
        """
        Validate entities based on their section context.
        """
        # Example validation rules
        if section == ResumeSection.EDUCATION:
            if entity['label'] == 'COMPANY':
                # Companies in education section might actually be schools
                entity['label'] = 'SCHOOL'
                entity['confidence'] *= 0.8  # Reduce confidence slightly

        elif section == ResumeSection.SKILLS:
            if entity['label'] == 'COMPANY' and len(entity['text']) < 4:
                # Short company names in skills might be technologies
                entity['label'] = 'SKILL'
                entity['confidence'] *= 0.7

        # Add more context-aware validation rules as needed

        return entity