from pydantic import BaseModel
from typing import List, Optional

class Agent(BaseModel):
    name: str
    company: Optional[str] = None
    location: str
    jurisdiction: List[str]
    capabilities: List[str]
    skills: List[str]
    cost_per_task: float
    currency: str
    access_type: str
    trust_score: float
    is_ai: bool
    wallet_address: str
    openid_token: str
    public_key: str
    public_key_pem: Optional[str]  # PEM-encoded public key string
