"""
Agent Response Types
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class AgentResponse:
    """Response from the agent."""
    
    type: Literal["message", "command", "result", "choice", "error", "done"]
    content: str = ""
    question: str = ""  # For choice type
    options: list[str] = None  # For choice type
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
