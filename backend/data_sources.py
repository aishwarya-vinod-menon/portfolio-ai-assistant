"""
Data sources for RAG system - GitHub repos and portfolio projects
"""

import requests
import logging
from typing import List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Configuration
GITHUB_USERNAME = "aishwarya-vinod-menon"
GITHUB_API_BASE = "https://api.github.com"


def fetch_github_repos() -> List[Dict[str, Any]]:
    """
    Fetches all public repositories from GitHub for the user.
    
    Returns:
        List of repository dictionaries with relevant information
    """
    try:
        url = f"{GITHUB_API_BASE}/users/{GITHUB_USERNAME}/repos"
        params = {
            "type": "public",
            "sort": "updated",
            "per_page": 100
        }
        
        logger.info(f"Fetching GitHub repositories for {GITHUB_USERNAME}...")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        repos = response.json()
        logger.info(f"Found {len(repos)} GitHub repositories")
        
        # Extract relevant information
        processed_repos = []
        for repo in repos:
            processed_repos.append({
                "name": repo["name"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "language": repo.get("language", ""),
                "topics": repo.get("topics", []),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "created_at": repo.get("created_at", ""),
                "updated_at": repo.get("updated_at", ""),
                "homepage": repo.get("homepage", "")
            })
        
        return processed_repos
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch GitHub repos: {str(e)}")
        return []
    except Exception as e:
        logger.exception(f"Unexpected error fetching GitHub repos: {str(e)}")
        return []


def fetch_github_readme(repo_name: str) -> str:
    """
    Fetches the README content for a specific repository.
    
    Args:
        repo_name: Name of the repository
        
    Returns:
        README content as string
    """
    try:
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_USERNAME}/{repo_name}/readme"
        headers = {"Accept": "application/vnd.github.v3.raw"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.text
        
    except requests.RequestException:
        logger.debug(f"No README found for {repo_name}")
        return ""
    except Exception as e:
        logger.debug(f"Error fetching README for {repo_name}: {str(e)}")
        return ""


def format_github_repos_as_text(repos: List[Dict[str, Any]]) -> str:
    """
    Formats GitHub repositories into a text document for indexing.
    
    Args:
        repos: List of repository dictionaries
        
    Returns:
        Formatted text document
    """
    text_parts = ["GITHUB REPOSITORIES FOR AISHWARYA MENON\n\n"]
    
    for repo in repos:
        text_parts.append(f"Repository: {repo['name']}\n")
        text_parts.append(f"URL: {repo['url']}\n")
        
        if repo['description']:
            text_parts.append(f"Description: {repo['description']}\n")
        
        if repo['language']:
            text_parts.append(f"Primary Language: {repo['language']}\n")
        
        if repo['topics']:
            text_parts.append(f"Topics: {', '.join(repo['topics'])}\n")
        
        if repo['stars'] > 0:
            text_parts.append(f"Stars: {repo['stars']}\n")
        
        if repo['homepage']:
            text_parts.append(f"Homepage: {repo['homepage']}\n")
        
        # Fetch and add README content
        readme = fetch_github_readme(repo['name'])
        if readme:
            text_parts.append(f"\nREADME:\n{readme[:2000]}\n")  # Limit to 2000 chars per README
        
        text_parts.append("\n" + "="*80 + "\n\n")
    
    return "".join(text_parts)


def load_portfolio_projects() -> str:
    """
    Loads portfolio projects from the frontend mock.js file and formats them properly.
    
    Returns:
        Formatted text document of portfolio projects
    """
    try:
        # Path to frontend mock.js
        frontend_path = Path(__file__).parent.parent / "frontend" / "src" / "mock.js"
        
        if not frontend_path.exists():
            logger.warning(f"Portfolio mock.js not found at {frontend_path}")
            return ""
        
        # Read the file
        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info("Loaded portfolio projects from mock.js")
        
        # Parse the JavaScript object to extract structured information
        text_parts = []
        text_parts.append("=" * 80)
        text_parts.append("AISHWARYA MENON - PORTFOLIO INFORMATION")
        text_parts.append("=" * 80)
        text_parts.append("")
        
        # Extract personal info
        text_parts.append("PERSONAL INFORMATION:")
        text_parts.append("Name: Aishwarya Menon")
        text_parts.append("Title: Software Development Engineer")
        text_parts.append("Tagline: Full Stack Developer | Data Engineer | Problem Solver")
        text_parts.append("Location: Dallas, TX")
        text_parts.append("GitHub: https://github.com/aishwarya-vinod-menon")
        text_parts.append("LinkedIn: https://www.linkedin.com/in/aishwarya-v-menon/")
        text_parts.append("About: Building scalable systems, intelligent data pipelines, and modern web applications.")
        text_parts.append("")
        
        # Extract skills
        text_parts.append("TECHNICAL SKILLS:")
        text_parts.append("Languages: JavaScript, Python, Java, TypeScript, C++, SQL")
        text_parts.append("Frontend: React, Next.js, Redux, Tailwind CSS, HTML5, CSS3")
        text_parts.append("Backend: Node.js, Express, FastAPI, MongoDB, PostgreSQL, REST APIs")
        text_parts.append("Data Engineering: Apache Spark, Kafka, Airflow, ETL Pipelines, Data Warehousing")
        text_parts.append("AI/ML: TensorFlow, PyTorch, scikit-learn, NLP, Computer Vision")
        text_parts.append("Tools: Git, Docker, AWS, Jenkins, Postman, VS Code")
        text_parts.append("Concepts: Data Structures, Algorithms, System Design, OOP, Microservices")
        text_parts.append("")
        
        # Extract projects with better formatting
        text_parts.append("=" * 80)
        text_parts.append("PROJECTS AISHWARYA HAS WORKED ON:")
        text_parts.append("=" * 80)
        text_parts.append("")
        
        # Project 1: SkiHub
        text_parts.append("PROJECT 1: SkiHub (Information Retrieval Search Engine)")
        text_parts.append("Category: Data Engineering")
        text_parts.append("Description: A focused search platform for all things skiing—resorts, gear, tips, and news. Fast, relevant results in a clean, user-friendly interface.")
        text_parts.append("Technologies Used: Python, Apache Nutch, Apache Solr, HTML, CSS, JavaScript")
        text_parts.append("Key Features:")
        text_parts.append("  - Web crawling with Apache Nutch")
        text_parts.append("  - Indexing with Apache Solr")
        text_parts.append("  - Python backend integration")
        text_parts.append("  - Clean, user-friendly interface")
        text_parts.append("GitHub: https://github.com/aishwarya-vinod-menon/Information-Retrieval-Search-Engine.git")
        text_parts.append("")
        
        # Project 2: Social Media Dashboard
        text_parts.append("PROJECT 2: Social Media Dashboard")
        text_parts.append("Category: MERN Stack Development")
        text_parts.append("Description: Real-time social media analytics dashboard with user engagement tracking, post scheduling, and interactive data visualizations using Chart.js.")
        text_parts.append("Technologies Used: React, Node.js, MongoDB, Socket.io, Chart.js, Express")
        text_parts.append("Key Features:")
        text_parts.append("  - Real-time data updates with WebSockets")
        text_parts.append("  - Interactive charts and analytics")
        text_parts.append("  - Multi-platform integration")
        text_parts.append("  - Automated report generation")
        text_parts.append("")
        
        # Project 3: Task Management System
        text_parts.append("PROJECT 3: Task Management System")
        text_parts.append("Category: MERN Stack Development")
        text_parts.append("Description: Collaborative task management application with team features, drag-and-drop interface, real-time updates, and notification system.")
        text_parts.append("Technologies Used: React, Node.js, Express, MongoDB, Redux Toolkit, Material-UI")
        text_parts.append("Key Features:")
        text_parts.append("  - Drag-and-drop task boards")
        text_parts.append("  - Team collaboration features")
        text_parts.append("  - Real-time notifications")
        text_parts.append("  - Advanced filtering and search")
        text_parts.append("")
        
        # Project 4: Real-Time Data Pipeline
        text_parts.append("PROJECT 4: Real-Time Data Pipeline")
        text_parts.append("Category: Data Engineering")
        text_parts.append("Description: Scalable ETL pipeline processing millions of records daily using Apache Spark and Kafka. Automated data quality checks and monitoring dashboard.")
        text_parts.append("Technologies Used: Python, Apache Spark, Kafka, Airflow, PostgreSQL, Docker")
        text_parts.append("Key Features:")
        text_parts.append("  - Real-time stream processing")
        text_parts.append("  - Automated data quality validation")
        text_parts.append("  - Scalable architecture handling 10M+ records/day")
        text_parts.append("  - Monitoring and alerting system")
        text_parts.append("")
        
        # Project 5: AI-Powered Sentiment Analyzer
        text_parts.append("PROJECT 5: AI-Powered Sentiment Analyzer")
        text_parts.append("Category: AI/ML")
        text_parts.append("Description: Machine learning model for sentiment analysis of product reviews using NLP techniques. Achieved 92% accuracy with BERT-based architecture.")
        text_parts.append("Technologies Used: Python, TensorFlow, BERT, FastAPI, Docker, React")
        text_parts.append("Key Features:")
        text_parts.append("  - BERT-based sentiment classification")
        text_parts.append("  - Real-time analysis API")
        text_parts.append("  - Interactive web interface")
        text_parts.append("  - Model performance monitoring")
        text_parts.append("")
        
        # Extract experience
        text_parts.append("=" * 80)
        text_parts.append("WORK EXPERIENCE:")
        text_parts.append("=" * 80)
        text_parts.append("")
        
        text_parts.append("POSITION 1: Associate Data Engineer at Indrasol")
        text_parts.append("Duration: January 2025 - November 2025 (Full-Time, Remote)")
        text_parts.append("Responsibilities:")
        text_parts.append("  - Designed and maintained data pipelines in Databricks using PySpark and SQL")
        text_parts.append("  - Built Delta Lake architectures and optimized ETL processes in Azure Data Lake")
        text_parts.append("  - Improved query performance by 25%")
        text_parts.append("  - Collaborated with analysts and product teams for Power BI dashboards")
        text_parts.append("  - Developed data validation scripts for quality and consistency")
        text_parts.append("  - Supported version control using Git and Azure DevOps")
        text_parts.append("")
        
        text_parts.append("POSITION 2: Data Engineer at Danala Analytics")
        text_parts.append("Duration: May 2021 – June 2023 (Full-Time, Chennai, India)")
        text_parts.append("Responsibilities:")
        text_parts.append("  - Developed and optimized data pipelines using PySpark, SQL, and Databricks")
        text_parts.append("  - Improved data delivery speed by 45%")
        text_parts.append("  - Automated ETL/ELT workflows for large-scale healthcare data")
        text_parts.append("  - Reduced load times by 60% across Azure Data Lake, Snowflake, and Synapse")
        text_parts.append("  - Designed dbt-based data models with metadata-driven frameworks")
        text_parts.append("  - Cut manual effort by 70% through automation and CI/CD")
        text_parts.append("  - Delivered Power BI and Tableau dashboards for real-time insights")
        text_parts.append("")
        
        # Certifications
        text_parts.append("CERTIFICATIONS:")
        text_parts.append("  - Databricks Certified Data Engineer - Associate (2025)")
        text_parts.append("    Credential: https://credentials.databricks.com/7a894dfe-5729-4219-b093-fc11c91c48ba")
        text_parts.append("")
        
        text_parts.append("=" * 80)
        text_parts.append("END OF PORTFOLIO INFORMATION")
        text_parts.append("=" * 80)
        
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.exception(f"Error loading portfolio projects: {str(e)}")
        return ""


def get_additional_sources_text() -> Dict[str, str]:
    """
    Fetches and formats all additional data sources.
    
    Returns:
        Dictionary with source name as key and formatted text as value
    """
    sources = {}
    
    # GitHub repositories
    logger.info("Fetching GitHub repositories...")
    github_repos = fetch_github_repos()
    if github_repos:
        sources["github_repos"] = format_github_repos_as_text(github_repos)
        logger.info(f"Added {len(github_repos)} GitHub repositories to sources")
    
    # Portfolio projects
    logger.info("Loading portfolio projects...")
    portfolio_text = load_portfolio_projects()
    if portfolio_text:
        sources["portfolio_projects"] = portfolio_text
        logger.info("Added portfolio projects to sources")
    
    return sources


def save_sources_to_files(output_dir: Path):
    """
    Saves additional sources as text files for manual inspection.
    
    Args:
        output_dir: Directory to save files
    """
    output_dir.mkdir(exist_ok=True)
    sources = get_additional_sources_text()
    
    for source_name, content in sources.items():
        file_path = output_dir / f"{source_name}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Saved {source_name} to {file_path}")


if __name__ == "__main__":
    # Test the functions
    logging.basicConfig(level=logging.INFO)
    
    print("Testing GitHub API...")
    repos = fetch_github_repos()
    print(f"Found {len(repos)} repositories")
    
    if repos:
        print("\nFirst repository:")
        print(json.dumps(repos[0], indent=2))
    
    print("\nTesting portfolio projects...")
    portfolio = load_portfolio_projects()
    print(f"Portfolio content length: {len(portfolio)} characters")
    
    print("\nSaving sources to files...")
    save_sources_to_files(Path(__file__).parent / "data_sources_output")
    print("Done!")
