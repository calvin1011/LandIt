
import random
import json
from typing import List


def augment_company_data() -> List:
    """Generate training data focused on company/organization names"""
    augmented_data = []

    # Templates for company mentions in resumes
    templates = [
        # Standard work experience formats
        ("{title} at {company}", ["TITLE", "COMPANY"]),
        ("{title}, {company}", ["TITLE", "COMPANY"]),
        ("{company} - {title}", ["COMPANY", "TITLE"]),
        ("Worked at {company} as {title}", ["COMPANY", "TITLE"]),
        ("{title} | {company}", ["TITLE", "COMPANY"]),

        # Experience sections
        ("Experience:\n{company} - {title} ({duration})", ["COMPANY", "TITLE", "DATE"]),
        ("{company}\n{title}\n{duration}", ["COMPANY", "TITLE", "DATE"]),
        ("• {title} at {company}, {duration}", ["TITLE", "COMPANY", "DATE"]),

        # Professional summary
        ("Professional with experience at {company} and {company2}", ["COMPANY", "COMPANY"]),
        ("Previously at {company}, {company2}, and {company3}", ["COMPANY", "COMPANY", "COMPANY"]),

        # Current position
        ("Currently: {title} at {company}", ["TITLE", "COMPANY"]),
        ("Present: {company} - {title}", ["COMPANY", "TITLE"]),

        # Multiple companies
        ("Companies: {company}, {company2}, {company3}", ["COMPANY", "COMPANY", "COMPANY"]),
        ("Work history includes {company} and {company2}", ["COMPANY", "COMPANY"]),

        # With locations
        ("{company} ({location}) - {title}", ["COMPANY", "LOCATION", "TITLE"]),
        ("{title} at {company}, {location}", ["TITLE", "COMPANY", "LOCATION"]),

        # Realistic resume formats
        ("PROFESSIONAL EXPERIENCE\n{company}\n{title} | {duration}", ["COMPANY", "TITLE", "DATE"]),
        ("WORK HISTORY\n• {title} - {company} ({duration})", ["TITLE", "COMPANY", "DATE"]),
        ("EMPLOYMENT\n{company}: {title} ({start_date}-{end_date})", ["COMPANY", "TITLE", "DATE"])
    ]

    # Extensive database of real companies across industries
    samples = {
        "company": [
            # Tech Giants
            "Google", "Microsoft", "Apple", "Amazon", "Meta", "Netflix", "Twitter", "LinkedIn",
            "Adobe", "Salesforce", "Oracle", "IBM", "Intel", "Cisco", "HP", "Dell",
            "Uber", "Lyft", "Airbnb", "DoorDash", "Slack", "Zoom", "Spotify", "Pinterest",

            # Finance & Banking
            "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Bank of America", "Wells Fargo",
            "Citigroup", "American Express", "Visa", "Mastercard", "PayPal", "Stripe", "Square",
            "BlackRock", "Fidelity Investments", "Charles Schwab", "Bloomberg",

            # Consulting & Professional Services
            "McKinsey & Company", "Boston Consulting Group", "Bain & Company", "Deloitte",
            "PricewaterhouseCoopers", "EY", "KPMG", "Accenture", "Capgemini", "Booz Allen Hamilton",

            # Healthcare & Pharma
            "Johnson & Johnson", "Pfizer", "Merck", "Novartis", "Roche", "GlaxoSmithKline",
            "UnitedHealth Group", "Anthem", "Cigna", "CVS Health", "Walgreens",

            # Retail & Consumer Goods
            "Walmart", "Target", "Costco", "Home Depot", "Lowe's", "Best Buy", "Starbucks",
            "Nike", "Adidas", "Procter & Gamble", "Unilever", "Coca-Cola", "PepsiCo",

            # Startups & Scale-ups
            "Robinhood", "Coinbase", "Snowflake", "Databricks", "MongoDB", "Elastic",
            "Asana", "Notion", "Figma", "Canva", "Dropbox", "Box", "Twilio", "SendGrid",

            # Automotive & Manufacturing
            "Tesla", "Ford", "General Motors", "Toyota", "Honda", "BMW", "Mercedes-Benz",
            "Boeing", "Lockheed Martin", "Raytheon", "General Electric", "Siemens",

            # Media & Entertainment
            "Disney", "Warner Bros", "Universal Studios", "Sony Pictures", "Paramount",
            "Comcast", "AT&T", "Verizon", "T-Mobile", "Netflix", "Hulu", "Disney+"
        ],

        "company2": [
            "Facebook", "Amazon Web Services", "Google Cloud", "Microsoft Azure",
            "Apple Inc.", "Tesla Motors", "SpaceX", "Blue Origin", "NASA",
            "Stanford University", "MIT", "Harvard University", "Yale University",
            "Berkeley", "UCLA", "University of Michigan", "Carnegie Mellon",
            "General Dynamics", "Northrop Grumman", "Boeing Defense", "Raytheon Technologies",
            "NVIDIA", "AMD", "Qualcomm", "Broadcom", "Texas Instruments"
        ],

        "company3": [
            "StartupX", "TechInnovate", "DataDriven Inc", "CloudSolutions", "AI Ventures",
            "Digital Transformers", "FutureTech Labs", "Innovation Partners", "Growth Hackers",
            "ScaleUp Co", "Disruptive Tech", "NextGen Solutions", "SmartSystems"
        ],

        "title": [
            "Software Engineer", "Senior Software Engineer", "Lead Developer", "Principal Engineer",
            "Data Scientist", "Machine Learning Engineer", "AI Researcher", "Data Analyst",
            "Product Manager", "Senior Product Manager", "Product Director", "VP of Product",
            "UX Designer", "UI Designer", "Product Designer", "Design Director",
            "DevOps Engineer", "Site Reliability Engineer", "Cloud Architect", "Systems Administrator",
            "Project Manager", "Program Manager", "Technical Program Manager", "Scrum Master",
            "Business Analyst", "Data Engineer", "Backend Developer", "Frontend Developer",
            "Full Stack Developer", "Mobile Developer", "iOS Developer", "Android Developer",
            "CTO", "VP of Engineering", "Engineering Manager", "Director of Engineering"
        ],

        "duration": [
            "2020-2023", "2018-2022", "2019-Present", "2016-2020", "2021-Present",
            "2 years", "3 years", "1 year 8 months", "4 years 3 months",
            "Jan 2020 - Dec 2022", "Mar 2019 - Present", "Jun 2018 - May 2021"
        ],

        "start_date": ["Jan 2020", "Mar 2019", "Jun 2018", "Sep 2021", "Jan 2022"],
        "end_date": ["Dec 2022", "Present", "May 2021", "Aug 2023", "Dec 2023"],

        "location": [
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA",
            "Chicago, IL", "Los Angeles, CA", "Denver, CO", "Portland, OR", "Atlanta, GA",
            "Remote", "Hybrid", "Mountain View, CA", "Cupertino, CA", "Redmond, WA"
        ]
    }

    print("🏢 Generating company-focused training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(40):  # Generate 40 examples per template
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
                if placeholder.startswith('company'):
                    label_type = "COMPANY"
                elif placeholder == 'title':
                    label_type = "TITLE"
                elif placeholder in ['duration', 'start_date', 'end_date']:
                    label_type = "DATE"
                elif placeholder == 'location':
                    label_type = "LOCATION"
                else:
                    label_type = placeholder.upper()

                entities.append([start_pos, end_pos, label_type])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data, samples  # Return samples for statistics


def main():
    """Main function to generate and save company training data"""
    print("🚀 Generating Company & Organization Training Data")
    print("=" * 60)
    print("Covering: Tech Giants, Finance, Consulting, Healthcare, Startups, and more!")
    print("=" * 60)

    # Generate company-focused data
    company_data, samples = augment_company_data()  # Get both data and samples

    # Save to file
    output_file = "train_data_companies.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(company_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {len(company_data)} company-focused examples")
    print(f"💾 Saved to {output_file}")

    # Show sample statistics
    print(f"\n📊 Covering {len(samples['company'])}+ real companies across industries:")
    industries = [
        "Tech Giants", "Finance & Banking", "Consulting", "Healthcare",
        "Retail", "Startups", "Automotive", "Media & Entertainment"
    ]

    for industry in industries:
        print(f"   • {industry}")

    print(f"\n🎯 Next steps:")
    print("   1. Run 'python train.py' to train with this additional data")
    print("   2. Create similar scripts for SCHOOL and DEGREE labels")
    print("   3. Your model will better distinguish companies from other entities")
    print("   4. Expect improved COMPANY label recognition in test results")


if __name__ == "__main__":
    main()