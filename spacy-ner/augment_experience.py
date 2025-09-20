
import random
import json
from typing import List

def augment_experience_data() -> List:
    """Generate training data focused on work experience and durations"""
    augmented_data = []

    # Templates for experience mentions in resumes
    templates = [
        # Experience duration formats
        ("{duration} of experience in {field}", ["DATE", "EXPERIENCE", "FIELD"]),
        ("{years} years experience in {industry}", ["DATE", "EXPERIENCE", "INDUSTRY"]),
        ("Over {years} years in {field}", ["DATE", "EXPERIENCE", "FIELD"]),
        ("{years}+ years of professional experience", ["DATE", "EXPERIENCE"]),
        ("{total_experience} of total work experience", ["DATE", "EXPERIENCE"]),

        # Specific experience contexts
        ("{years} years in {role} roles", ["DATE", "EXPERIENCE", "TITLE"]),
        ("{duration} as a {title}", ["DATE", "EXPERIENCE", "TITLE"]),
        ("{years} years at {company} as {title}", ["DATE", "EXPERIENCE", "COMPANY", "TITLE"]),

        # Industry experience
        ("{years} years in {industry} industry", ["DATE", "EXPERIENCE", "INDUSTRY"]),
        ("{duration} in {field} field", ["DATE", "EXPERIENCE", "FIELD"]),
        ("Extensive experience in {tech} spanning {years} years", ["EXPERIENCE", "SKILL", "DATE"]),

        # Management and leadership experience
        ("{years} years of management experience", ["DATE", "EXPERIENCE"]),
        ("{duration} in leadership roles", ["DATE", "EXPERIENCE"]),
        ("{years} years leading {team_size} teams", ["DATE", "EXPERIENCE", "OTHER"]),

        # Technical experience
        ("{years} years of {tech} experience", ["DATE", "EXPERIENCE", "SKILL"]),
        ("{duration} working with {tech1} and {tech2}", ["DATE", "EXPERIENCE", "SKILL", "SKILL"]),
        ("{years} years hands-on experience with {tech}", ["DATE", "EXPERIENCE", "SKILL"]),

        # Project experience
        ("{years} years of project management experience", ["DATE", "EXPERIENCE"]),
        ("{duration} managing {project_type} projects", ["DATE", "EXPERIENCE", "PROJECT"]),
        ("{years} years experience delivering {project_scale} projects", ["DATE", "EXPERIENCE", "OTHER"]),

        # International experience
        ("{years} years of international experience", ["DATE", "EXPERIENCE"]),
        ("{duration} working in {country}", ["DATE", "EXPERIENCE", "LOCATION"]),
        ("{years} years across multiple continents", ["DATE", "EXPERIENCE"]),

        # Realistic resume formats
        ("EXPERIENCE SUMMARY\n{total_experience} in {industry}", ["DATE", "EXPERIENCE", "INDUSTRY"]),
        ("• {years} years of {field} experience", ["DATE", "EXPERIENCE", "FIELD"]),
        ("{duration} professional experience with focus on {specialization}", ["DATE", "EXPERIENCE", "FIELD"]),

        # With achievements
        ("{years} years experience with expertise in {achievement_area}", ["DATE", "EXPERIENCE", "ACHIEVEMENT"]),
        ("{duration} delivering {achievement_result}", ["DATE", "EXPERIENCE", "ACHIEVEMENT"]),
        ("{years} years driving {business_outcome}", ["DATE", "EXPERIENCE", "ACHIEVEMENT"])
    ]

    # Extensive database of experience-related terms
    samples = {
        "years": ["5", "8", "10", "12", "15", "20", "25", "3", "7", "6", "4", "2", "1"],
        "duration": [
            "5 years", "8 years", "10+ years", "15 years", "20+ years",
            "3 years", "7 years", "6+ years", "4 years", "2 years",
            "Over 10 years", "More than 5 years", "Nearly 8 years", "Approximately 12 years"
        ],
        "total_experience": [
            "10+ years", "15 years", "20 years", "8+ years", "12 years",
            "5 years", "7 years", "25+ years", "30 years", "3 years"
        ],

        "field": [
            "software development", "data science", "cloud computing", "cybersecurity",
            "web development", "mobile development", "devops", "machine learning",
            "artificial intelligence", "database management", "network administration",
            "project management", "product management", "UX design", "quality assurance"
        ],

        "industry": [
            "technology", "finance", "healthcare", "e-commerce", "education",
            "manufacturing", "telecommunications", "media", "entertainment",
            "automotive", "aerospace", "retail", "hospitality", "energy"
        ],

        "role": [
            "software engineering", "data analysis", "system administration", "network engineering",
            "cloud architecture", "security analysis", "devops engineering", "machine learning engineering",
            "product management", "project management", "technical leadership", "quality assurance"
        ],

        "title": [
            "Software Engineer", "Senior Developer", "Lead Engineer", "Principal Architect",
            "Data Scientist", "ML Engineer", "DevOps Specialist", "Cloud Engineer",
            "Security Analyst", "Network Administrator", "Project Manager", "Product Manager"
        ],

        "company": [
            "Google", "Microsoft", "Amazon", "Facebook", "Apple", "Netflix", "Twitter",
            "Uber", "Airbnb", "Salesforce", "Oracle", "IBM", "Intel", "Cisco"
        ],

        "tech": [
            "Python", "Java", "JavaScript", "C++", "React", "Node.js", "AWS",
            "Azure", "Docker", "Kubernetes", "TensorFlow", "PyTorch", "SQL",
            "MongoDB", "PostgreSQL", "Redis", "Kafka", "Spark", "Hadoop"
        ],

        "tech1": ["Python", "Java", "JavaScript", "C++", "React"],
        "tech2": ["AWS", "Docker", "Kubernetes", "TensorFlow", "SQL"],

        "team_size": ["small", "medium", "large", "cross-functional", "distributed", "agile"],

        "project_type": [
            "software development", "infrastructure", "data migration", "cloud transformation",
            "security implementation", "API development", "mobile application", "web application"
        ],

        "project_scale": [
            "enterprise-level", "large-scale", "mission-critical", "complex",
            "multi-million dollar", "global", "strategic", "high-impact"
        ],

        "country": [
            "United States", "Canada", "United Kingdom", "Germany", "France",
            "Australia", "Japan", "Singapore", "India", "China", "Brazil"
        ],

        "specialization": [
            "machine learning", "cloud infrastructure", "cybersecurity", "data engineering",
            "frontend development", "backend systems", "devops automation", "mobile platforms"
        ],

        "achievement_area": [
            "performance optimization", "cost reduction", "revenue growth", "process improvement",
            "team building", "innovation", "customer satisfaction", "security enhancement"
        ],

        "achievement_result": [
            "successful projects", "on-time deliveries", "budget compliance", "quality improvements",
            "security enhancements", "performance gains", "customer solutions", "innovative features"
        ],

        "business_outcome": [
            "revenue growth", "cost savings", "efficiency improvements", "market expansion",
            "customer acquisition", "retention rates", "operational excellence", "digital transformation"
        ]
    }

    print("💼 Generating experience-focused training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(25):  # Generate 25 examples per template
            text = template
            entities = []
            current_pos = 0

            # Replace each placeholder with sample values
            placeholders = []
            for part in template.split():
                if part.startswith('{') and part.endswith('}'):
                    placeholders.append(part[1:-1])

            for placeholder in placeholders:
                sample = random.choice(samples[placeholder])
                text = text.replace(f"{{{placeholder}}}", sample, 1)

                # Find the position of this entity in the final text
                start_pos = text.find(sample, current_pos)
                if start_pos == -1:
                    continue
                end_pos = start_pos + len(sample)

                # Map placeholder to label type
                if placeholder in ['years', 'duration', 'total_experience']:
                    label_type = "DATE"
                elif placeholder == 'field':
                    label_type = "FIELD"
                elif placeholder == 'industry':
                    label_type = "INDUSTRY"
                elif placeholder == 'role':
                    label_type = "TITLE"
                elif placeholder == 'title':
                    label_type = "TITLE"
                elif placeholder == 'company':
                    label_type = "COMPANY"
                elif placeholder.startswith('tech'):
                    label_type = "SKILL"
                elif placeholder in ['team_size', 'project_scale']:
                    label_type = "OTHER"
                elif placeholder == 'project_type':
                    label_type = "PROJECT"
                elif placeholder == 'country':
                    label_type = "LOCATION"
                elif placeholder == 'specialization':
                    label_type = "FIELD"
                elif placeholder.startswith('achievement') or placeholder == 'business_outcome':
                    label_type = "ACHIEVEMENT"
                else:
                    label_type = placeholder.upper()

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            # Add EXPERIENCE label for the overall context
            if "experience" in text.lower():
                exp_start = text.lower().find("experience")
                if exp_start != -1:
                    entities.append([exp_start, exp_start + 10, "EXPERIENCE"])

            augmented_data.append([text, {"entities": entities}])

    return augmented_data, samples


def main():
    """Main function to generate and save experience training data"""
    print("🚀 Generating Work Experience & Duration Training Data")
    print("=" * 70)
    print("Covering: Experience durations, industries, roles, technologies, and more!")
    print("=" * 70)

    # Generate experience-focused data
    experience_data, samples = augment_experience_data()

    # Save to file
    output_file = "train_data_experience.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(experience_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(experience_data)} experience-focused examples")
    print(f"💾 Saved to {output_file}")

    # Show sample statistics
    print(f"\n📊 Covering comprehensive experience contexts:")
    categories = [
        "Experience durations", "Industry sectors", "Technical roles",
        "Technologies & skills", "Project types", "Achievement areas",
        "International experience", "Management experience"
    ]

    for category in categories:
        print(f"   • {category}")

    print(f"\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this additional data")
    print("   2. Update train.py to include train_data_experience.json")
    print("   3. Your model will better understand experience contexts")
    print("   4. Expect improved EXPERIENCE label recognition and duration parsing")


if __name__ == "__main__":
    main()