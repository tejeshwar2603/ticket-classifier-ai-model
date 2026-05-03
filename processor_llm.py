import json
import re
import requests
from typing import Optional


OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama2"  # or any model you have available


def _classify_fallback(log_msg: str) -> str:
    """Fallback classification using simple regex patterns."""
    log_lower = log_msg.lower()
    
    # Deprecation patterns
    if any(word in log_lower for word in ['deprecated', 'retire', 'migration', 'migrate']):
        return "Deprecation Warning"
    
    # Workflow error patterns
    if any(word in log_lower for word in ['error', 'failed', 'crash', 'exception', 'escalation']):
        return "Workflow Error"
    
    return "Unclassified"


def _ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def _get_available_model() -> Optional[str]:
    """Get the first available model from Ollama."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            if models:
                return models[0]["name"]
    except Exception:
        pass
    return None


def classify_with_llm(log_msg: str) -> str:
    """
    Classify a log message using Ollama LLM.
    Falls back to simple pattern matching if Ollama is unavailable.
    
    Categories: (1) Workflow Error, (2) Deprecation Warning, or "Unclassified"
    """
    # Check if Ollama is available
    if not _ollama_available():
        return _classify_fallback(log_msg)
    
    prompt = f'''Classify the log message into one of these categories: 
    (1) Workflow Error, (2) Deprecation Warning.
    If you can't figure out a category, use "Unclassified".
    Put the category inside <category></category> tags. 
    Log message: {log_msg}'''

    try:
        # Get an available model
        model = _get_available_model() or OLLAMA_MODEL
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.5
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return _classify_fallback(log_msg)
        
        data = response.json()
        content = data.get("response", "")
        
        # Extract category from response
        match = re.search(r'<category>(.*?)</category>', content, flags=re.DOTALL)
        if match:
            category = match.group(1).strip()
            if category and category != "Unclassified":
                return category
    
    except Exception:
        pass
    
    # Fall back to pattern-based classification
    return _classify_fallback(log_msg)


if __name__ == "__main__":
    print(classify_with_llm(
        "Case escalation for ticket ID 7324 failed because the assigned support agent is no longer active."))
    print(classify_with_llm(
        "The 'ReportGenerator' module will be retired in version 4.0. Please migrate to the 'AdvancedAnalyticsSuite' by Dec 2025"))
    print(classify_with_llm("System reboot initiated by user 12345."))