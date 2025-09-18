"""
Strategy Agent - The Brain of the Multi-Agent System

This agent analyzes user input and determines the optimal sequence of other agents
to execute based on conversation context and D&T service expertise.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
from app.core.base_agent import BaseAgent, ConversationContext, AgentResponse

class StrategyAgent(BaseAgent):
    """
    Expert Strategy Agent that acts as the brain of the multi-agent system.
    Analyzes user input and orchestrates other agents based on business context.
    """
    
    def __init__(self):
        super().__init__("strategy_agent")
    
    async def process(self, context: ConversationContext, user_input: str) -> AgentResponse:
        """
        Analyze user input and determine optimal agent execution sequence.
        
        Returns either:
        1. execute_pipeline - with specific agent sequence
        2. gather_more_context - with targeted follow-up questions
        """
        start_time = time.time()
        
        self.logger.info(f"🧠 STRATEGY AGENT: Starting analysis for session {context.session_id}")
        self.logger.info(f"📝 USER INPUT: '{user_input}'")
        self.logger.info(f"📊 CONTEXT: {len(context.conversation_history)} messages in history")
        self.logger.info(f"📊 CLIENT CONTEXT: {context.client_context}")
        self.logger.info(f"📊 BUSINESS CONTEXT: {context.business_context}")
        self.logger.info(f"📊 PAIN POINTS: {len(context.pain_points)} identified")
        
        # Debug: Check conversation history structure
        self.logger.info(f"🔍 CONVERSATION HISTORY DEBUG:")
        for i, msg in enumerate(context.conversation_history):
            self.logger.info(f"  Message {i}: {type(msg)} - {msg}")
        
        try:
            # Create strategy analysis prompt
            self.logger.info(f"🔍 STRATEGY AGENT: Creating analysis prompt...")
            try:
                prompt = self._create_strategy_prompt(context, user_input)
                self.logger.info(f"📝 PROMPT LENGTH: {len(prompt)} characters")
            except Exception as e:
                self.logger.error(f"❌ PROMPT CREATION FAILED: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Generate strategy response
            self.logger.info(f"🤖 STRATEGY AGENT: Calling LLM for strategy decision...")
            response_text = await self._generate_response(prompt, temperature=0.3)
            self.logger.info(f"🤖 LLM RESPONSE LENGTH: {len(response_text)} characters")
            self.logger.info(f"🤖 LLM RESPONSE PREVIEW: {response_text[:200]}...")
            
            # Parse JSON response
            self.logger.info(f"🔍 STRATEGY AGENT: Parsing JSON response...")
            self.logger.info(f"🔍 RAW LLM RESPONSE: {response_text}")
            strategy_decision = self._parse_json_response(response_text)
            self.logger.info(f"🔍 PARSED DECISION: {strategy_decision}")
            
            if strategy_decision:
                decision = strategy_decision.get('decision', 'unknown')
                self.logger.info(f"🎯 STRATEGY DECISION: {decision}")
                
                if decision == "execute_pipeline":
                    agents_sequence = strategy_decision.get('agents_sequence', [])
                    self.logger.info(f"🔧 PIPELINE: {len(agents_sequence)} agents to execute")
                    for i, agent in enumerate(agents_sequence):
                        agent_name = agent.get('agent', 'unknown')
                        focus = agent.get('search_focus', agent.get('scope_focus', agent.get('response_type', 'N/A')))
                        self.logger.info(f"   {i+1}. {agent_name} - {focus}")
                elif decision == "gather_more_context":
                    follow_up = strategy_decision.get('follow_up_question', 'N/A')
                    self.logger.info(f"❓ FOLLOW-UP: {follow_up}")
            else:
                self.logger.error(f"❌ STRATEGY AGENT: Failed to parse JSON response")
            
            # Validate strategy decision
            validated_decision = self._validate_strategy_decision(strategy_decision)
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Strategy decision: {validated_decision.get('decision', 'unknown')}")
            
            return AgentResponse(
                success=True,
                agent_name=self.agent_name,
                content=validated_decision,
                confidence=self._calculate_confidence(validated_decision, context),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Strategy analysis failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide fallback strategy
            fallback_strategy = self._create_fallback_strategy(context, user_input)
            
            return AgentResponse(
                success=False,
                agent_name=self.agent_name,
                content=fallback_strategy,
                confidence=0.3,
                execution_time=execution_time,
                error=error_msg
            )
    
    def _create_strategy_prompt(self, context: ConversationContext, user_input: str) -> str:
        """Create a comprehensive prompt for strategy analysis."""
        
        # Extract and update context from conversation
        self._extract_context_from_conversation(context, user_input)
        
        # Analyze conversation completeness
        context_analysis = self._analyze_context_completeness(context)
        
        base_prompt = self._create_prompt(context, user_input)
        
        strategy_prompt = f"""
{base_prompt}

## Context Analysis:
{context_analysis}

## Strategy Decision Required:
You are a senior consultant with deep expertise in D&T services. Based on the conversation so far:

**CRITICAL DECISION RULE**: If the context analysis shows "🔴 INSUFFICIENT CONTEXT", you MUST choose "gather_more_context". Do NOT execute the pipeline with insufficient information.

1. **Execute Pipeline** ONLY if you have ALL of these:
   - **Specific business challenges** (not just "they have problems")
   - **Business impact** (how problems affect operations, costs, growth)
   - **Sufficient detail** (more than just a greeting or vague statement)
   - **Clear pain points** that D&T services can address
   - **Context analysis shows "🟢 SUFFICIENT CONTEXT"**

2. **Gather More Context** when:
   - Context analysis shows "🔴 INSUFFICIENT CONTEXT" or "🟡 PARTIAL CONTEXT"
   - User just mentioned they have a client but no specific challenges
   - Challenges mentioned are too vague ("scalability issues" without details)
   - No business impact or urgency described
   - Missing key information needed for proper service recommendations

**Examples:**
- ❌ "I have a retail client" → Gather more context
- ❌ "They have scalability issues" → Gather more context  
- ✅ "Legacy POS system can't handle Black Friday traffic, losing $50K/day" → Execute pipeline

## Your D&T Service Expertise:
- **Cloud**: Legacy system modernization, scalability, infrastructure
- **Data & Analytics**: Data management, reporting, insights
- **Digital**: Process automation, digital transformation
- **Application Development**: Custom solutions, integrations

## Decision Guidelines:
- **Be proactive**: If you see technology challenges, recommend solutions
- **Use context clues**: Banking + legacy systems = likely cloud/application services
- **Think business impact**: Scalability issues affect revenue and operations
- **Trust your expertise**: You know which D&T services solve which problems

Respond with valid JSON only, following the exact format specified in your system prompt.
"""
        
        return strategy_prompt
    
    def _analyze_context_completeness(self, context: ConversationContext) -> str:
        """Analyze how complete the conversation context is."""
        analysis = []
        
        # Check client context
        if context.client_context:
            analysis.append(f"✅ Client Context: {len(context.client_context)} items")
        else:
            analysis.append("❌ Client Context: Missing")
        
        # Check business context
        if context.business_context:
            analysis.append(f"✅ Business Context: {len(context.business_context)} items")
        else:
            analysis.append("❌ Business Context: Missing")
        
        # Check pain points
        if context.pain_points:
            analysis.append(f"✅ Pain Points: {len(context.pain_points)} identified")
        else:
            analysis.append("❌ Pain Points: Not identified")
        
        # Check conversation history
        if context.conversation_history:
            analysis.append(f"✅ Conversation: {len(context.conversation_history)} messages")
        else:
            analysis.append("❌ Conversation: Just started")
        
        # Overall assessment - More realistic thresholds
        completeness_score = sum(1 for item in analysis if item.startswith("✅")) / len(analysis)
        
        # Check if we have SPECIFIC business challenges and pain points
        conversation_texts = []
        self.logger.info(f"🔍 ANALYZING CONVERSATION: {len(context.conversation_history)} messages")
        for i, msg in enumerate(context.conversation_history):
            self.logger.info(f"  Message {i}: {type(msg)} - {msg}")
            if isinstance(msg, dict):
                conversation_texts.append(msg.get("content", ""))
            else:
                conversation_texts.append(str(msg))
        all_conversation_text = " ".join(conversation_texts).lower()
        
        # Look for specific business challenges, not just generic mentions
        specific_challenges = any(phrase in all_conversation_text for phrase in [
            "legacy system", "scalability issue", "performance problem", "outdated", "slow", "inefficient",
            "data problem", "integration issue", "security concern", "compliance", "cost reduction",
            "modernization", "digital transformation", "automation", "process improvement",
            "tender", "manual process", "physical", "online", "digital", "submission", "paperwork",
            "in-person", "holding", "burden", "labor", "storing"
        ])
        
        # Look for business impact indicators
        business_impact = any(phrase in all_conversation_text for phrase in [
            "losing money", "revenue impact", "customer complaints", "operational cost", "efficiency",
            "growth", "expansion", "competitive", "market pressure", "urgent", "critical",
            "want to stop", "trying to", "moving online", "more efficient", "mitigate", "address",
            "pain points", "issues", "challenges", "problems", "inefficiencies"
        ])
        
        # Look for sufficient detail (not just "hello I have a client")
        has_detail = len(all_conversation_text.split()) > 15  # More than just a greeting
        
        # Be much more conservative about executing pipeline
        if specific_challenges and business_impact and has_detail:
            assessment = "🟢 SUFFICIENT CONTEXT - Ready for service recommendations"
        elif specific_challenges and has_detail:
            assessment = "🟡 PARTIAL CONTEXT - Need business impact details"
        else:
            assessment = "🔴 INSUFFICIENT CONTEXT - Need specific challenges and business impact"
        
        return f"{assessment}\n\n" + "\n".join(analysis)
    
    def _extract_context_from_conversation(self, context: ConversationContext, user_input: str):
        """Extract and update context from conversation history and current input."""
        
        self.logger.info(f"🔍 CONTEXT EXTRACTION: Analyzing conversation for context clues...")
        
        # Combine all conversation text for analysis
        conversation_texts = []
        self.logger.info(f"🔍 EXTRACTING CONTEXT: {len(context.conversation_history)} messages")
        for i, msg in enumerate(context.conversation_history):
            self.logger.info(f"  Message {i}: {type(msg)} - {msg}")
            if isinstance(msg, dict):
                content = msg.get("content", "")
                self.logger.info(f"    Content: {type(content)} - {content}")
                conversation_texts.append(content)
            else:
                conversation_texts.append(str(msg))
        
        self.logger.info(f"🔍 EXTRACTED TEXTS: {conversation_texts}")
        self.logger.info(f"🔍 TEXT TYPES: {[type(t) for t in conversation_texts]}")
        
        # Debug: Check each item in conversation_texts
        for i, text in enumerate(conversation_texts):
            self.logger.info(f"  Text {i}: {type(text)} - {text}")
        
        all_text = " ".join(conversation_texts + [user_input]).lower()
        
        self.logger.info(f"📝 COMBINED TEXT: {len(all_text)} characters to analyze")
        self.logger.info(f"📝 TEXT PREVIEW: '{all_text[:150]}...'")
        
        # Extract client context
        client_updates = []
        if "bank" in all_text:
            context.client_context["industry"] = "Banking/Financial Services"
            client_updates.append("industry: Banking/Financial Services")
        if "qatari" in all_text or "qatar" in all_text:
            context.client_context["location"] = "Qatar"
            client_updates.append("location: Qatar")
        if "regional" in all_text:
            context.client_context["company_size"] = "Regional/Medium Enterprise"
            client_updates.append("company_size: Regional/Medium Enterprise")
        
        if client_updates:
            self.logger.info(f"👤 CLIENT CONTEXT UPDATES: {', '.join(client_updates)}")
            
        # Extract business context
        if any(word in all_text for word in ["legacy", "old", "outdated"]):
            context.business_context["technology_maturity"] = "Legacy systems"
        if any(word in all_text for word in ["scalability", "scale", "demand", "growth"]):
            context.business_context["key_drivers"] = "Scalability and growth"
        if any(word in all_text for word in ["account opening", "new accounts"]):
            context.business_context["specific_processes"] = "Account opening processes"
            
        # Extract pain points
        pain_point_keywords = {
            "legacy applications": "Legacy application modernization needed",
            "scalability": "System cannot handle increasing demand", 
            "on-premise": "On-premise infrastructure limitations",
            "data writing": "Data management and processing issues",
            "increasing demand": "Business growth outpacing system capacity"
        }
        
        for keyword, description in pain_point_keywords.items():
            if keyword in all_text:
                pain_point = {
                    "description": description,
                    "category": "technology" if keyword in ["legacy", "on-premise", "data"] else "business",
                    "urgency": "high" if keyword in ["demand", "scalability"] else "medium"
                }
                if pain_point not in context.pain_points:
                    context.pain_points.append(pain_point)
        
        # Update last_updated timestamp
        context.last_updated = datetime.now()
    
    def _validate_strategy_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance strategy decision structure."""
        
        if "decision" not in decision:
            raise ValueError("Strategy decision missing 'decision' field")
        
        if decision["decision"] not in ["execute_pipeline", "gather_more_context", "provide_estimates"]:
            raise ValueError(f"Invalid decision type: {decision['decision']}")
        
        # Validate agents_sequence
        if "agents_sequence" not in decision:
            raise ValueError("Strategy decision missing 'agents_sequence'")
        
        # Validate each agent in sequence
        for i, agent_config in enumerate(decision["agents_sequence"]):
            if "agent" not in agent_config:
                raise ValueError(f"Agent {i} missing 'agent' field")
            
            if "depends_on" not in agent_config:
                agent_config["depends_on"] = []
        
        # Ensure scoping agents have baseline_source
        for agent_config in decision["agents_sequence"]:
            if agent_config["agent"] == "scoping_agent":
                if "baseline_source" not in agent_config:
                    # Check if this is an estimates-only request (no RAG needed)
                    if decision.get("decision") == "provide_estimates":
                        agent_config["baseline_source"] = "direct_lookup"
                    else:
                        # Find the first RAG search to use as baseline
                        for rag_agent in decision["agents_sequence"]:
                            if rag_agent["agent"] == "rag_agent":
                                agent_config["baseline_source"] = rag_agent.get("search_id", "search_1")
                                break
        
        return decision
    
    def _calculate_confidence(self, decision: Dict[str, Any], context: ConversationContext) -> float:
        """Calculate confidence score for the strategy decision."""
        base_confidence = 0.7
        
        # Boost confidence if we have good context
        if context.pain_points:
            base_confidence += 0.1
        if context.business_context:
            base_confidence += 0.1
        if len(context.conversation_history) > 2:
            base_confidence += 0.1
        
        # Adjust based on decision type
        if decision.get("decision") == "execute_pipeline":
            # Higher confidence if we're making recommendations
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _create_fallback_strategy(self, context: ConversationContext, user_input: str) -> Dict[str, Any]:
        """Create a fallback strategy when LLM generation fails."""
        
        # Analyze what we have
        has_context = bool(context.client_context or context.business_context)
        has_pain_points = bool(context.pain_points)
        
        if has_context and has_pain_points:
            # We have some context, try to provide recommendations
            return {
                "decision": "execute_pipeline",
                "consultant_hypothesis": "Based on available context, attempting to provide service recommendations",
                "agents_sequence": [
                    {
                        "agent": "rag_agent",
                        "search_id": "search_1", 
                        "search_focus": "general D&T services for business challenges",
                        "depends_on": []
                    },
                    {
                        "agent": "summarizing_agent",
                        "response_type": "service_recommendations",
                        "depends_on": ["rag_agent"]
                    }
                ]
            }
        else:
            # We need more context
            return {
                "decision": "gather_more_context",
                "consultant_analysis": "Insufficient context for service recommendations",
                "follow_up_focus": "business_context",
                "agents_sequence": [
                    {
                        "agent": "summarizing_agent",
                        "response_type": "targeted_follow_up",
                        "question_focus": "business challenges and pain points",
                        "depends_on": []
                    }
                ]
            }
