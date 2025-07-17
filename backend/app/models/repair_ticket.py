from pydantic import BaseModel
from typing import List, Optional

class RepairTicket(BaseModel):
    ticket_id: str
    customer_location: str
    issue: str
    max_budget: float
    max_days: int
    required_capabilities: List[str]
    data_constraints: List[str]  # ["EU", "India"]
    max_hops: Optional[int] = 4
