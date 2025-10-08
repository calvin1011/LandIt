import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SemanticResumeExtractor:
    """
    Semantic resume extractor using advanced pattern matching and rules
    No external ML dependencies initially - pure Python approach
    """

    def __init__(self):
        logger.info(" SemanticResumeExtractor initialized")

    def extract_semantic_entities(self, text: str) -> Dict:
        """Extract entities using advanced pattern matching"""
        try:
            results = {
                "contact_info": self._extract_contact_info(text),
                "work_experience": self._extract_work_experience(text),
                "education": self._extract_education(text),
                "skills": self._extract_skills(text),
                "achievements": self._extract_achievements(text)
            }

            # Convert to entity format
            entities = self._convert_to_entity_format(results, text)

            return {
                "entities": entities,
                "structured_data": results,
                "confidence": 0.8,
                "method": "semantic_pattern_extraction"
            }

        except Exception as e:
            logger.error(f"SemanticResumeExtractor failed: {e}")
            return {"entities": [], "confidence": 0.0}

    def _extract_contact_info(self, text: str) -> Dict:
        """Extract contact information using improved patterns"""
        contact_info = {}

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info["email"] = email_match.group()

        # Extract phone
        phone_patterns = [
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # (555) 123-4567
            r'\d{3}[-.]?\d{3}[-.]?\d{4}',  # 555-123-4567
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact_info["phone"] = phone_match.group()
                break

        # Extract name (from first few lines)
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            words = line.split()
            if 2 <= len(words) <= 3:
                if all(word[0].isupper() and word[1:].islower() for word in words if word.isalpha()):
                    # Not a section header
                    if not any(header in line.upper() for header in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY']):
                        contact_info["name"] = line
                        break

        # Extract location
        location_pattern = r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b'  # City, ST
        location_match = re.search(location_pattern, text)
        if location_match:
            contact_info["location"] = location_match.group()

        return contact_info

    def _extract_skills(self, text: str) -> List[Dict]:
        """Extract skills using comprehensive keyword matching"""
        # Comprehensive skill database
        skills_db = {
            "Programming Languages": [
                "python", "java", "javascript", "typescript", "c++", "c#",
                "php", "ruby", "go", "rust", "swift", "kotlin", "scala", "sql",
                "powershell", "bash"
            ],
            "Web Technologies": [
                "react", "angular", "vue", "html", "css", "nodejs", "node.js",
                "express", "django", "flask", "spring", "bootstrap",
                "next.js", "graphql"
            ],
            "Databases": [
                "mysql", "postgresql", "mongodb", "redis", "sqlite",
                "oracle", "sql server", "elasticsearch", "dynamodb"
            ],
            "Cloud & DevOps": [
                "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
                "git", "gitlab", "github", "terraform", "ansible", "linux",
                "ci/cd", "circleci"
            ],
            "Data Science & ML": [
                "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
                "machine learning", "deep learning", "natural language processing"
            ]
        }

        found_skills = []
        text_lower = text.lower()

        for category, skills_list in skills_db.items():
            for skill in skills_list:
                if skill in text_lower:
                    found_skills.append({
                        "name": skill.title(),
                        "category": category,
                        "confidence": 0.9,
                        "method": "keyword_match"
                    })

        return found_skills

    def _extract_work_experience(self, text: str) -> List[Dict]:
        """Extract work experience using pattern matching"""
        experiences = []

        # Pattern for job title | company
        job_pattern = r'([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Technician|Intern|Manager|Analyst|Supervisor))\s*[|\-–]\s*([A-Z][a-zA-Z\s]+(?:University|Amazon|Google|Microsoft|Company|Corp|Inc|LLC)?)'

        matches = re.findall(job_pattern, text)
        for title, company in matches:
            experiences.append({
                "title": title.strip(),
                "company": company.strip(),
                "confidence": 0.8
            })

        return experiences

    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []

        # Degree patterns
        degree_pattern = r'(Bachelor|Master|PhD|Doctorate|Associates?)\s+(?:of\s+)?(?:Science\s+in\s+|Arts\s+in\s+)?([A-Z][a-zA-Z\s]+)'
        matches = re.findall(degree_pattern, text, re.IGNORECASE)

        for degree_type, field in matches:
            education.append({
                "degree": f"{degree_type} of Science in {field}".strip(),
                "confidence": 0.8
            })

        # GPA extraction
        gpa_pattern = r'GPA:\s*(\d+\.?\d*)'
        gpa_match = re.search(gpa_pattern, text)
        if gpa_match and education:
            education[0]["gpa"] = gpa_match.group(1)

        return education

    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements and accomplishments"""
        achievements = []

        # Look for bullet points with action verbs
        bullet_pattern = r'[•·▪▫‣⁃]\s*([A-Z][^•·▪▫‣⁃\n]+)'
        matches = re.findall(bullet_pattern, text)

        for match in matches:
            if len(match.strip()) > 20:  # Reasonable length
                achievements.append(match.strip())

        return achievements[:10]  # Limit to 10

    def _convert_to_entity_format(self, results: Dict, original_text: str) -> List[Dict]:
        """Convert results to entity format"""
        entities = []

        # Convert contact info
        contact = results.get("contact_info", {})
        for info_type, value in contact.items():
            if value:
                start_pos = original_text.find(value)
                if start_pos != -1:
                    entities.append({
                        "text": value,
                        "label": info_type.upper(),
                        "start": start_pos,
                        "end": start_pos + len(value),
                        "confidence": 0.9,
                        "source": "semantic"
                    })

        # Convert skills
        skills = results.get("skills", [])
        for skill in skills:
            skill_name = skill["name"]
            start_pos = original_text.lower().find(skill_name.lower())
            if start_pos != -1:
                entities.append({
                    "text": skill_name,
                    "label": "SKILL",
                    "start": start_pos,
                    "end": start_pos + len(skill_name),
                    "confidence": skill["confidence"],
                    "source": "semantic",
                    "category": skill["category"]
                })

        # Convert work experience
        work_exp = results.get("work_experience", [])
        for exp in work_exp:
            # Add job title
            title = exp["title"]
            start_pos = original_text.find(title)
            if start_pos != -1:
                entities.append({
                    "text": title,
                    "label": "TITLE",
                    "start": start_pos,
                    "end": start_pos + len(title),
                    "confidence": exp["confidence"],
                    "source": "semantic"
                })

            # Add company
            company = exp["company"]
            start_pos = original_text.find(company)
            if start_pos != -1:
                entities.append({
                    "text": company,
                    "label": "COMPANY",
                    "start": start_pos,
                    "end": start_pos + len(company),
                    "confidence": exp["confidence"],
                    "source": "semantic"
                })

        return entities


# Test the extractor
if __name__ == "__main__":
    extractor = SemanticResumeExtractor()

    test_text = """
    Calvin Ssendawula
    Software Engineer
    cssendawula@adams.edu | (719) 587-7246 | Alamosa, CO

    RESNET Technician | Adams State University | September 2023 - Present
    • Troubleshoot network connectivity issues for residential students
    • Configure network equipment and maintain campus internet infrastructure

    Software Development Engineer Intern | Amazon | June 2023 - August 2023
    • Developed scalable web applications using Python and Java

    EDUCATION
    Bachelor of Science in Computer Science | Adams State University | Expected May 2024
    GPA: 3.7/4.0

    TECHNICAL SKILLS
    Programming Languages: Python, Java, JavaScript, SQL
    Web Technologies: React, Node.js, Express.js, HTML, CSS
    Databases: MySQL, PostgreSQL, MongoDB
    Cloud & DevOps: AWS, Docker, Git, Linux
    """

    results = extractor.extract_semantic_entities(test_text)

    print(" SemanticResumeExtractor Test Results:")
    print(f"Entities found: {len(results['entities'])}")
    print(f"Overall confidence: {results['confidence']}")

    print("\n Extracted Entities:")
    for entity in results['entities']:
        source = entity.get('source', 'unknown')
        confidence = entity.get('confidence', 0.0)
        category = f" ({entity['category']})" if entity.get('category') else ""
        print(f"• {entity['text']} → {entity['label']}{category} [{source}, {confidence:.2f}]")

    print("\n Structured Data:")
    structured = results['structured_data']

    contact = structured.get('contact_info', {})
    if contact:
        print(" Contact Info:")
        for field, value in contact.items():
            print(f"   {field}: {value}")

    skills = structured.get('skills', [])
    if skills:
        print(f"️ Skills by Category:")
        skill_categories = {}
        for skill in skills:
            category = skill['category']
            if category not in skill_categories:
                skill_categories[category] = []
            skill_categories[category].append(skill['name'])

        for category, skill_list in skill_categories.items():
            print(f"   {category}: {', '.join(skill_list)}")

    work_exp = structured.get('work_experience', [])
    if work_exp:
        print("💼 Work Experience:")
        for exp in work_exp:
            print(f"   • {exp['title']} at {exp['company']}")