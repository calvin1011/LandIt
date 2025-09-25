import openai
from openai import OpenAI
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
import os
from enum import Enum

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    TRENDING = "trending"
    NICE_TO_HAVE = "nice_to_have"


class ProjectDifficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class ProjectRecommendation:
    title: str
    description: str
    skills_addressed: List[str]
    difficulty: ProjectDifficulty
    estimated_weeks: int
    learning_outcomes: List[str]
    resources: List[Dict[str, str]]
    milestones: List[str]
    portfolio_value: str
    market_relevance: str


class AIProjectGenerator:
    """
    AI-powered project recommendation generator using GPT
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI project generator

        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

        # Initialize OpenAI client with new syntax
        self.client = OpenAI(api_key=self.api_key)

        # Configuration
        self.model = "gpt-3.5-turbo"  # Cost-effective choice
        self.max_tokens = 2000
        self.temperature = 0.7  # Balance creativity and consistency

        logger.info("AI Project Generator initialized")

    def generate_learning_plan(self,
                               user_profile: Dict[str, Any],
                               job_data: Dict[str, Any],
                               skill_gaps_detailed: Dict[str, List[str]],
                               gap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive learning plan with AI-powered project recommendations

        Args:
            user_profile: User's current skills, experience level, etc.
            job_data: Target job information
            skill_gaps_detailed: Categorized skill gaps
            gap_analysis: Gap severity analysis

        Returns:
            Complete learning plan with project recommendations
        """
        try:
            start_time = time.time()

            # Generate projects for different skill categories
            learning_plan = {
                "overview": self._generate_plan_overview(user_profile, job_data, gap_analysis),
                "critical_projects": [],
                "important_projects": [],
                "trending_projects": [],
                "timeline": self._generate_timeline(gap_analysis),
                "success_metrics": self._generate_success_metrics(job_data),
                "next_steps": []
            }

            # Generate projects for critical skills (highest priority)
            if skill_gaps_detailed.get('critical'):
                learning_plan["critical_projects"] = self._generate_projects_for_skills(
                    skill_gaps_detailed['critical'],
                    SkillCategory.CRITICAL,
                    user_profile,
                    job_data,
                    max_projects=3
                )

            # Generate projects for important skills
            if skill_gaps_detailed.get('important'):
                learning_plan["important_projects"] = self._generate_projects_for_skills(
                    skill_gaps_detailed['important'],
                    SkillCategory.IMPORTANT,
                    user_profile,
                    job_data,
                    max_projects=2
                )

            # Generate projects for trending skills (future-proofing)
            if skill_gaps_detailed.get('trending'):
                learning_plan["trending_projects"] = self._generate_projects_for_skills(
                    skill_gaps_detailed['trending'],
                    SkillCategory.TRENDING,
                    user_profile,
                    job_data,
                    max_projects=1
                )

            # Generate actionable next steps
            learning_plan["next_steps"] = self._generate_next_steps(learning_plan, gap_analysis)

            processing_time = time.time() - start_time

            learning_plan["metadata"] = {
                "generated_at": time.time(),
                "processing_time": processing_time,
                "target_job": f"{job_data.get('title')} at {job_data.get('company')}",
                "user_experience_level": user_profile.get('experience_level', 'mid')
            }

            logger.info(f"Generated learning plan in {processing_time:.2f}s")
            return learning_plan

        except Exception as e:
            logger.error(f"Failed to generate learning plan: {e}")
            return self._generate_fallback_plan(skill_gaps_detailed, gap_analysis)

    def _generate_projects_for_skills(self,
                                      skills: List[str],
                                      category: SkillCategory,
                                      user_profile: Dict[str, Any],
                                      job_data: Dict[str, Any],
                                      max_projects: int = 3) -> List[Dict[str, Any]]:
        """Generate AI-powered project recommendations for specific skills"""

        try:
            # Create context-aware prompt
            prompt = self._build_project_prompt(skills, category, user_profile, job_data, max_projects)

            # Call GPT API with new syntax
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Parse GPT response
            gpt_content = response.choices[0].message.content
            projects = self._parse_gpt_response(gpt_content, category)

            return projects[:max_projects]  # Limit number of projects

        except Exception as e:
            logger.error(f"Failed to generate projects for {skills}: {e}")
            return self._generate_fallback_projects(skills, category, max_projects)

    def _build_project_prompt(self,
                              skills: List[str],
                              category: SkillCategory,
                              user_profile: Dict[str, Any],
                              job_data: Dict[str, Any],
                              max_projects: int) -> str:
        """Build a context-aware prompt for GPT"""

        user_experience = user_profile.get('experience_level', 'mid')
        current_skills = user_profile.get('current_skills', [])

        prompt = f"""
        I need {max_projects} practical project recommendations for a {user_experience}-level developer to learn these {category.value} skills: {', '.join(skills)}

        TARGET ROLE: {job_data.get('title', 'Software Engineer')} at {job_data.get('company', 'tech company')}
        CURRENT SKILLS: {', '.join(current_skills[:10])}
        EXPERIENCE LEVEL: {user_experience}

        For each project, provide:
        1. Project Title (specific and engaging)
        2. Description (2-3 sentences explaining what they'll build)
        3. Skills Addressed (which missing skills this project teaches)
        4. Difficulty Level (beginner/intermediate/advanced)
        5. Estimated Timeline (in weeks)
        6. Learning Outcomes (3-4 specific things they'll learn)
        7. Resources (2-3 helpful learning resources)
        8. Milestones (3-4 progress checkpoints)
        9. Portfolio Value (how this helps job applications)
        10. Market Relevance (why these skills matter in 2024)

        REQUIREMENTS:
        - Projects should be portfolio-worthy and job-relevant
        - Focus on practical, hands-on learning
        - Include real-world applications they can showcase
        - Projects should build on their existing {user_experience}-level knowledge
        - Consider what {job_data.get('company', 'hiring companies')} values

        FORMAT: Return as valid JSON array with each project as an object with the above fields.
        """

        return prompt

    def _get_system_prompt(self) -> str:
        """Get the system prompt for GPT to ensure consistent project recommendations"""
        return """You are an expert software engineering mentor and career advisor. You specialize in creating practical, portfolio-worthy project recommendations that help developers bridge skill gaps and land their target jobs.

        Your project recommendations should be:
        - Practical and immediately actionable
        - Portfolio-worthy (something they can showcase to employers)
        - Appropriately scoped for the timeframe
        - Industry-relevant and current with 2024 standards
        - Building on existing skills rather than starting from zero
        - Focused on real-world applications companies actually use

        Always consider the user's experience level and current skills when recommending projects. Make sure projects are challenging but achievable, and clearly explain the career value of each project."""

    def _parse_gpt_response(self, gpt_content: str, category: SkillCategory) -> List[Dict[str, Any]]:
        """Parse GPT response into structured project data"""
        try:
            # Try to extract JSON from GPT response
            json_start = gpt_content.find('[')
            json_end = gpt_content.rfind(']') + 1

            if json_start != -1 and json_end != -1:
                json_content = gpt_content[json_start:json_end]
                projects_data = json.loads(json_content)

                # Validate and structure the projects
                structured_projects = []
                for project in projects_data:
                    if isinstance(project, dict) and 'Project Title' in project:
                        structured_project = {
                            "title": project.get('Project Title', 'Unnamed Project'),
                            "description": project.get('Description', ''),
                            "skills_addressed": project.get('Skills Addressed', []),
                            "difficulty": project.get('Difficulty Level', 'intermediate'),
                            "estimated_weeks": self._parse_timeline(project.get('Estimated Timeline', '2 weeks')),
                            "learning_outcomes": project.get('Learning Outcomes', []),
                            "resources": self._structure_resources(project.get('Resources', [])),
                            "milestones": project.get('Milestones', []),
                            "portfolio_value": project.get('Portfolio Value', ''),
                            "market_relevance": project.get('Market Relevance', ''),
                            "category": category.value,
                            "ai_generated": True
                        }
                        structured_projects.append(structured_project)

                return structured_projects

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT JSON response: {e}")
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")

        # Fallback: try to extract basic project info from text
        return self._extract_projects_from_text(gpt_content, category)

    def _parse_timeline(self, timeline_str: str) -> int:
        """Extract weeks from timeline string"""
        try:
            # Extract number from strings like "2 weeks", "3-4 weeks", "1 month"
            timeline_lower = timeline_str.lower()
            if 'week' in timeline_lower:
                numbers = [int(s) for s in timeline_str.split() if s.isdigit()]
                return numbers[0] if numbers else 2
            elif 'month' in timeline_lower:
                numbers = [int(s) for s in timeline_str.split() if s.isdigit()]
                return (numbers[0] * 4) if numbers else 4
            else:
                return 2  # Default 2 weeks
        except:
            return 2

    def _structure_resources(self, resources: List[str]) -> List[Dict[str, str]]:
        """Structure resources into a consistent format"""
        structured = []
        for resource in resources:
            if isinstance(resource, str):
                structured.append({
                    "title": resource,
                    "type": "tutorial",
                    "url": ""  # GPT doesn't provide real URLs
                })
            elif isinstance(resource, dict):
                structured.append(resource)

        return structured

    def _extract_projects_from_text(self, text: str, category: SkillCategory) -> List[Dict[str, Any]]:
        """Fallback method to extract project info from unstructured text"""
        # This is a simplified fallback - in production, you might use more sophisticated NLP
        lines = text.split('\n')
        projects = []

        current_project = {}
        for line in lines:
            line = line.strip()
            if line.startswith('1.') or line.startswith('Project') or line.startswith('Title'):
                if current_project:
                    projects.append(current_project)
                current_project = {
                    "title": line.split(':', 1)[-1].strip() if ':' in line else "AI-Generated Project",
                    "description": "Learn new skills through hands-on practice",
                    "skills_addressed": [],
                    "difficulty": "intermediate",
                    "estimated_weeks": 2,
                    "learning_outcomes": ["Practical experience", "Portfolio project"],
                    "resources": [],
                    "milestones": ["Setup", "Development", "Completion"],
                    "portfolio_value": "Demonstrates practical skills",
                    "market_relevance": "In-demand technology",
                    "category": category.value,
                    "ai_generated": True
                }

        if current_project:
            projects.append(current_project)

        return projects[:3]  # Limit to 3 projects

    def _generate_plan_overview(self, user_profile: Dict, job_data: Dict, gap_analysis: Dict) -> str:
        """Generate an AI-powered overview of the learning plan"""
        try:
            prompt = f"""
            Create a motivational and strategic overview for a learning plan:

            USER: {user_profile.get('experience_level', 'mid')}-level developer
            TARGET: {job_data.get('title')} at {job_data.get('company')}
            GAPS: {gap_analysis.get('critical_gaps', 0)} critical skills, {gap_analysis.get('estimated_learning_weeks', 8)} weeks estimated
            DIFFICULTY: {gap_analysis.get('difficulty_level', 'medium')}

            Write 2-3 sentences that:
            1. Acknowledge their current strengths
            2. Outline the strategic approach to bridging gaps
            3. Motivate them about the outcome

            Tone: Professional but encouraging, like a mentor
            """

            # Updated to use new OpenAI API syntax
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.6
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate overview: {e}")
            return f"Strategic learning plan to bridge {gap_analysis.get('critical_gaps', 0)} critical skill gaps for your target {job_data.get('title')} role. Focus on hands-on projects that build both skills and portfolio value."

    def _generate_timeline(self, gap_analysis: Dict) -> Dict[str, Any]:
        """Generate a strategic timeline for the learning plan"""
        total_weeks = gap_analysis.get('estimated_learning_weeks', 8)

        return {
            "total_duration_weeks": total_weeks,
            "phase_1_critical": min(total_weeks // 2, 6),  # Focus on critical skills first
            "phase_2_important": min(total_weeks // 3, 4),
            "phase_3_trending": min(total_weeks // 4, 2),
            "weekly_commitment": "10-15 hours recommended",
            "milestones": [
                f"Week {total_weeks // 4}: Complete first critical project",
                f"Week {total_weeks // 2}: Portfolio review checkpoint",
                f"Week {total_weeks * 3 // 4}: Begin job applications",
                f"Week {total_weeks}: Final portfolio polish"
            ]
        }

    def _generate_success_metrics(self, job_data: Dict) -> List[str]:
        """Generate measurable success metrics"""
        return [
            "Complete at least 2 portfolio-worthy projects",
            f"Demonstrate proficiency in key {job_data.get('title', 'role')} skills",
            "Receive positive feedback on portfolio projects",
            "Successfully complete technical interviews",
            f"Land {job_data.get('title')} role or similar position"
        ]

    def _generate_next_steps(self, learning_plan: Dict, gap_analysis: Dict) -> List[str]:
        """Generate immediate next steps"""
        steps = []

        if learning_plan.get('critical_projects'):
            first_project = learning_plan['critical_projects'][0]
            steps.append(f"Start with: {first_project.get('title', 'First critical project')}")

        steps.extend([
            "Set up development environment and project repository",
            "Schedule 2-3 focused learning sessions per week",
            "Join relevant developer communities for support",
            "Plan weekly progress reviews and portfolio updates"
        ])

        return steps

    def _generate_fallback_plan(self, skill_gaps_detailed: Dict, gap_analysis: Dict) -> Dict[str, Any]:
        """Generate a fallback plan if AI generation fails"""
        return {
            "overview": f"Strategic learning plan to address {len(skill_gaps_detailed.get('critical', []))} critical skill gaps.",
            "critical_projects": self._generate_fallback_projects(
                skill_gaps_detailed.get('critical', []),
                SkillCategory.CRITICAL,
                2
            ),
            "important_projects": [],
            "trending_projects": [],
            "timeline": self._generate_timeline(gap_analysis),
            "success_metrics": ["Complete projects", "Build portfolio", "Apply for roles"],
            "next_steps": ["Choose first project", "Set up environment", "Begin learning"],
            "metadata": {
                "generated_at": time.time(),
                "fallback_mode": True,
                "ai_generation_failed": True
            }
        }

    def _generate_fallback_projects(self, skills: List[str], category: SkillCategory, max_projects: int) -> List[
        Dict[str, Any]]:
        """Generate basic fallback projects if AI fails"""
        projects = []

        # Basic project templates
        templates = {
            SkillCategory.CRITICAL: {
                "title": "Essential Skills Project",
                "description": "Build a practical application to demonstrate core competencies",
                "estimated_weeks": 3
            },
            SkillCategory.IMPORTANT: {
                "title": "Skills Enhancement Project",
                "description": "Develop additional capabilities through hands-on practice",
                "estimated_weeks": 2
            },
            SkillCategory.TRENDING: {
                "title": "Emerging Technology Project",
                "description": "Explore cutting-edge tools and frameworks",
                "estimated_weeks": 1
            }
        }

        template = templates.get(category, templates[SkillCategory.CRITICAL])

        for i, skill in enumerate(skills[:max_projects]):
            projects.append({
                "title": f"{skill.title()} {template['title']}",
                "description": f"Learn {skill} through {template['description'].lower()}",
                "skills_addressed": [skill],
                "difficulty": "intermediate",
                "estimated_weeks": template['estimated_weeks'],
                "learning_outcomes": [f"Master {skill}", "Build portfolio project"],
                "resources": [{"title": f"{skill} documentation", "type": "docs", "url": ""}],
                "milestones": ["Setup", "Development", "Testing", "Completion"],
                "portfolio_value": f"Demonstrates {skill} proficiency",
                "market_relevance": f"{skill} is in high demand",
                "category": category.value,
                "ai_generated": False,
                "fallback": True
            })

        return projects