"""
Multi-provider LLM client for research agents
Supports Anthropic Claude (primary) and OpenAI (fallback)
"""

import os
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from project root (override system env vars)
load_dotenv(Path(__file__).parent.parent.parent / '.env', override=True)

class LLMClient:
    """Multi-provider LLM client wrapper for research tasks"""
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize LLM client with specified provider
        
        Args:
            provider: "openai" (default) or "anthropic"
        """
        self.provider = provider
        self.anthropic_client = None
        self.openai_client = None
        
        # Model configurations based on provider
        if provider == "anthropic":
            self.mini_model = "claude-3-haiku-20240307"  # Fast, simple tasks
            self.full_model = "claude-3-5-sonnet-20241022"  # Complex reasoning - use available model
        else:  # OpenAI
            self.mini_model = "gpt-4o-mini"
            self.full_model = "gpt-4o"
        
        # Embedding model (OpenAI only for now)
        self.embedding_model = "text-embedding-3-small"
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available clients based on API keys"""
        
        # Try Anthropic initialization
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            try:
                import anthropic
                # Clean quotes from key if present
                clean_key = anthropic_key.strip('"')
                self.anthropic_client = anthropic.Anthropic(api_key=clean_key)
                print(f"✅ Anthropic client initialized")
            except Exception as e:
                print(f"⚠️  Anthropic client initialization failed: {e}")
        
        # Try OpenAI initialization  
        openai_key = os.getenv('OPENAI_API_KEY')
        org_id = os.getenv('OPENAI_ORGANIZATION_ID')
        project_id = os.getenv('OPENAI_PROJECT_ID')
        
        if openai_key:
            try:
                from openai import OpenAI
                # Clean quotes from key if present
                clean_key = openai_key.strip('"')
                clean_org = org_id.strip('"') if org_id else None
                clean_project = project_id.strip('"') if project_id else None
                
                # Create client with org and project IDs
                client_params = {"api_key": clean_key}
                if clean_org:
                    client_params["organization"] = clean_org
                if clean_project:
                    client_params["project"] = clean_project
                
                self.openai_client = OpenAI(**client_params)
                print(f"✅ OpenAI client initialized")
            except Exception as e:
                print(f"⚠️  OpenAI client initialization failed: {e}")
    
    def chat_completion(self, messages: List[Dict[str, str]], model: str = None, temperature: float = 0.3) -> str:
        """
        Get chat completion from configured provider with fallback
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Specific model name (uses default if None)
            temperature: Randomness level 0-1
            
        Returns:
            Response content as string
        """
        if model is None:
            model = self.mini_model
        
        # Try primary provider first
        if self.provider == "anthropic" and self.anthropic_client:
            try:
                return self._anthropic_chat(messages, model, temperature)
            except Exception as e:
                print(f"⚠️  Anthropic failed, trying OpenAI fallback: {e}")
        elif self.provider == "openai" and self.openai_client:
            try:
                return self._openai_chat(messages, model, temperature)
            except Exception as e:
                print(f"⚠️  OpenAI failed, trying Anthropic fallback: {e}")
        
        # Try fallback provider
        return self._fallback_chat(messages, model, temperature)
    
    def structured_completion(self, messages: List[Dict[str, str]], response_format: Dict[str, Any] = None, model: str = None) -> Dict[str, Any]:
        """
        Get structured JSON completion from configured provider
        
        Args:
            messages: List of message dicts
            response_format: Response format specification (used by OpenAI)
            model: Specific model name (uses default if None)
            
        Returns:
            Parsed JSON response
        """
        if model is None:
            model = self.mini_model
        
        # Handle provider-specific JSON responses
        if self.provider == "anthropic" and self.anthropic_client:
            try:
                return self._anthropic_structured(messages, model)
            except Exception as e:
                print(f"⚠️  Anthropic structured failed, trying OpenAI: {e}")
                if self.openai_client:
                    return self._openai_structured(messages, response_format, model)
        elif self.provider == "openai" and self.openai_client:
            try:
                return self._openai_structured(messages, response_format, model)
            except Exception as e:
                print(f"⚠️  OpenAI structured failed, trying Anthropic: {e}")
                if self.anthropic_client:
                    return self._anthropic_structured(messages, self.mini_model)
        
        # Fallback
        return self._fallback_structured(messages, response_format, model)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get text embedding from OpenAI
        
        Args:
            text: Input text to embed
            
        Returns:
            List of float values representing the embedding vector
        """
        if not self.openai_client:
            # Fallback to mock if OpenAI not available
            print(f"⚠️  OpenAI not available, using mock embedding for: {text[:50]}...")
            text_hash = hash(text) % 1000000
            random.seed(text_hash)
            return [random.uniform(-1, 1) for _ in range(1536)]
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            print(f"⚠️  OpenAI embedding failed: {e}")
            # Fallback to mock on error
            text_hash = hash(text) % 1000000
            random.seed(text_hash)
            return [random.uniform(-1, 1) for _ in range(1536)]
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts from OpenAI
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            print(f"⚠️  OpenAI not available, using mock embeddings for {len(texts)} texts")
            return [self.get_embedding(text) for text in texts]
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
            
        except Exception as e:
            print(f"⚠️  OpenAI batch embeddings failed: {e}")
            # Fallback to individual requests
            return [self.get_embedding(text) for text in texts]
    
    def _anthropic_chat(self, messages: List[Dict[str, str]], model: str, temperature: float) -> str:
        """Anthropic-specific chat completion"""
        # Separate system messages from regular messages for Anthropic
        system_content = None
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                filtered_messages.append(msg)
        
        # Create request parameters
        request_params = {
            "model": model,
            "max_tokens": 2000,
            "temperature": temperature,
            "messages": filtered_messages
        }
        
        # Add system parameter if we found system messages
        if system_content:
            request_params["system"] = system_content
        
        response = self.anthropic_client.messages.create(**request_params)
        return response.content[0].text
    
    def _openai_chat(self, messages: List[Dict[str, str]], model: str, temperature: float) -> str:
        """OpenAI-specific chat completion"""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _anthropic_structured(self, messages: List[Dict[str, str]], model: str) -> Dict[str, Any]:
        """Anthropic structured JSON completion"""
        # Handle system messages properly for Anthropic
        system_content = None
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                user_messages.append(msg)
        
        # Add JSON instruction to the last user message
        if user_messages:
            last_message = user_messages[-1].copy()
            last_message["content"] = (
                "Respond with valid JSON only. Do not include any text before or after the JSON.\n\n" + 
                last_message["content"]
            )
            structured_messages = user_messages[:-1] + [last_message]
        else:
            structured_messages = user_messages
        
        # Create request with proper system handling
        if system_content:
            # Combine system instruction with JSON requirement
            combined_system = system_content + "\n\nAlways respond with valid JSON format only."
            structured_messages = [{"role": "system", "content": combined_system}] + structured_messages
        
        response_text = self._anthropic_chat(structured_messages, model, 0.1)
        
        # Clean response and parse JSON
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response.replace('```', '').strip()
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed, raw response: {cleaned_response[:200]}...")
            # Return a basic structure as fallback
            return {"error": "JSON parsing failed", "raw_response": cleaned_response}
    
    def _openai_structured(self, messages: List[Dict[str, str]], response_format: Dict[str, Any], model: str) -> Dict[str, Any]:
        """OpenAI structured JSON completion"""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _fallback_chat(self, messages: List[Dict[str, str]], model: str, temperature: float) -> str:
        """Try alternative provider as fallback"""
        
        # Try Anthropic if not primary
        if self.provider != "anthropic" and self.anthropic_client:
            try:
                fallback_model = "claude-3-haiku-20240307"  # Safe fallback model
                return self._anthropic_chat(messages, fallback_model, temperature)
            except Exception as e:
                print(f"⚠️  Anthropic fallback failed: {e}")
        
        # Try OpenAI if not primary  
        if self.provider != "openai" and self.openai_client:
            try:
                fallback_model = "gpt-4o-mini"  # Safe fallback model
                return self._openai_chat(messages, fallback_model, temperature)
            except Exception:
                pass
        
        # If all fails, raise error
        raise Exception(f"No working LLM provider available. Provider: {self.provider}, Anthropic: {'✅' if self.anthropic_client else '❌'}, OpenAI: {'✅' if self.openai_client else '❌'}")
    
    def _fallback_structured(self, messages: List[Dict[str, str]], response_format: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Try alternative provider for structured completion"""
        
        # Try Anthropic if not primary
        if self.provider != "anthropic" and self.anthropic_client:
            try:
                return self._anthropic_structured(messages, "claude-3-haiku-20240307")
            except Exception:
                pass
        
        # Try OpenAI if not primary
        if self.provider != "openai" and self.openai_client:
            try:
                return self._openai_structured(messages, response_format, "gpt-4o-mini")
            except Exception:
                pass
        
        # Return error structure if all fails
        return {"error": "No working LLM provider available for structured completion"}
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider setup"""
        return {
            "primary_provider": self.provider,
            "anthropic_available": self.anthropic_client is not None,
            "openai_available": self.openai_client is not None,
            "mini_model": self.mini_model,
            "full_model": self.full_model,
            "embedding_model": self.embedding_model
        }
