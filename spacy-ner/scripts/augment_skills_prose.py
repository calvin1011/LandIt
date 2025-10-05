import json
import random

def generate_skills_in_prose(num_examples=100):
    skills = ["Python", "JavaScript", "React", "AWS", "Docker", "SQL", "Java"]

    templates = [
        "Proficient in {s1} and {s2}.",
        "Experienced with a range of technologies including {s1}, {s2}, and {s3}.",
        "Developed applications using {s1} for the backend and {s2} for the frontend.",
        "My core competencies include {s1}, {s2}, and data analysis with {s3}."
    ]

    augmented_data = []
    for _ in range(num_examples):
        s1, s2, s3 = random.sample(skills, 3)
        template = random.choice(templates)
        text = template.format(s1=s1, s2=s2, s3=s3)

        entities = [(text.find(s1), text.find(s1) + len(s1), "SKILL"),
                    (text.find(s2), text.find(s2) + len(s2), "SKILL")]
        if '{s3}' in template:
            entities.append((text.find(s3), text.find(s3) + len(s3), "SKILL"))

        augmented_data.append([text, {"entities": entities}])

    with open("../train_data_skills_prose.json", "w") as f:
        json.dump(augmented_data, f, indent=2)
    print(f"Generated {len(augmented_data)} prose skills examples.")

if __name__ == "__main__":
    generate_skills_in_prose()