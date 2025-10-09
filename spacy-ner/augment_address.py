import json
import random
from faker import Faker

def generate_address_data(num_examples=200):
    """
    Generates synthetic training data for addresses using the Faker library.
    """
    print(" Generating synthetic address data...")

    # Initialize Faker to generate realistic fake data
    fake = Faker()
    training_data = []

    for _ in range(num_examples):
        # Generate different components of an address
        street_address = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        zipcode = fake.zipcode()

        # Create a few different formats for variety
        formats = [
            f"{street_address}, {city}, {state} {zipcode}",
            f"{street_address}, {city}, {state}",
            f"{city}, {state} {zipcode}",
            f"{city}, {state}"
        ]

        # Choose a random format
        address_text = random.choice(formats)

        # The entire text is the location entity
        text = address_text
        start_index = 0
        end_index = len(text)

        # Create the spaCy training example format
        entities = [(start_index, end_index, "LOCATION")]
        training_data.append((text, {"entities": entities}))

    print(f" Generated {len(training_data)} address examples.")
    return training_data


def main():
    """Main function to generate and save the new training data."""
    address_data = generate_address_data(num_examples=300)

    # Define the output path to save the file in the parent 'spacy-ner' directory
    output_file = "train_data_address.json"

    # Save the new data to the file
    with open(output_file, "w") as f:
        json.dump(address_data, f, indent=4)

    print(f"   Saved to: {output_file}")

    print("\nSample Address Example:")
    print(address_data[0])


if __name__ == "__main__":
    main()