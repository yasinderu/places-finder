from pydantic import BaseModel
from typing import List, Optional

class PlacePayload(BaseModel):
    """Represents the payload for finding places."""
    query: str
    user_location: Optional[str] = None

class PromptRequest(BaseModel):
    """Represents the request for ollama."""
    prompt: str

class ResponseLLM(BaseModel):
    model: Optional[str]
    response: str