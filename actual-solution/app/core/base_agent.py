"""
Base Agent and Context Management for AI Co-Pilot Multi-Agent System
"""

import logging
import json
import yaml
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
import google.generativeai as genai
from groq import Groq

from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LLM clients
genai.configure(api_key=settings.google_api_key)
groq_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None

class LLMState:
    """Manages LLM fallback state with sticky behavior."""
    def __init__(self):
        self._use_groq = False
    
    def should_use_groq(self) -> bool:
        return self._use_groq
    
    def switch_to_groq(self):
        self._use_groq = True
        logger.info("Switched to Groq LLM for this session")

# Global LLM state
llm_state = LLMState()

class ConversationContext(BaseModel):
    """Shared context between agents in a conversation."""
    session_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    client_context: Dict[str, Any] = Field(default_factory=dict)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    pain_points: List[Dict[str, Any]] = Field(default_factory=list)
    discovered_services: Dict[str, Any] = Field(default_factory=dict)
    rag_results: Dict[str, Any] = Field(default_factory=dict)  # Stores results by search_id
    scoping_results: Dict[str, Any] = Field(default_factory=dict)  # Stores results by service
    current_phase: str = "discovery"
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.last_updated = datetime.now()
    
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation messages."""
        return self.conversation_history[-count:]
    
    def update_context(self, updates: Dict[str, Any]):
        """Update context with new information."""
        for key, value in updates.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), dict):
                    getattr(self, key).update(value)
                elif isinstance(getattr(self, key), list) and isinstance(value, list):
                    getattr(self, key).extend(value)
                else:
                    setattr(self, key, value)
        self.last_updated = datetime.now()

class AgentResponse(BaseModel):
    """Standardized response format for all agents."""
    success: bool
    agent_name: str
    content: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    execution_time: Optional[float] = None
    error: Optional[str] = None

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agents.{agent_name}")
        self.model = genai.GenerativeModel(settings.gemini_model)
        
        # Load system prompt from bots.yaml
        self.system_prompt = self._load_system_prompt()
        
        self.logger.info(f"Initialized {agent_name} agent")
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from bots.yaml configuration."""
        try:
            with open("config/bots.yaml", "r") as f:
                config = yaml.safe_load(f)
            
            prompt = config["agents"][self.agent_name]["system_prompt"]
            self.logger.debug(f"Loaded system prompt for {self.agent_name}")
            return prompt
            
        except Exception as e:
            self.logger.error(f"Failed to load system prompt: {e}")
            return f"You are a helpful AI assistant specialized in {self.agent_name}."
    
    async def _generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini or Groq (with sticky fallback)."""
        
        self.logger.info(f"🤖 {self.agent_name.upper()}: Generating LLM response...")
        self.logger.info(f"🌡️  TEMPERATURE: {kwargs.get('temperature', 0.7)}")
        self.logger.info(f"📝 PROMPT LENGTH: {len(prompt)} characters")
        self.logger.info(f"🔄 SHOULD USE GROQ: {llm_state.should_use_groq()}")
        
        # Check if we should use Groq (sticky behavior)
        if llm_state.should_use_groq():
            self.logger.info(f"🟠 {self.agent_name.upper()}: Using Groq (sticky mode)")
            return await self._generate_response_groq(prompt, **kwargs)
        
        # Try Gemini first
        try:
            self.logger.info(f"🔵 {self.agent_name.upper()}: Trying Gemini API...")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get('temperature', 0.7),
                    top_p=kwargs.get('top_p', 0.8),
                    top_k=kwargs.get('top_k', 40),
                    max_output_tokens=kwargs.get('max_tokens', 1000),
                )
            )
            
            self.logger.info(f"✅ GEMINI SUCCESS: {len(response.text)} characters received")
            self.logger.info(f"📝 GEMINI PREVIEW: {response.text[:200]}...")
            return response.text
            
        except Exception as e:
            self.logger.warning(f"❌ GEMINI FAILED: {e}")
            # Switch to Groq and stick with it
            self.logger.info("🔄 SWITCHING TO GROQ: Gemini failed, activating sticky fallback")
            llm_state.switch_to_groq()
            return await self._generate_response_groq(prompt, **kwargs)
    
    async def _generate_response_groq(self, prompt: str, **kwargs) -> str:
        """Generate response using Groq."""
        if not groq_client:
            self.logger.error("❌ GROQ NOT AVAILABLE: Client not initialized - check API key")
            raise Exception("Groq client not available - check API key")
            
        try:
            self.logger.info(f"🟠 {self.agent_name.upper()}: Calling Groq API...")
            
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=settings.groq_model,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 1000),
                top_p=kwargs.get('top_p', 0.8),
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Groq also failed: {e}")
            raise
    
    def _create_prompt(self, context: ConversationContext, user_input: str) -> str:
        """Create a complete prompt with system prompt, context, and user input."""
        conversation_summary = self._summarize_conversation(context)
        
        prompt = f"""
{self.system_prompt}

## Current Conversation Context:
{conversation_summary}

## User Input:
{user_input}

Please respond according to your role and the specified JSON format.
"""
        return prompt
    
    def _summarize_conversation(self, context: ConversationContext) -> str:
        """Create a summary of the conversation context."""
        summary_parts = []
        
        try:
            if context.client_context:
                summary_parts.append(f"Client Context: {json.dumps(context.client_context, indent=2)}")
            
            if context.business_context:
                summary_parts.append(f"Business Context: {json.dumps(context.business_context, indent=2)}")
            
            if context.pain_points:
                summary_parts.append(f"Pain Points: {json.dumps(context.pain_points, indent=2)}")
            
            if context.discovered_services:
                summary_parts.append(f"Discovered Services: {json.dumps(context.discovered_services, indent=2)}")
            
            if context.conversation_history:
                recent_messages = context.get_recent_messages(3)
                self.logger.info(f"🔍 RECENT MESSAGES: {recent_messages}")
                summary_parts.append(f"Recent Messages: {json.dumps(recent_messages, indent=2)}")
            
            return "\n\n".join(summary_parts) if summary_parts else "No context available."
            
        except Exception as e:
            self.logger.error(f"Error summarizing conversation: {e}")
            return "Error summarizing conversation context."
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM, with error handling."""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()
            
            # Handle markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            
            # If response contains template examples, try to find the actual JSON
            if "### Response Format:" in response_text or "Always respond with valid JSON" in response_text:
                # Look for the last JSON object in the response
                json_start = response_text.rfind("{")
                if json_start != -1:
                    # Find the matching closing brace
                    brace_count = 0
                    json_end = json_start
                    for i, char in enumerate(response_text[json_start:], json_start):
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    response_text = response_text[json_start:json_end]
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from {self.agent_name}")
    
    @abstractmethod
    async def process(self, context: ConversationContext, user_input: str) -> AgentResponse:
        """Process user input and return agent response."""
        pass

class ContextManager:
    """Manages conversation contexts across sessions."""
    
    def __init__(self):
        self.active_contexts: Dict[str, ConversationContext] = {}
        self.logger = logging.getLogger("context_manager")
    
    def get_context(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for session."""
        if session_id not in self.active_contexts:
            self.active_contexts[session_id] = ConversationContext(session_id=session_id)
            self.logger.info(f"Created new context for session {session_id}")
        
        return self.active_contexts[session_id]
    
    def update_context(self, context: ConversationContext):
        """Update stored context."""
        self.active_contexts[context.session_id] = context
        self.logger.debug(f"Updated context for session {context.session_id}")
    
    def clear_context(self, session_id: str):
        """Clear context for session."""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
            self.logger.info(f"Cleared context for session {session_id}")

# Global context manager
context_manager = ContextManager()
