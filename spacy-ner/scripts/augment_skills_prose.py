import json
import random

# Templates for generating contextual sentences with skills
CONTEXTUAL_TEMPLATES = [
    "Experienced in {skill1} and {skill2}, with a strong command of {skill3}.",
    "Led a team to build a scalable application using {skill1}, {skill2}, and {skill3}.",
    "Applied {skill1} and {skill2} for predictive analysis and data visualization.",
    "Proficient in a range of technologies including {skill1}, {skill2}, and {skill3}.",
    "Developed and maintained a CI/CD pipeline with {skill1} and {skill2}."
]

# Templates for generating negative examples (no skills)
NEGATIVE_TEMPLATES = [
    "I will manage to complete the project by the deadline.",
    "The team's communication was excellent during the daily stand-ups.",
    "This new software will streamline our workflow and improve efficiency.",
    "We need to analyze the market trends before making a decision.",
    "My primary responsibility was the management of the project timeline."
]


def create_contextual_example(skills_list):
    """
    Generates a training example with skills embedded in a contextual sentence.
    """
    if len(skills_list) < 3:
        return None, None

    selected_skills = random.sample(skills_list, 3)
    skill1, skill2, skill3 = selected_skills[0], selected_skills[1], selected_skills[2]

    template = random.choice(CONTEXTUAL_TEMPLATES)
    text = template.format(skill1=skill1, skill2=skill2, skill3=skill3)

    entities = []
    # Use selected_skills to find the entities in the final text
    for skill in selected_skills:
        start_index = text.find(skill)
        if start_index != -1:
            end_index = start_index + len(skill)
            # Use the new, more specific "TECHNOLOGY" label
            entities.append((start_index, end_index, "TECHNOLOGY"))

    return text, {"entities": entities}


def create_negative_example():
    """
    Generates a negative training example with no labeled entities.
    """
    text = random.choice(NEGATIVE_TEMPLATES)
    return text, {"entities": []}


def main():
    """Main function to generate and save the new training data."""
    print(" Generating new contextual and negative training data...")

    # A more comprehensive list of skills for better variety
    all_skills = [
        "Python", "JavaScript", "React", "AWS", "Docker", "Kubernetes",
        "machine learning", "SQL", "Node.js", "Java", "C#", "Go", "TypeScript",
        "Vue.js", "Angular", "Terraform", "PostgreSQL", "MongoDB"
    ]

    new_training_data = []

    # Generate 200 contextual examples
    for _ in range(200):
        text, annotations = create_contextual_example(all_skills)
        if text and annotations and annotations["entities"]:
            new_training_data.append((text, annotations))

    # Generate 100 negative examples
    for _ in range(100):
        text, annotations = create_negative_example()
        new_training_data.append((text, annotations))

    # Define the output path to save the file in the parent 'spacy-ner' directory
    output_file = "../train_data_contextual.json"

    # Save the new data to the file
    with open(output_file, "w") as f:
        json.dump(new_training_data, f, indent=4)

    print(f"\n Generated {len(new_training_data)} new training examples.")
    print(f"   Saved to: {output_file}")

    print("\nSample Contextual Example:")
    print(new_training_data[0])
    print("\nSample Negative Example:")
    print(new_training_data[-1])


if __name__ == "__main__":
    main()