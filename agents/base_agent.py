"""
Base Agent Module

Provides base class for all LLM-powered agents.
"""
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from openai import OpenAI

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


class BaseAgent(ABC):
    """Base class for all agents in the document analysis pipeline."""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            model: OpenAI model to use
        """
        self.model = model or settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    @abstractmethod
    def process(self, **kwargs) -> Dict[str, Any]:
        """Process input and return results."""
        pass
    
    def _call_llm(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Call the LLM with given prompts.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            response_format: Optional response format specification
            
        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def _call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Call LLM and parse JSON response.
        
        Returns:
            Parsed JSON dict
        """
        import json
        
        response = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Failed to parse JSON", "raw_response": response}
