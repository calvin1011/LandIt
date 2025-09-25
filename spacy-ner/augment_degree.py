# augment_degree.py
import random
import json
from typing import List


def augment_degree_data() -> List:
    """Generate training data focused on degrees and educational details"""
    augmented_data = []

    # Templates for degree and educational details
    templates = [
        # Degree-focused formats
        ("{degree} in {field}", ["DEGREE", "FIELD"]),
        ("{degree} with concentration in {field}", ["DEGREE", "FIELD"]),
        ("{degree} specializing in {field}", ["DEGREE", "FIELD"]),
        ("{degree} with focus on {field}", ["DEGREE", "FIELD"]),
        ("{degree} - {field} major", ["DEGREE", "FIELD"]),

        # With academic details
        ("{degree} | GPA: {gpa}", ["DEGREE", "EDUCATION"]),
        ("{degree} - Graduated {grad_year}", ["DEGREE", "DATE"]),
        ("{degree} | {grad_year} | GPA: {gpa}", ["DEGREE", "DATE", "EDUCATION"]),
        ("{degree} - {grad_year} - {gpa}", ["DEGREE", "DATE", "EDUCATION"]),

        # Academic achievements
        ("{degree} with {honors}", ["DEGREE", "EDUCATION"]),
        ("{degree} - {honors}", ["DEGREE", "EDUCATION"]),
        ("{degree} | {honors} | GPA: {gpa}", ["DEGREE", "EDUCATION", "EDUCATION"]),

        # Coursework and specializations
        ("{degree} with coursework in {course1}, {course2}, {course3}", ["DEGREE", "FIELD", "FIELD", "FIELD"]),
        ("{degree} focusing on {specialization1} and {specialization2}", ["DEGREE", "FIELD", "FIELD"]),
        ("{degree} with expertise in {tech1}, {tech2}", ["DEGREE", "SKILL", "SKILL"]),

        # Research and projects
        ("{degree} with research in {research_area}", ["DEGREE", "FIELD"]),
        ("{degree} - Thesis: {thesis_topic}", ["DEGREE", "PROJECT"]),
        ("{degree} with capstone project in {project_area}", ["DEGREE", "PROJECT"]),

        # Multiple degrees and combinations
        ("{degree} and {degree2}", ["DEGREE", "DEGREE"]),
        ("{degree} with {degree2}", ["DEGREE", "DEGREE"]),
        ("Dual degrees: {degree} and {degree2}", ["DEGREE", "DEGREE"]),

        # Realistic resume formats
        ("EDUCATION\n{degree} in {field}\n{grad_year} | GPA: {gpa}", ["DEGREE", "FIELD", "DATE", "EDUCATION"]),
        ("{degree}\n{field} Concentration\n{grad_year} - {gpa}", ["DEGREE", "FIELD", "DATE", "EDUCATION"]),
        ("• {degree} in {field} ({grad_year})", ["DEGREE", "FIELD", "DATE"]),

        # With minor/secondary focus
        ("{degree} with minor in {minor}", ["DEGREE", "FIELD"]),
        ("{degree} and minor in {minor}", ["DEGREE", "FIELD"]),
        ("{degree} with secondary focus in {secondary}", ["DEGREE", "FIELD"])
    ]

    # Extensive database of degrees and educational details
    samples = {
        "degree": [
            "Bachelor of Science", "BS", "B.S.", "Bachelor of Arts", "BA", "B.A.",
            "Bachelor of Engineering", "BE", "B.Eng", "Bachelor of Computer Science", "BCS", "B.CS.",
            "Master of Science", "MS", "M.S.", "Master of Arts", "MA", "M.A.",
            "Master of Business Administration", "MBA", "M.B.A.", "Master of Engineering", "ME", "M.Eng",
            "PhD", "Ph.D", "Doctor of Philosophy", "Doctorate", "Postdoctoral Research",
            "Associate Degree", "AA", "A.S.", "Certificate", "Diploma", "High School Diploma",
            "Bachelor of Technology", "B.Tech", "Master of Technology", "M.Tech",
            "Bachelor of Fine Arts", "BFA", "Master of Fine Arts", "MFA",
            "Juris Doctor", "JD", "J.D.", "Medical Doctor", "MD", "M.D.",
            "Bachelor of Architecture", "B.Arch", "Master of Architecture", "M.Arch"
        ],

        "degree2": [
            "Master of Data Science", "MDS", "Master of Computer Science", "MCS",
            "Master of Artificial Intelligence", "MAI", "Master of Machine Learning", "MML",
            "Bachelor of Mathematics", "BMath", "Bachelor of Physics", "BPhys",
            "Master of Finance", "MF", "Master of Accounting", "MAcc",
            "Executive MBA", "EMBA", "Online MBA", "Part-time MBA"
        ],

        "field": [
            "Computer Science", "CS", "Electrical Engineering", "EE", "Mechanical Engineering", "ME",
            "Civil Engineering", "CE", "Data Science", "Artificial Intelligence", "AI", "Machine Learning", "ML",
            "Computer Engineering", "CE", "Software Engineering", "SE", "Information Technology", "IT",
            "Mathematics", "Math", "Physics", "Chemistry", "Biology", "Biochemistry",
            "Economics", "Psychology", "Sociology", "Political Science", "International Relations",
            "Business Administration", "Finance", "Marketing", "Accounting", "Management",
            "English Literature", "History", "Philosophy", "Communications", "Journalism"
        ],

        "grad_year": [
            "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015",
            "Expected 2024", "Expected 2025", "2024", "2025", "2026",
            "May 2023", "December 2022", "Spring 2021", "Fall 2020", "Winter 2019",
            "Class of 2023", "Class of 2022", "Graduated 2021"
        ],

        "gpa": [
            "3.9/4.0", "3.8/4.0", "3.7/4.0", "3.6/4.0", "3.5/4.0", "3.4/4.0", "3.3/4.0",
            "4.0/4.0", "3.95/4.0", "3.85/4.0", "3.75/4.0", "3.65/4.0",
            "Summa Cum Laude", "Magna Cum Laude", "Cum Laude", "With Honors", "With Distinction",
            "3.8 GPA", "3.7 GPA", "3.6 GPA", "3.5 GPA", "4.0 GPA",
            "92%", "90%", "88%", "85%", "First Class", "First Division"
        ],

        "honors": [
            "Honors", "With Honors", "High Honors", "Highest Honors", "Dean's List",
            "President's List", "Academic Excellence", "Research Excellence",
            "Thesis Honors", "Departmental Honors", "College Honors",
            "Gold Medal", "Silver Medal", "Bronze Medal", "Academic Award"
        ],

        "course1": ["Algorithms", "Data Structures", "Machine Learning", "Database Systems"],
        "course2": ["Computer Networks", "Operating Systems", "Software Engineering", "Web Development"],
        "course3": ["Artificial Intelligence", "Cloud Computing", "Cybersecurity", "Data Mining"],

        "specialization1": ["Machine Learning", "Data Science", "AI", "Cloud Computing"],
        "specialization2": ["Cybersecurity", "DevOps", "Mobile Development", "Web Technologies"],

        "tech1": ["Python", "Java", "JavaScript", "C++", "SQL"],
        "tech2": ["React", "Node.js", "AWS", "Docker", "Kubernetes"],

        "research_area": ["Computer Vision", "NLP", "Robotics", "Quantum Computing"],
        "thesis_topic": ["Deep Learning Applications", "AI Ethics", "Cloud Security", "Big Data Analytics"],
        "project_area": ["Web Development", "Mobile App", "Data Analysis", "Machine Learning Model"],

        "minor": ["Mathematics", "Computer Science", "Economics", "Psychology", "Business"],
        "secondary": ["Data Science", "AI", "Cybersecurity", "Cloud Computing", "UX Design"]
    }

    print("🎓 Generating degree-focused training data...")

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

                # Map placeholder to label type
                if placeholder.startswith('degree'):
                    label_type = "DEGREE"
                elif placeholder == 'field':
                    label_type = "FIELD"
                elif placeholder in ['grad_year']:
                    label_type = "DATE"
                elif placeholder in ['gpa', 'honors']:
                    label_type = "EDUCATION"
                elif placeholder.startswith('course') or placeholder.startswith('specialization'):
                    label_type = "FIELD"
                elif placeholder.startswith('tech'):
                    label_type = "SKILL"
                elif placeholder in ['research_area', 'thesis_topic', 'project_area']:
                    label_type = "PROJECT" if 'project' in placeholder or 'thesis' in placeholder else "FIELD"
                elif placeholder in ['minor', 'secondary']:
                    label_type = "FIELD"
                else:
                    label_type = placeholder.upper()

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data, samples


def main():
    """Main function to generate and save degree training data"""
    print(" Generating Degree & Educational Details Training Data")
    print("=" * 70)
    print("Covering: Degrees, Fields, GPAs, Honors, Specializations, and more!")
    print("=" * 70)

    # Generate degree-focused data
    degree_data, samples = augment_degree_data()

    # Save to file
    output_file = "train_data_degrees.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(degree_data, f, indent=2, ensure_ascii=False)

    print(f" Generated {len(degree_data)} degree-focused examples")
    print(f" Saved to {output_file}")

    # Show sample statistics
    print(f"\n Covering comprehensive educational details:")
    categories = [
        "Degree types", "Academic fields", "GPA formats", "Honors designations",
        "Specializations", "Research areas", "Coursework examples"
    ]

    for category in categories:
        print(f"   • {category}")


if __name__ == "__main__":
    main()