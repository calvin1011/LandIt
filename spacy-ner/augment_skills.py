
import random
import json
from typing import List

def augment_skills_data() -> List:
    """Generate training data focused on comprehensive tech skills"""
    augmented_data = []

    # Templates for skills sections
    templates = [
        # Standard skills formats
        ("Skills: {skills}", ["SKILL"]),
        ("Technical Skills: {skills}", ["SKILL"]),
        ("Technologies: {skills}", ["SKILL"]),
        ("Proficient in: {skills}", ["SKILL"]),
        ("Expertise: {skills}", ["SKILL"]),
        ("Core Competencies: {skills}", ["SKILL"]),

        # Categorized skills
        ("Programming: {programming} | Frameworks: {frameworks} | Tools: {tools}", ["SKILL", "SKILL", "SKILL"]),
        ("Languages: {programming} | Cloud: {cloud} | Databases: {databases}", ["SKILL", "SKILL", "SKILL"]),
        ("Frontend: {frontend} | Backend: {backend} | DevOps: {devops}", ["SKILL", "SKILL", "SKILL"]),

        # Detailed sections
        ("SKILLS\nProgramming Languages: {programming}\nFrameworks: {frameworks}\nCloud Platforms: {cloud}",
         ["SKILL", "SKILL", "SKILL"]),
        ("TECHNICAL EXPERTISE\n{skills}", ["SKILL"]),
        ("TECHNOLOGIES & TOOLS\n{skills}", ["SKILL"]),

        # Bullet point formats
        ("• {skills}", ["SKILL"]),
        ("- {skills}", ["SKILL"]),
        ("* {skills}", ["SKILL"]),

        # With proficiency levels
        ("{skills} (Advanced)", ["SKILL"]),
        ("{skills} (Intermediate)", ["SKILL"]),
        ("{skills} (Proficient)", ["SKILL"]),
        ("{skills} (Expert)", ["SKILL"]),

        # Realistic resume formats
        ("SKILLS SUMMARY\n{skills}", ["SKILL"]),
        ("TECHNICAL PROFICIENCIES\n{skills}", ["SKILL"]),
        ("TECHNICAL SKILLS\n{skills}", ["SKILL"])
    ]

    # Comprehensive tech skills database
    samples = {
        "programming": [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
            "Swift", "Kotlin", "Ruby", "PHP", "Scala", "R", "MATLAB", "SQL", "NoSQL",
            "HTML", "CSS", "Sass", "Less", "Shell", "Bash", "PowerShell", "Perl"
        ],
        "frameworks": [
            "React", "Angular", "Vue.js", "Node.js", "Express.js", "Django", "Flask",
            "Spring Boot", "Ruby on Rails", "Laravel", "ASP.NET", "TensorFlow", "PyTorch",
            "Keras", "React Native", "Flutter", "Vue", "Svelte", "Next.js", "Nuxt.js",
            "FastAPI", "GraphQL", "Apache Spark", "Hadoop", "Kafka"
        ],
        "cloud": [
            "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform",
            "Ansible", "Jenkins", "GitLab CI", "GitHub Actions", "CloudFormation",
            "EC2", "S3", "Lambda", "RDS", "DynamoDB", "CloudFront", "Route53",
            "Azure DevOps", "Google Kubernetes Engine", "OpenStack", "Heroku",
            "DigitalOcean", "Vercel", "Netlify", "Firebase"
        ],
        "databases": [
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
            "Oracle", "SQL Server", "DynamoDB", "Firestore", "BigQuery", "Snowflake",
            "Redshift", "Cosmos DB", "Neo4j", "MariaDB", "SQLite", "InfluxDB"
        ],
        "tools": [
            "Git", "GitHub", "GitLab", "JIRA", "Confluence", "Docker", "Kubernetes",
            "Jenkins", "CircleCI", "Travis CI", "Ansible", "Terraform", "Puppet",
            "Chef", "Splunk", "Datadog", "New Relic", "Prometheus", "Grafana",
            "Postman", "Swagger", "VS Code", "IntelliJ", "Eclipse", "PyCharm",
            "WebStorm", "Xcode", "Android Studio", "Figma", "Sketch", "Adobe XD"
        ],
        "devops": [
            "CI/CD", "Infrastructure as Code", "Microservices", "Containerization",
            "Orchestration", "Monitoring", "Logging", "Auto Scaling", "Load Balancing",
            "Serverless", "Cloud Native", "DevSecOps", "Site Reliability Engineering",
            "Disaster Recovery", "High Availability", "Performance Optimization"
        ],
        "cybersecurity": [
            "Network Security", "Application Security", "Cloud Security", "SOC 2",
            "GDPR", "HIPAA", "Penetration Testing", "Vulnerability Assessment",
            "SIEM", "Firewalls", "VPN", "Encryption", "Zero Trust", "OWASP",
            "NIST Framework", "ISO 27001", "Incident Response", "Threat Intelligence"
        ],
        "ai_ml": [
            "Machine Learning", "Deep Learning", "Natural Language Processing",
            "Computer Vision", "Reinforcement Learning", "Data Mining",
            "Predictive Analytics", "Neural Networks", "TensorFlow", "PyTorch",
            "Keras", "Scikit-learn", "OpenCV", "Hugging Face", "LangChain",
            "LLMs", "GPT", "BERT", "Transformers", "GANs", "Random Forest",
            "XGBoost", "Data Visualization", "Tableau", "Power BI"
        ],
        "frontend": [
            "React", "Vue", "Angular", "Svelte", "TypeScript", "JavaScript",
            "HTML5", "CSS3", "Sass", "Less", "Webpack", "Vite", "Babel",
            "Redux", "MobX", "Vuex", "Next.js", "Nuxt.js", "Gatsby",
            "Tailwind CSS", "Bootstrap", "Material-UI", "Chakra UI", "Three.js",
            "D3.js", "WebGL", "PWA", "Responsive Design", "Cross-browser Compatibility"
        ],
        "backend": [
            "Node.js", "Express", "Django", "Flask", "Spring Boot", "Ruby on Rails",
            "Laravel", "ASP.NET", "FastAPI", "GraphQL", "REST APIs", "Microservices",
            "WebSockets", "Socket.io", "gRPC", "Message Queues", "RabbitMQ",
            "Celery", "Background Jobs", "Caching", "Redis", "Memcached",
            "Authentication", "OAuth", "JWT", "API Security", "Rate Limiting"
        ],
        "skills": [
            # Combined skills for general templates
            "Python JavaScript React AWS Docker Kubernetes",
            "Java Spring Boot MySQL MongoDB Microservices",
            "React Node.js Express MongoDB Full Stack Development",
            "AWS Lambda DynamoDB Serverless Architecture",
            "TensorFlow PyTorch Machine Learning Deep Learning",
            "Kubernetes Helm Terraform GitLab CI DevOps",
            "TypeScript Angular RxJS NgRx Frontend Development",
            "Python Django PostgreSQL Redis Celery",
            "Go Gin Docker Kubernetes Cloud Native",
            "React Native Flutter iOS Android Mobile Development",
            "Cybersecurity Network Security Penetration Testing",
            "Data Engineering ETL Pipelines Apache Spark Hadoop",
            "Cloud Architecture AWS Solutions Architect",
            "UI/UX Design Figma Adobe XD Prototyping",
            "Agile Scrum Kanban Project Management"
        ]
    }

    print(" Generating comprehensive tech skills training data...")

    # Generate examples from templates
    for template, labels in templates:
        for _ in range(30):  # Generate 30 examples per template
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
                entities.append([start_pos, end_pos, "SKILL"])
                current_pos = end_pos + 1

            augmented_data.append([text, {"entities": entities}])

    return augmented_data


def main():
    """Main function to generate and save skills training data"""
    print(" Generating Comprehensive Tech Skills Training Data")
    print("=" * 60)
    print("Covering: Full Stack, Cloud, DevOps, Cybersecurity, AI/ML, and more!")
    print("=" * 60)

    # Generate skills-focused data
    skills_data = augment_skills_data()

    # Save to file
    output_file = "train_data_skills.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(skills_data, f, indent=2, ensure_ascii=False)

    print(f" Generated {len(skills_data)} skills-focused examples")
    print(f" Saved to {output_file}")

    # Define samples here for the summary (same as inside augment_skills_data)
    samples = {
        "programming": ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Swift", "Kotlin",
                        "Ruby", "PHP", "Scala", "R", "MATLAB", "SQL", "NoSQL", "HTML", "CSS", "Sass", "Less", "Shell",
                        "Bash", "PowerShell", "Perl"],
        "frameworks": ["React", "Angular", "Vue.js", "Node.js", "Express.js", "Django", "Flask", "Spring Boot",
                       "Ruby on Rails", "Laravel", "ASP.NET", "TensorFlow", "PyTorch", "Keras", "React Native",
                       "Flutter", "Vue", "Svelte", "Next.js", "Nuxt.js", "FastAPI", "GraphQL", "Apache Spark", "Hadoop",
                       "Kafka"],
        "cloud": ["AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
                  "GitLab CI", "GitHub Actions", "CloudFormation", "EC2", "S3", "Lambda", "RDS", "DynamoDB",
                  "CloudFront", "Route53", "Azure DevOps", "Google Kubernetes Engine", "OpenStack", "Heroku",
                  "DigitalOcean", "Vercel", "Netlify", "Firebase"],
        "databases": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "Oracle", "SQL Server",
                      "DynamoDB", "Firestore", "BigQuery", "Snowflake", "Redshift", "Cosmos DB", "Neo4j", "MariaDB",
                      "SQLite", "InfluxDB"],
        "tools": ["Git", "GitHub", "GitLab", "JIRA", "Confluence", "Docker", "Kubernetes", "Jenkins", "CircleCI",
                  "Travis CI", "Ansible", "Terraform", "Puppet", "Chef", "Splunk", "Datadog", "New Relic", "Prometheus",
                  "Grafana", "Postman", "Swagger", "VS Code", "IntelliJ", "Eclipse", "PyCharm", "WebStorm", "Xcode",
                  "Android Studio", "Figma", "Sketch", "Adobe XD"],
        "devops": ["CI/CD", "Infrastructure as Code", "Microservices", "Containerization", "Orchestration",
                   "Monitoring", "Logging", "Auto Scaling", "Load Balancing", "Serverless", "Cloud Native", "DevSecOps",
                   "Site Reliability Engineering", "Disaster Recovery", "High Availability",
                   "Performance Optimization"],
        "cybersecurity": ["Network Security", "Application Security", "Cloud Security", "SOC 2", "GDPR", "HIPAA",
                          "Penetration Testing", "Vulnerability Assessment", "SIEM", "Firewalls", "VPN", "Encryption",
                          "Zero Trust", "OWASP", "NIST Framework", "ISO 27001", "Incident Response",
                          "Threat Intelligence"],
        "ai_ml": ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
                  "Reinforcement Learning", "Data Mining", "Predictive Analytics", "Neural Networks", "TensorFlow",
                  "PyTorch", "Keras", "Scikit-learn", "OpenCV", "Hugging Face", "LangChain", "LLMs", "GPT", "BERT",
                  "Transformers", "GANs", "Random Forest", "XGBoost", "Data Visualization", "Tableau", "Power BI"],
        "frontend": ["React", "Vue", "Angular", "Svelte", "TypeScript", "JavaScript", "HTML5", "CSS3", "Sass", "Less",
                     "Webpack", "Vite", "Babel", "Redux", "MobX", "Vuex", "Next.js", "Nuxt.js", "Gatsby",
                     "Tailwind CSS", "Bootstrap", "Material-UI", "Chakra UI", "Three.js", "D3.js", "WebGL", "PWA",
                     "Responsive Design", "Cross-browser Compatibility"],
        "backend": ["Node.js", "Express", "Django", "Flask", "Spring Boot", "Ruby on Rails", "Laravel", "ASP.NET",
                    "FastAPI", "GraphQL", "REST APIs", "Microservices", "WebSockets", "Socket.io", "gRPC",
                    "Message Queues", "RabbitMQ", "Celery", "Background Jobs", "Caching", "Redis", "Memcached",
                    "Authentication", "OAuth", "JWT", "API Security", "Rate Limiting"],
        "skills": ["Python JavaScript React AWS Docker Kubernetes", "Java Spring Boot MySQL MongoDB Microservices",
                   "React Node.js Express MongoDB Full Stack Development",
                   "AWS Lambda DynamoDB Serverless Architecture", "TensorFlow PyTorch Machine Learning Deep Learning",
                   "Kubernetes Helm Terraform GitLab CI DevOps", "TypeScript Angular RxJS NgRx Frontend Development",
                   "Python Django PostgreSQL Redis Celery", "Go Gin Docker Kubernetes Cloud Native",
                   "React Native Flutter iOS Android Mobile Development",
                   "Cybersecurity Network Security Penetration Testing",
                   "Data Engineering ETL Pipelines Apache Spark Hadoop", "Cloud Architecture AWS Solutions Architect",
                   "UI/UX Design Figma Adobe XD Prototyping", "Agile Scrum Kanban Project Management"]
    }

    print(f" Covered {len(samples)} different tech categories")
    print("\n Categories included:")
    for category in samples.keys():
        print(f"   • {category}: {len(samples[category])} skills")


if __name__ == "__main__":
    main()