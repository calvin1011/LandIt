import random
import json
from typing import List


def augment_gpa_data() -> List:
    """Generate training data focused on GPA mentions"""
    augmented_data = []

    # Templates for GPA mentions
    templates = [
        # Standard GPA formats
        ("GPA: {gpa}", ["GPA"]),
        ("Grade Point Average: {gpa}", ["GPA"]),
        ("Cumulative GPA: {gpa}", ["GPA"]),
        ("Overall GPA: {gpa}", ["GPA"]),
        ("GPA {gpa}", ["GPA"]),
        ("{gpa} GPA", ["GPA"]),

        # With scale
        ("GPA: {gpa}/4.0", ["GPA"]),
        ("{gpa} on 4.0 scale", ["GPA"]),
        ("{gpa} cumulative GPA on 4.0 scale", ["GPA"]),
        ("{gpa} out of 4.0", ["GPA"]),

        # Academic context
        ("Academic performance: {gpa} GPA", ["GPA"]),
        ("Graduated with {gpa} GPA", ["GPA"]),
        ("Maintained {gpa} GPA", ["GPA"]),
        ("Achieved {gpa} GPA", ["GPA"]),

        # Major-specific GPA
        ("Major GPA: {gpa}", ["GPA"]),
        ("{field} GPA: {gpa}", ["FIELD", "GPA"]),
        ("In-major GPA: {gpa}", ["GPA"]),

        # Resume formats
        ("EDUCATION\nGPA: {gpa}", ["GPA"]),
        ("ACADEMIC RECORD\nCumulative GPA: {gpa}", ["GPA"]),
        ("GRADES\nOverall GPA: {gpa}/4.0", ["GPA"]),
        ("{school}\nGPA: {gpa}", ["SCHOOL", "GPA"])
    ]

    # GPA samples
    samples = {
        "gpa": [
            "3.9", "3.8", "3.7", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0",
            "3.95", "3.85", "3.75", "3.65", "3.55", "3.45", "3.35", "3.25", "3.15",
            "4.0", "3.98", "3.92", "3.87", "3.81", "3.79", "3.72", "3.68", "3.63"
        ],
        "school": [
            "Harvard University", "Stanford University", "MIT", "University of California, Berkeley",
            "Carnegie Mellon University", "University of Michigan", "Columbia University"
        ],
        "field": [
            "Computer Science", "Data Science", "Electrical Engineering", "Mathematics",
            "Economics", "Business Administration", "Physics"
        ]
    }

    print("📊 Generating GPA training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(20):  # Generate 20 examples per template
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

                # Map placeholder to appropriate label
                if placeholder == 'gpa':
                    label_type = "GPA"
                elif placeholder == 'school':
                    label_type = "SCHOOL"
                elif placeholder == 'field':
                    label_type = "FIELD"
                else:
                    label_type = placeholder.upper()

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data


def main():
    """Main function to generate and save GPA training data"""
    print("🚀 Generating GPA Training Data")
    print("=" * 50)
    print("Covering: GPA formats, scales, and academic contexts!")
    print("=" * 50)

    # Generate GPA data
    gpa_data = augment_gpa_data()

    # Save to file
    output_file = "train_data_gpa.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(gpa_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(gpa_data)} GPA examples")
    print(f"💾 Saved to {output_file}")

    print(f"\n📊 Coverage includes:")
    print("   • Various GPA formats (3.8, 3.75, etc.)")
    print("   • Scale mentions (/4.0, on 4.0 scale)")
    print("   • Cumulative and major-specific GPA")
    print("   • Resume-style formatting")

    print(f"\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this additional data")
    print("   2. Update train.py to include train_data_gpa.json")
    print("   3. Your model will better understand GPA formats and contexts")


if __name__ == "__main__":
    main()