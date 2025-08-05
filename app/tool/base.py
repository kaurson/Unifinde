"""
Base tool classes for the University Data Collection System
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class ToolResult:
    """Result from a tool execution"""
    output: str
    error: Optional[str] = None
    base64_image: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_success(self) -> bool:
        """Check if the tool execution was successful"""
        return self.error is None


class BaseTool(ABC, BaseModel):
    """Base class for all tools"""
    
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for LLM integration"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        } 