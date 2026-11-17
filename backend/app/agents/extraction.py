import re
from typing import Any, Dict, List, Optional
from app.agents.base import BaseAgent

EXPANDED_SKILL_KEYWORDS = [
    # Languages
    "python", "javascript", "typescript", "java", "golang", "go", "rust", "c++", "c#", "c", "ruby", "php", "sql", "html", "css", "scala", "r",
    # Machine Learning, Deep Learning & AI
    "machine learning", "deep learning", "artificial intelligence", "data science", "nlp", "natural language processing",
    "computer vision", "generative ai", "llm", "large language models", "prompt engineering",
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "opencv", "easyocr", "ocr", "huggingface", "transformers",
    "bert", "resnet", "u-net", "cnn", "rnn", "lstm", "xgboost", "lightgbm", "spacy", "nltk",
    "langchain", "langgraph", "llama-index", "llamaindex", "openai", "gemini", "claude", "rag",
    # Data & Analytics
    "pandas", "numpy", "matplotlib", "seaborn", "scipy", "spark", "pyspark", "hadoop", "kafka", "airflow",
    # Backend Frameworks
    "fastapi", "flask", "django", "nodejs", "express", "spring", "spring boot", "nestjs", "graphql", "rest api", "grpc", ".net", "asp.net",
    # Frontend Frameworks
    "react", "reactjs", "nextjs", "next.js", "vue", "vuejs", "angular", "tailwind", "redux",
    # Databases & Storage
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "dynamodb", "cassandra", "vector database", "pgvector", "pinecone", "chromadb", "qdrant",
    # Cloud, DevOps & Tools
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "google cloud", "linux", "git", "github", "gitlab", "ci/cd", "terraform", "ansible",
    # Architecture & Algorithms
    "microservices", "system design", "data structures", "algorithms", "oop", "trie", "bloom filter", "caching",
]

def clean_html(raw_html: str) -> str:
    """Clean raw HTML description into clean readable plain text."""
    if not raw_html:
        return ""
    # Replace breaks and list items with newlines
    text = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</?(li|p|div|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Unescape common HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    # Collapse multiple whitespaces
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def extract_skills_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    found = set()
    for skill in EXPANDED_SKILL_KEYWORDS:
        # Use boundary matching for short words, substring for phrases
        if len(skill) <= 4:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.add(skill)
        else:
            if skill in text_lower:
                found.add(skill)
    return sorted(list(found))

def detect_location_type(location: str) -> str:
    loc = (location or "").lower()
    if "remote" in loc:
        return "remote"
    if "hybrid" in loc:
        return "hybrid"
    return "onsite"

def extract_experience(text: str) -> Optional[int]:
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\s*-\s*\d+\s*years?',
        r'experience\s*of\s*(\d+)\+?\s*years?',
        r'minimum\s*(\d+)\s*years?',
    ]
    text_lower = text.lower()
    if re.search(r'fresher|0-1 year|0 to 1 year|entry.level|graduate|intern|trainee|college', text_lower):
        return 0
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            return int(m.group(1))
    return None

class ExtractionAgent(BaseAgent):
    name = "extraction_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        raw_job = input_data["raw_job"]
        raw_description = raw_job.get("description", "") or ""
        clean_description = clean_html(raw_description)
        title = raw_job.get("title", "")
        location = raw_job.get("location", "")

        combined_text = f"{title}\n{clean_description}"
        required_skills = extract_skills_from_text(combined_text)
        exp_min = extract_experience(combined_text)
        location_type = detect_location_type(location)

        return {
            "title": title,
            "description": clean_description,
            "location": location,
            "location_type": location_type,
            "source": raw_job.get("source", ""),
            "source_id": str(raw_job.get("source_id", "")),
            "application_url": raw_job.get("application_url", ""),
            "department": raw_job.get("department", ""),
            "posted_at": raw_job.get("posted_at"),
            "required_skills": required_skills,
            "experience_min": exp_min,
            "raw_payload": raw_job,
        }

extraction_agent = ExtractionAgent()
