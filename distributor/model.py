from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Task:
    id: str
    user_tier: str  # "paid" or "free"
    est_processing_time: int  # seconds
    data: str
    enqueued_at: datetime
    retry_count: int = 0
    assigned_agent: Optional[str] = None
    
    def is_retry(self) -> bool:
        return self.retry_count > 0
    
    def increment_retry(self):
        self.retry_count += 1
    
    def __str__(self):
        retry_info = f" (retry {self.retry_count})" if self.is_retry() else ""
        return f"TaskDetails: (ID: {self.id}, Tier: {self.user_tier}, Processing Time: {self.est_processing_time}{retry_info})"