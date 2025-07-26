from pydantic import BaseModel

class ComplaintIn(BaseModel):
    title: str
    content: str

class ClassificationOut(BaseModel):
    priority: str
    feedback: str