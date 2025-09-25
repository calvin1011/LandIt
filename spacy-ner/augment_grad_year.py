import random
import json
from typing import List


def augment_grad_year_data() -> List:
    """Generate training data focused on graduation years"""
    augmented_data = []

    # Templates for graduation year mentions
    templates = [
        # Graduation year formats
        ("Graduated {grad_year}", ["GRAD_YEAR"]),
        ("Class of {grad_year}", ["GRAD_YEAR"]),
        ("Expected graduation: {grad_year}", ["GRAD_YEAR"]),
        ("Degree completed in {grad_year}", ["GRAD_YEAR"]),
        ("{grad_year} graduate", ["GRAD_YEAR"]),
        ("Alumni, class of {grad_year}", ["GRAD_YEAR"]),
        ("Completed studies in {grad_year}", ["GRAD_YEAR"]),
        ("Graduation year: {grad_year}", ["GRAD_YEAR"]),
        ("{grad_year} alumni", ["GRAD_YEAR"]),
        ("Earned degree in {grad_year}", ["GRAD_YEAR"]),

        # With context
        ("{degree} earned in {grad_year}", ["DEGREE", "GRAD_YEAR"]),
        ("{school}, class of {grad_year}", ["SCHOOL", "GRAD_YEAR"]),
        ("{field} degree completed {grad_year}", ["FIELD", "GRAD_YEAR"]),
        ("Graduated from {school} in {grad_year}", ["SCHOOL", "GRAD_YEAR"]),

        # Resume formats
        ("EDUCATION\n{degree}\n{school}, {grad_year}", ["DEGREE", "SCHOOL", "GRAD_YEAR"]),
        ("GRADUATION DATE\n{grad_year}", ["GRAD_YEAR"]),
        ("DEGREE COMPLETION\n{grad_year}", ["GRAD_YEAR"]),
        ("{school} - {grad_year}", ["SCHOOL", "GRAD_YEAR"])
    ]

    # Graduation year samples
    samples = {
        "grad_year": [str(year) for year in range(1990, 2030)],
        "degree": [
            "Bachelor of Science", "BS", "Master of Science", "MS", "PhD",
            "Bachelor of Arts", "BA", "Master of Arts", "MA", "Doctorate"
        ],
        "school": [
            "Harvard University", "Stanford University", "MIT", "University of California, Berkeley",
            "Carnegie Mellon University", "University of Michigan", "Columbia University",
            "University of Texas at Austin", "Georgia Institute of Technology", "University of Illinois"
        ],
        "field": [
            "Computer Science", "Data Science", "Electrical Engineering", "Mathematics",
            "Economics", "Business Administration", "Physics", "Psychology"
        ]
    }

    print(" Generating graduation year training data...")

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
                if placeholder == 'grad_year':
                    label_type = "GRAD_YEAR"
                elif placeholder == 'degree':
                    label_type = "DEGREE"
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
    """Main function to generate and save graduation year training data"""
    print(" Generating Graduation Year Training Data")
    print("=" * 60)
    print("Covering: Graduation years, class years, completion dates!")
    print("=" * 60)

    # Generate grad year data
    grad_year_data = augment_grad_year_data()

    # Save to file
    output_file = "train_data_grad_year.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grad_year_data, f, indent=2, ensure_ascii=False)

    print(f" Generated {len(grad_year_data)} graduation year examples")
    print(f" Saved to {output_file}")

    print(f"\n Coverage includes:")
    print("   • Graduation years (1990-2030)")
    print("   • Class year mentions")
    print("   • Degree completion dates")
    print("   • Various formatting styles")


if __name__ == "__main__":
    main()