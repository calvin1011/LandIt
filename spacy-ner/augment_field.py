
import random
import json
from typing import List


def augment_field_data() -> List:
    """Generate training data focused on academic and professional fields"""
    augmented_data = []

    # Templates for field/specialization mentions
    templates = [
        # Academic field formats
        ("{degree} in {field}", ["DEGREE", "FIELD"]),
        ("{degree} with major in {field}", ["DEGREE", "FIELD"]),
        ("{field} major", ["FIELD"]),
        ("Studied {field} at {school}", ["FIELD", "SCHOOL"]),
        ("Focus on {field}", ["FIELD"]),

        # Specializations and concentrations
        ("Specialization in {specialization}", ["FIELD"]),
        ("Concentration in {concentration}", ["FIELD"]),
        ("Emphasis on {emphasis}", ["FIELD"]),
        ("Focus area: {focus_area}", ["FIELD"]),
        ("Track: {track}", ["FIELD"]),

        # Minor and secondary fields
        ("Minor in {minor}", ["FIELD"]),
        ("Double major in {field1} and {field2}", ["FIELD", "FIELD"]),
        ("{field1} and {field2} double major", ["FIELD", "FIELD"]),
        ("Secondary field in {secondary_field}", ["FIELD"]),

        # Research and thesis fields
        ("Research in {research_field}", ["FIELD"]),
        ("Thesis on {thesis_topic}", ["FIELD"]),
        ("Dissertation in {dissertation_field}", ["FIELD"]),
        ("Published research in {research_area}", ["FIELD"]),

        # Professional field expertise
        ("Expertise in {professional_field}", ["FIELD"]),
        ("Domain knowledge in {domain}", ["FIELD"]),
        ("Industry focus: {industry_focus}", ["FIELD"]),
        ("Professional background in {background_field}", ["FIELD"]),

        # Technical field specializations
        ("{tech_field} specialist", ["FIELD"]),
        ("Specialized in {technical_field}", ["FIELD"]),
        ("{tech_domain} expert", ["FIELD"]),
        ("Advanced knowledge in {advanced_field}", ["FIELD"]),

        # Cross-functional fields
        ("{field1} with applications in {field2}", ["FIELD", "FIELD"]),
        ("Interdisciplinary focus on {field1} and {field2}", ["FIELD", "FIELD"]),
        ("Bridge between {field1} and {field2}", ["FIELD", "FIELD"]),

        # Realistic resume formats
        ("EDUCATION\n{degree} in {field}\n{school}", ["DEGREE", "FIELD", "SCHOOL"]),
        ("SPECIALIZATION\n• {specialization1}\n• {specialization2}", ["FIELD", "FIELD"]),
        ("FIELD OF STUDY\n{field} with focus on {subfield}", ["FIELD", "FIELD"]),
        ("ACADEMIC FOCUS\n{main_field} and {secondary_field}", ["FIELD", "FIELD"]),

        # With coursework
        ("Coursework in {course1}, {course2}, {course3}", ["FIELD", "FIELD", "FIELD"]),
        ("Advanced courses in {advanced_course1} and {advanced_course2}", ["FIELD", "FIELD"]),
        ("Relevant coursework: {course1}, {course2}", ["FIELD", "FIELD"])
    ]

    # Comprehensive database of academic and professional fields
    samples = {
        "degree": [
            "Bachelor of Science", "BS", "Master of Science", "MS", "PhD",
            "Bachelor of Arts", "BA", "Master of Arts", "MA", "Doctorate"
        ],

        "field": [
            "Computer Science", "Data Science", "Artificial Intelligence", "Machine Learning",
            "Electrical Engineering", "Mechanical Engineering", "Civil Engineering", "Chemical Engineering",
            "Mathematics", "Physics", "Chemistry", "Biology", "Biochemistry", "Neuroscience",
            "Economics", "Psychology", "Sociology", "Political Science", "International Relations",
            "Business Administration", "Finance", "Marketing", "Accounting", "Management",
            "English Literature", "History", "Philosophy", "Communications", "Journalism",
            "Computer Engineering", "Software Engineering", "Information Technology", "Cybersecurity"
        ],

        "specialization": [
            "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
            "Cloud Computing", "Distributed Systems", "Database Systems", "Network Security",
            "Quantitative Finance", "Financial Modeling", "Investment Analysis", "Risk Management",
            "Digital Marketing", "Brand Management", "Consumer Behavior", "Market Research",
            "Clinical Psychology", "Cognitive Science", "Behavioral Economics", "Social Psychology"
        ],

        "concentration": [
            "Data Analytics", "Business Intelligence", "Big Data", "Data Engineering",
            "Software Architecture", "DevOps", "Cloud Infrastructure", "Mobile Development",
            "UX Research", "Human-Computer Interaction", "Information Architecture", "Usability",
            "Corporate Finance", "Investment Banking", "Financial Planning", "Wealth Management"
        ],

        "emphasis": [
            "Algorithm Design", "System Architecture", "Performance Optimization", "Scalability",
            "Statistical Analysis", "Predictive Modeling", "Experimental Design", "Data Visualization",
            "Strategic Planning", "Organizational Behavior", "Leadership", "Change Management"
        ],

        "focus_area": [
            "AI Ethics", "Responsible AI", "Explainable AI", "AI Safety",
            "Cloud Security", "Network Defense", "Cyber Threat Intelligence", "Digital Forensics",
            "Sustainable Business", "Social Entrepreneurship", "Corporate Social Responsibility"
        ],

        "track": [
            "Data Science Track", "AI Track", "Systems Track", "Theory Track",
            "Finance Track", "Marketing Track", "Consulting Track", "Analytics Track",
            "Research Track", "Applied Track", "Professional Track", "Academic Track"
        ],

        "minor": [
            "Mathematics", "Computer Science", "Economics", "Psychology", "Business",
            "Statistics", "Physics", "Chemistry", "Philosophy", "History"
        ],

        "field1": ["Computer Science", "Mathematics", "Physics", "Economics", "Psychology"],
        "field2": ["Biology", "Statistics", "Engineering", "Business", "Neuroscience"],

        "secondary_field": [
            "Data Science", "AI", "Cybersecurity", "Cloud Computing", "UX Design",
            "Finance", "Marketing", "Management", "Communications", "Education"
        ],

        "research_field": [
            "Computer Vision", "NLP", "Robotics", "Quantum Computing", "Bioinformatics",
            "Computational Biology", "Neuroeconomics", "Behavioral Finance", "Social Network Analysis"
        ],

        "thesis_topic": [
            "Deep Learning Applications", "AI Ethics", "Cloud Security", "Big Data Analytics",
            "Algorithm Optimization", "System Performance", "User Experience", "Market Trends"
        ],

        "dissertation_field": [
            "Machine Learning Theory", "Computational Complexity", "Information Theory",
            "Behavioral Economics", "Cognitive Science", "Social Psychology", "Political Economy"
        ],

        "research_area": [
            "AI Research", "Data Science", "Computational Linguistics", "Computer Graphics",
            "Theoretical Physics", "Organic Chemistry", "Molecular Biology", "Clinical Research"
        ],

        "professional_field": [
            "Software Development", "Data Analysis", "Project Management", "Product Management",
            "UX Design", "Quality Assurance", "Technical Writing", "Business Analysis"
        ],

        "domain": [
            "Healthcare", "Finance", "E-commerce", "Education", "Manufacturing",
            "Telecommunications", "Media", "Entertainment", "Automotive", "Aerospace"
        ],

        "industry_focus": [
            "FinTech", "HealthTech", "EdTech", "MedTech", "CleanTech",
            "BioTech", "AgriTech", "RetailTech", "InsurTech", "PropTech"
        ],

        "background_field": [
            "Technical Background", "Scientific Background", "Business Background",
            "Research Background", "Engineering Background", "Academic Background"
        ],

        "tech_field": [
            "Frontend Development", "Backend Development", "Full Stack Development",
            "Mobile Development", "DevOps", "Cloud Architecture", "Data Engineering"
        ],

        "technical_field": [
            "Database Management", "Network Administration", "System Administration",
            "Security Analysis", "Performance Engineering", "Quality Engineering"
        ],

        "tech_domain": [
            "Web Technologies", "Mobile Platforms", "Cloud Services", "Data Platforms",
            "Security Systems", "Networking Infrastructure", "Storage Solutions"
        ],

        "advanced_field": [
            "Distributed Systems", "Parallel Computing", "High-Performance Computing",
            "Machine Learning Operations", "AI Infrastructure", "Big Data Systems"
        ],

        "specialization1": [
            "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
            "Cloud Computing", "Distributed Systems", "Database Systems", "Network Security"
        ],

        "specialization2": [
            "Quantitative Finance", "Financial Modeling", "Investment Analysis", "Risk Management",
            "Digital Marketing", "Brand Management", "Consumer Behavior", "Market Research"
        ],

        "main_field": [
            "Computer Science", "Data Science", "Electrical Engineering", "Mechanical Engineering",
            "Mathematics", "Physics", "Economics", "Business Administration"
        ],

        "subfield": [
            "Neural Networks", "Reinforcement Learning", "Computer Vision", "NLP",
            "Microservices", "Containerization", "Serverless Architecture", "Edge Computing"
        ],

        "school": [
            "Harvard University", "Stanford University", "MIT", "University of California, Berkeley",
            "Carnegie Mellon University", "University of Michigan", "Columbia University",
            "University of Texas at Austin", "Georgia Institute of Technology", "University of Illinois",
            "Princeton University", "Yale University", "Cornell University", "University of Washington",
            "California Institute of Technology", "University of Pennsylvania", "University of Chicago",
            "University of Southern California", "New York University", "University of California, Los Angeles"
        ],

        "course1": ["Algorithms", "Data Structures", "Machine Learning", "Database Systems"],
        "course2": ["Computer Networks", "Operating Systems", "Software Engineering", "Web Development"],
        "course3": ["Artificial Intelligence", "Cloud Computing", "Cybersecurity", "Data Mining"],

        "advanced_course1": ["Advanced Algorithms", "Deep Learning", "Distributed Systems", "Computer Vision"],
        "advanced_course2": ["Natural Language Processing", "Reinforcement Learning", "Cloud Security",
                             "Big Data Analytics"]
    }

    print("📚 Generating field/specialization training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(30):  # Generate 30 examples per template
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

                # Map placeholder to FIELD label for all academic/professional fields
                label_type = "FIELD"

                # Except for these special cases
                if placeholder == 'degree':
                    label_type = "DEGREE"
                elif placeholder == 'school':
                    label_type = "SCHOOL"

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data, samples


def main():
    """Main function to generate and save field training data"""
    print("🚀 Generating Academic & Professional Fields Training Data")
    print("=" * 75)
    print("Covering: Academic majors, specializations, research areas, professional domains!")
    print("=" * 75)

    # Generate field-focused data
    field_data, samples = augment_field_data()

    # Save to file
    output_file = "train_data_fields.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(field_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(field_data)} field-focused examples")
    print(f"💾 Saved to {output_file}")

    # Show sample statistics
    print(f"\n📊 Covering comprehensive field contexts:")
    categories = [
        "Academic majors", "Technical specializations", "Research areas",
        "Professional domains", "Industry focuses", "Interdisciplinary fields",
        "Coursework areas", "Thesis topics"
    ]

    for category in categories:
        print(f"   • {category}")

    print(f"\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this additional data")
    print("   2. Update train.py to include train_data_fields.json")
    print("   3. Your model will better understand academic and professional fields")
    print("   4. Expect improved FIELD label recognition (currently 0 examples)")


if __name__ == "__main__":
    main()