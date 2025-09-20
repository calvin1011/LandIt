import random
import json
from typing import List, Tuple


def augment_resume_data(existing_data: List) -> List:
    augmented = existing_data.copy()

    # Template-based augmentation
    templates = [
        ("{name} {email} {phone}", ["NAME", "EMAIL", "PHONE"]),
        ("{title} at {company} with {skills}", ["TITLE", "COMPANY", "SKILL"]),
        ("{degree} in {field} from {school} {year}", ["DEGREE", "FIELD", "SCHOOL", "DATE"])
    ]

    # Sample values for each entity type
    samples = {
        "name": ["John Smith", "Jane Doe", "Robert Johnson", "Maria Garcia"],
        "email": ["john@email.com", "jane.doe@company.com", "rj@domain.org"],
        "phone": ["(555) 123-4567", "555-987-6543", "+1-555-789-0123"],
        "title": ["Software Engineer", "Data Scientist", "Product Manager"],
        "company": ["Google", "Microsoft", "Amazon", "Tesla"],
        "skills": ["Python Java React", "AWS Docker Kubernetes", "Machine Learning AI"],
        "degree": ["Bachelor of Science", "Master of Science", "PhD"],
        "field": ["Computer Science", "Data Science", "Electrical Engineering"],
        "school": ["MIT", "Stanford", "Harvard", "UC Berkeley"],
        "year": ["2020", "2023", "2019"]
    }

    for template, labels in templates:
        for _ in range(20):  # Generate 20 examples per template
            text = template
            entities = []
            current_pos = 0

            for placeholder in ["{name}", "{email}", "{phone}", "{title}", "{company}",
                                "{skills}", "{degree}", "{field}", "{school}", "{year}"]:
                if placeholder in text:
                    sample = random.choice(samples[placeholder[1:-1]])
                    text = text.replace(placeholder, sample, 1)
                    end_pos = current_pos + len(sample)
                    entities.append((current_pos, end_pos, placeholder[1:-1].upper()))
                    current_pos = end_pos + 1  # +1 for space

            augmented.append([text, {"entities": entities}])

    return augmented


# Usage
with open("train_data_cleaned.json", "r") as f:
    existing_data = json.load(f)

augmented_data = augment_resume_data(existing_data)

with open("train_data_augmented.json", "w") as f:
    json.dump(augmented_data, f, indent=2)