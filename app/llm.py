"""
LLM integration for the University Data Collection System
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call from the LLM"""
    function: Dict[str, Any]
    arguments: str


@dataclass
class LLMResponse:
    """Response from the LLM"""
    content: str
    tool_calls: Optional[List[ToolCall]] = None


class LLM:
    """LLM client for tool integration"""
    
    def __init__(self, config=None):
        """
        Initialize LLM client
        
        Args:
            config: LLM configuration (optional, will use default if not provided)
        """
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on configuration"""
        try:
            if not self.config:
                # Use default configuration
                import os
                from .config import LLMConfig
                self.config = LLMConfig(
                    provider=os.getenv("LLM_PROVIDER", "openai"),
                    api_key=os.getenv("LLM_API_KEY"),
                    model=os.getenv("LLM_MODEL", "gpt-4"),
                    base_url=os.getenv("LLM_BASE_URL"),
                    temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
                    max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
                    timeout=int(os.getenv("LLM_TIMEOUT", "30"))
                )
            
            if self.config.provider == "openai":
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
            elif self.config.provider == "anthropic":
                import anthropic
                self.client = anthropic.AsyncAnthropic(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url
                )
            elif self.config.provider == "local":
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key="not-needed",
                    base_url=self.config.base_url or "http://localhost:11434/v1"
                )
            else:
                logger.warning(f"Unknown LLM provider: {self.config.provider}")
                
        except ImportError as e:
            logger.error(f"Failed to import LLM library for {self.config.provider}: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    
    async def ask_tool(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Optional[LLMResponse]:
        """
        Ask the LLM with tool calling support
        
        Args:
            messages: List of message dictionaries
            tools: List of tool schemas
            tool_choice: Tool choice strategy ("required", "auto", etc.)
            
        Returns:
            LLMResponse with content and optional tool calls
        """
        if not self.client:
            logger.error("LLM client not initialized")
            return None
        
        try:
            if self.config.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                content = response.choices[0].message.content
                tool_calls = None
                
                if response.choices[0].message.tool_calls:
                    tool_calls = []
                    for tool_call in response.choices[0].message.tool_calls:
                        tool_calls.append(ToolCall(
                            function=tool_call.function.model_dump(),
                            arguments=tool_call.function.arguments
                        ))
                
                return LLMResponse(content=content, tool_calls=tool_calls)
            
            elif self.config.provider == "anthropic":
                # Anthropic doesn't support tool calling in the same way
                # For now, just return the content
                response = await self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=messages
                )
                return LLMResponse(content=response.content[0].text)
            
            elif self.config.provider == "local":
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                content = response.choices[0].message.content
                tool_calls = None
                
                if response.choices[0].message.tool_calls:
                    tool_calls = []
                    for tool_call in response.choices[0].message.tool_calls:
                        tool_calls.append(ToolCall(
                            function=tool_call.function.model_dump(),
                            arguments=tool_call.function.arguments
                        ))
                
                return LLMResponse(content=content, tool_calls=tool_calls)
                
        except Exception as e:
            logger.error(f"Error asking LLM: {e}")
            return None 