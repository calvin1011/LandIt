# augment_school.py
import random
import json
from typing import List


def augment_school_data() -> List:
    """Generate training data focused on educational institutions"""
    augmented_data = []

    # Templates for school/education mentions in resumes
    templates = [
        # Standard education formats
        ("{degree} from {school}", ["DEGREE", "SCHOOL"]),
        ("{school} - {degree}", ["SCHOOL", "DEGREE"]),
        ("{degree}, {school}", ["DEGREE", "SCHOOL"]),
        ("Attended {school} for {degree}", ["SCHOOL", "DEGREE"]),
        ("{school} | {degree}", ["SCHOOL", "DEGREE"]),

        # Education sections
        ("Education:\n{school}\n{degree} | {grad_year}", ["SCHOOL", "DEGREE", "DATE"]),
        ("{school}\n{degree}\n{grad_year}", ["SCHOOL", "DEGREE", "DATE"]),
        ("• {degree} from {school} ({grad_year})", ["DEGREE", "SCHOOL", "DATE"]),

        # Multiple degrees
        ("{school}: {degree} and {degree2}", ["SCHOOL", "DEGREE", "DEGREE"]),
        ("{school} - {degree}, {degree2}", ["SCHOOL", "DEGREE", "DEGREE"]),

        # With locations and details
        ("{school} ({location}) - {degree}", ["SCHOOL", "LOCATION", "DEGREE"]),
        ("{degree} from {school}, {location}", ["DEGREE", "SCHOOL", "LOCATION"]),
        ("{school} - {degree} - GPA: {gpa}", ["SCHOOL", "DEGREE", "EDUCATION"]),

        # Realistic resume formats
        ("EDUCATION\n{school}\n{degree} | {grad_year}", ["SCHOOL", "DEGREE", "DATE"]),
        ("ACADEMIC BACKGROUND\n• {degree} - {school} ({grad_year})", ["DEGREE", "SCHOOL", "DATE"]),
        ("{school}\n{degree}, {grad_year}\nGPA: {gpa}", ["SCHOOL", "DEGREE", "DATE", "EDUCATION"]),

        # Coursework and specializations
        ("{school} - {degree} with focus on {field}", ["SCHOOL", "DEGREE", "FIELD"]),
        ("{degree} in {field} from {school}", ["DEGREE", "FIELD", "SCHOOL"]),
        ("{school}: {degree} in {field}", ["SCHOOL", "DEGREE", "FIELD"]),

        # Multiple schools
        ("Education: {school} and {school2}", ["SCHOOL", "SCHOOL"]),
        ("Attended {school}, {school2}", ["SCHOOL", "SCHOOL"]),
        ("Schools: {school}, {school2}", ["SCHOOL", "SCHOOL"])
    ]

    # Extensive database of educational institutions
    samples = {
        "school": [
            # Ivy League
            "Harvard University", "Yale University", "Princeton University", "Columbia University",
            "University of Pennsylvania", "Brown University", "Dartmouth College", "Cornell University",

            # Top US Universities
            "Stanford University", "MIT", "Caltech", "University of Chicago", "Johns Hopkins University",
            "Northwestern University", "Duke University", "Vanderbilt University", "Rice University",
            "Washington University in St. Louis", "University of Notre Dame", "Georgetown University",

            # Public Universities
            "University of California, Berkeley", "UCLA", "University of Michigan", "University of Virginia",
            "University of North Carolina", "University of Texas at Austin", "University of Wisconsin-Madison",
            "University of Illinois at Urbana-Champaign", "University of Washington", "Georgia Tech",
            "University of Florida", "Ohio State University", "Penn State University", "University of Maryland",

            # Liberal Arts Colleges
            "Williams College", "Amherst College", "Swarthmore College", "Pomona College", "Wellesley College",
            "Bowdoin College", "Middlebury College", "Carleton College", "Claremont McKenna College",
            "Davidson College", "Haverford College", "Vassar College", "Colby College", "Hamilton College",

            # International Universities
            "University of Oxford", "University of Cambridge", "Imperial College London", "London School of Economics",
            "ETH Zurich", "University of Toronto", "McGill University", "University of British Columbia",
            "National University of Singapore", "University of Melbourne", "University of Sydney",
            "University of Tokyo", "Peking University", "Tsinghua University",

            # State Universities
            "University of California, San Diego", "UC Davis", "UC Santa Barbara", "UC Irvine",
            "University of Massachusetts Amherst", "University of Connecticut", "University of Colorado Boulder",
            "University of Arizona", "Arizona State University", "University of Utah", "University of Oregon",

            # Technical Institutes
            "Carnegie Mellon University", "Rensselaer Polytechnic Institute", "Worcester Polytechnic Institute",
            "Stevens Institute of Technology", "Illinois Institute of Technology", "Rochester Institute of Technology",

            # Business Schools
            "Wharton School", "Sloan School of Management", "Kellogg School of Management",
            "Booth School of Business", "Haas School of Business", "Anderson School of Management"
        ],

        "school2": [
            "Community College", "State College", "Technical Institute", "Online University",
            "Art Institute", "Music Conservatory", "Law School", "Medical School",
            "Graduate School", "Extension School", "Summer School", "Study Abroad Program"
        ],

        "degree": [
            "Bachelor of Science", "Bachelor of Arts", "Bachelor of Engineering", "Bachelor of Computer Science",
            "Master of Science", "Master of Arts", "Master of Business Administration", "Master of Engineering",
            "PhD", "Doctor of Philosophy", "Doctorate", "Postdoctoral Research",
            "Associate Degree", "Certificate", "Diploma", "High School Diploma",
            "Bachelor of Technology", "Master of Technology", "Bachelor of Fine Arts", "Master of Fine Arts",
            "Juris Doctor", "Medical Doctor", "Doctor of Medicine", "Bachelor of Architecture"
        ],

        "degree2": [
            "Minor in Mathematics", "Minor in Computer Science", "Minor in Economics", "Minor in Psychology",
            "Concentration in Data Science", "Specialization in AI", "Focus on Machine Learning",
            "Emphasis on Software Engineering", "Track in Cybersecurity", "Path in Cloud Computing"
        ],

        "grad_year": [
            "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016",
            "Expected 2024", "Expected 2025", "2024", "2025",
            "May 2023", "December 2022", "Spring 2021", "Fall 2020"
        ],

        "gpa": [
            "3.9/4.0", "3.8/4.0", "3.7/4.0", "3.6/4.0", "3.5/4.0", "3.4/4.0",
            "4.0/4.0", "3.95/4.0", "3.85/4.0", "3.75/4.0",
            "Summa Cum Laude", "Magna Cum Laude", "Cum Laude", "With Honors"
        ],

        "location": [
            "Cambridge, MA", "New Haven, CT", "Princeton, NJ", "New York, NY",
            "Ithaca, NY", "Stanford, CA", "Cambridge, MA", "Pasadena, CA",
            "Chicago, IL", "Baltimore, MD", "Evanston, IL", "Durham, NC",
            "Berkeley, CA", "Los Angeles, CA", "Ann Arbor, MI", "Charlottesville, VA"
        ],

        "field": [
            "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Civil Engineering",
            "Data Science", "Artificial Intelligence", "Machine Learning", "Computer Engineering",
            "Mathematics", "Physics", "Chemistry", "Biology", "Economics", "Psychology",
            "Business Administration", "Finance", "Marketing", "Accounting",
            "Political Science", "International Relations", "History", "English Literature"
        ]
    }

    print("🎓 Generating school/education-focused training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(35):  # Generate 35 examples per template
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
                if placeholder.startswith('school'):
                    label_type = "SCHOOL"
                elif placeholder.startswith('degree'):
                    label_type = "DEGREE"
                elif placeholder in ['grad_year']:
                    label_type = "DATE"
                elif placeholder == 'gpa':
                    label_type = "EDUCATION"
                elif placeholder == 'location':
                    label_type = "LOCATION"
                elif placeholder == 'field':
                    label_type = "FIELD"
                else:
                    label_type = placeholder.upper()

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data, samples


def main():
    """Main function to generate and save school training data"""
    print("🚀 Generating Educational Institutions Training Data")
    print("=" * 60)
    print("Covering: Ivy League, Top Universities, Public Universities, and more!")
    print("=" * 60)

    # Generate school-focused data
    school_data, samples = augment_school_data()

    # Save to file
    output_file = "train_data_schools.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(school_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(school_data)} school-focused examples")
    print(f"💾 Saved to {output_file}")

    # Show sample statistics
    print(f"\n📊 Covering {len(samples['school'])}+ educational institutions:")
    categories = [
        "Ivy League", "Top US Universities", "Public Universities", "Liberal Arts Colleges",
        "International Universities", "Technical Institutes", "Business Schools"
    ]

    for category in categories:
        print(f"   • {category}")

    print(f"\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this additional data")
    print("   2. Update train.py to include train_data_schools.json")
    print("   3. Your model will better distinguish schools from companies")
    print("   4. Expect improved SCHOOL and DEGREE label recognition")


if __name__ == "__main__":
    main()