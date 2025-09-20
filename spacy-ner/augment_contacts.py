import random
import json
from typing import List


def augment_contact_data() -> List:
    """Generate training data focused on contact information"""
    augmented_data = []

    # Templates specifically for contact information
    templates = [
        # Email and phone combinations
        ("Email: {email} Phone: {phone}", ["EMAIL", "PHONE"]),
        ("Contact: {email} | {phone}", ["EMAIL", "PHONE"]),
        ("{email} {phone}", ["EMAIL", "PHONE"]),
        ("Reach me at {email} or {phone}", ["EMAIL", "PHONE"]),
        ("{email} | Tel: {phone}", ["EMAIL", "PHONE"]),

        # With names
        ("{name}: {email} {phone}", ["NAME", "EMAIL", "PHONE"]),
        ("{name} - {email} - {phone}", ["NAME", "EMAIL", "PHONE"]),
        ("Contact {name} at {email} or {phone}", ["NAME", "EMAIL", "PHONE"]),

        # With locations
        ("{email} {phone} {location}", ["EMAIL", "PHONE", "LOCATION"]),
        ("Contact: {email} | {phone} | {location}", ["EMAIL", "PHONE", "LOCATION"]),

        # Realistic resume formats
        ("{name}\n{email}\n{phone}\n{location}", ["NAME", "EMAIL", "PHONE", "LOCATION"]),
        ("CONTACT INFO\nEmail: {email}\nPhone: {phone}\nLocation: {location}", ["EMAIL", "PHONE", "LOCATION"]),

        # International formats
        ("Email: {email}\nMobile: {phone}\nBased in: {location}", ["EMAIL", "PHONE", "LOCATION"]),
        ("{email}\n{phone}\n{location}", ["EMAIL", "PHONE", "LOCATION"]),

        # Separated formats
        ("Email Address: {email}", ["EMAIL"]),
        ("Phone Number: {phone}", ["PHONE"]),
        ("Contact Email: {email}", ["EMAIL"]),
        ("Direct Line: {phone}", ["PHONE"]),
        ("Personal: {email} | Work: {work_email}", ["EMAIL", "EMAIL"]),
        ("Cell: {phone} | Office: {work_phone}", ["PHONE", "PHONE"])
    ]

    # Extensive sample values
    samples = {
        "name": [
            "John Smith", "Jane Doe", "Robert Johnson", "Maria Garcia",
            "David Kim", "Sarah Chen", "Michael Brown", "Emily Wilson",
            "James Taylor", "Jennifer Lopez", "Christopher Lee", "Amanda Rodriguez"
        ],
        "email": [
            "john.smith@email.com", "jane.doe@company.com", "rjohnson@domain.org",
            "maria.garcia@tech.com", "david.kim@ai.org", "sarah.chen@startup.io",
            "michael.b@corporation.com", "emily.wilson@consulting.com",
            "james.taylor@engineer.com", "jlopez@designstudio.com",
            "chris.lee@developers.com", "amanda.rodriguez@datascience.org",
            "contact@personal.com", "info@professional.org", "hello@career.email"
        ],
        "phone": [
            "(555) 123-4567", "555-987-6543", "+1-555-789-0123", "123-456-7890",
            "555-555-5555", "(444) 321-7654", "333-888-9999", "+1-222-333-4444",
            "1-800-123-4567", "(777) 555-1212", "888.123.4567", "999-123-4567",
            "123.456.7890", "(555) 867-5309", "654-321-0987"
        ],
        "work_phone": [
            "(555) 123-4567 ext. 123", "555-987-6543 x456", "+1-555-789-0123 ext. 789",
            "123-456-7890 office", "555-555-5555 x100", "(444) 321-7654 direct"
        ],
        "work_email": [
            "john.smith@company.com", "j.doe@corporation.com", "rj@business.org",
            "mgarcia@enterprise.com", "dkim@organization.com", "schen@firm.com"
        ],
        "location": [
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO",
            "Portland, OR", "Atlanta, GA", "Miami, FL", "Phoenix, AZ",
            "Toronto, ON", "Vancouver, BC", "London, UK", "Berlin, Germany"
        ]
    }

    print("🧪 Generating contact-focused training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(25):  # Generate 25 examples per template
            text = template
            entities = []
            current_pos = 0

            # Replace each placeholder with a sample value
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
                entities.append([start_pos, end_pos, placeholder.upper()])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data


def main():
    """Main function to generate and save contact training data"""
    print("🚀 Generating Contact Information Training Data")
    print("=" * 50)

    # Generate contact-focused data
    contact_data = augment_contact_data()

    # Save to file
    output_file = "train_data_contacts.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(contact_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(contact_data)} contact-focused examples")
    print(f"💾 Saved to {output_file}")
    print("\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this data")
    print("   2. Create other specialized augmentation scripts")
    print("   3. Modify train.py to load multiple data files")


if __name__ == "__main__":
    main()