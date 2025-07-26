import sys
import json
import re
import asyncio
from pathlib import Path
from typing import Dict, Any
from openai import AsyncOpenAI  # <-- importing async method

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from app.config import settings

client = AsyncOpenAI(  # <-- async method 
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key
)

_government_structure = None

async def load_government_structure() -> Dict[str, Any]:
    global _government_structure
    if _government_structure is None:
        gov_file = BASE_DIR / "app" / "data" / "syrian_government_structure.json"
        try:
            content = await asyncio.to_thread(
                lambda: gov_file.read_text(encoding='utf-8')
            )
            _government_structure = json.loads(content)
        except Exception as e:
            raise RuntimeError(f"Failed to load government file :  {str(e)}")
    return _government_structure

async def get_cached_government_structure() -> Dict[str, Any]:
    if _government_structure is None:
        raise RuntimeError("government structure file not loaded yet")
    return _government_structure

async def classify_complaint(title: str, content: str) -> tuple[str, str]:  # <-- async
    """
    Calls the LLM to classify a complaint and returns (priority, feedback) in Arabic.
    Raises RuntimeError if parsing fails or LLM returns unexpected format.
    """
    government_structure = await get_cached_government_structure()  # <-- await
    
    prompt = f"""
    You are a complaint classification system for Syrian government entities.
    Government Structure (JSON):
    {json.dumps(government_structure, ensure_ascii=False)}
    
    Instructions:
    1. Analyze this complaint strictly based on the provided government structure
    2. Respond IN ARABIC using EXACT format:
    
    PRIORITY: <عاجل|مهم|متوسط|روتيني>
    FEEDBACK: <Which government agency should handle this complaint and brief guidance notes>
    Complaint Title: {title}
    Complaint Content: {content}
    """
    
    try:
        # calling API async
        resp = await client.chat.completions.create(  # <-- await هنا
            model=settings.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw = resp.choices[0].message.content.strip()
        
        # extract priority and feedback : 
        cleaned = await asyncio.to_thread(
            re.sub, r'\*+|\\n|\n|#+', ' ', raw
        )
        
        # extract data using parallel method :
        priority, feedback = await asyncio.gather(
            asyncio.to_thread(re.search, r'PRIORITY:\s*([\u0600-\u06FF]+)', cleaned),
            asyncio.to_thread(re.search, r'FEEDBACK:\s*([^\n]+)', cleaned)
        )
        
        if not priority or not feedback:
            raise ValueError("Invalid response format")
            
        # cleaning feedback : 
        feedback_text = await asyncio.to_thread(
            lambda: re.split(r'[\.\-\:]', feedback.group(1))[0].strip()
        )
        
        return priority.group(1).strip(), feedback_text
    
        
    except Exception as e:
        raise RuntimeError(f"Classification failed : {str(e)}")
    
    
    

