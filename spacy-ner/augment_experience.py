import json
import random

def generate_experience_data(num_examples=150):
    """Generates augmented data for work experience durations."""

    years = [str(i) for i in range(1, 11)] + ["-5", "5+", "several", "many", "2-3"]

    # Add more templates to create varied sentences
    templates = [
        "Boasts {exp} years of professional experience.",
        "With over {exp} years in the field.",
        "A seasoned professional with {exp} years of dedicated experience.",
        "Professional Experience: {exp} years.",
        "Experience: {exp} years.",
        "Summary: A developer with {exp} years of experience in software engineering."
    ]

    augmented_data = []
    for _ in range(num_examples):
        template = random.choice(templates)
        experience_str = random.choice(years)
        text = template.format(exp=experience_str)

        # Find the start and end of the experience entity
        start_index = text.find(experience_str)
        end_index = start_index + len(experience_str)

        entities = [(start_index, end_index, "EXPERIENCE")]

        augmented_data.append([text, {"entities": entities}])

    # Save to the parent directory where train.py is
    with open("train_data_experience_refined.json", "w") as f:
        json.dump(augmented_data, f, indent=2)

    print(f"Generated {len(augmented_data)} refined experience examples.")

if __name__ == "__main__":
    generate_experience_data()