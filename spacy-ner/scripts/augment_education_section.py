import json
import random

def generate_education_data(num_examples=100):
    schools = ["MIT", "Stanford University", "State University", "Community College"]
    degrees = ["Bachelor of Science", "Master of Arts", "PhD", "Associate Degree"]
    fields = ["Computer Science", "Engineering", "Liberal Arts", "Business Administration"]

    templates = [
        "Graduated from {school} with a {degree} in {field}.",
        "Earned a {degree} in {field} at {school}.",
        "Education: {school}, {degree} in {field}.",
        "Holds a {degree} from {school} with a major in {field}."
    ]

    augmented_data = []
    for _ in range(num_examples):
        template = random.choice(templates)
        school = random.choice(schools)
        degree = random.choice(degrees)
        field = random.choice(fields)

        text = template.format(school=school, degree=degree, field=field)

        entities = [(text.find(school), text.find(school) + len(school), "SCHOOL"),
                    (text.find(degree), text.find(degree) + len(degree), "DEGREE"),
                    (text.find(field), text.find(field) + len(field), "FIELD")]

        # Filter out overlapping entities before adding
        validated_entities = []
        for ent1 in entities:
            is_overlapping = False
            for ent2 in entities:
                if ent1 != ent2 and ent1[0] <= ent2[1] and ent1[1] >= ent2[0]:
                    is_overlapping = True
                    break
            if not is_overlapping:
                validated_entities.append(ent1)

        augmented_data.append([text, {"entities": entities}])

    with open("../train_data_education_complex.json", "w") as f:
        json.dump(augmented_data, f, indent=2)
    print(f"Generated {len(augmented_data)} complex education examples.")

if __name__ == "__main__":
    generate_education_data()