"""
AI Co-Pilot Orchestrator - The Heart of the Multi-Agent System

This orchestrator receives user messages, calls the Strategy Agent to determine
the optimal agent execution sequence, then executes that sequence and returns
a natural language response to the consultant.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from app.core.base_agent import ConversationContext, context_manager
from app.agents.strategy import StrategyAgent
from app.agents.rag import RAGAgent
from app.agents.scoping import ScopingAgent
from app.agents.summarizing import SummarizingAgent

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Main orchestrator that coordinates all agents based on strategy decisions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("orchestrator")
        
        # Initialize all agents
        self.strategy_agent = StrategyAgent()
        self.rag_agent = RAGAgent()
        self.scoping_agent = ScopingAgent()
        self.summarizing_agent = SummarizingAgent()
        
        self.logger.info("Orchestrator initialized with all agents")
    
    async def process_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        Process a user message through the multi-agent pipeline.
        
        Args:
            session_id: Unique session identifier
            user_message: Message from the consultant
            
        Returns:
            Dictionary containing the AI response and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🚀 ORCHESTRATOR: Processing message for session {session_id}")
            self.logger.info(f"📝 USER INPUT: '{user_message}'")
            self.logger.info(f"⏰ START TIME: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
            
            # Get or create conversation context
            self.logger.info(f"🔍 ORCHESTRATOR: Getting context for session {session_id}")
            context = context_manager.get_context(session_id)
            self.logger.info(f"📊 CONTEXT: {len(context.conversation_history)} messages in history")
            
            # Add user message to context
            context.add_message("user", user_message)
            self.logger.info(f"✅ CONTEXT: User message added to conversation history")
            
            # Step 1: Get strategy decision from Strategy Agent
            self.logger.info(f"🧠 ORCHESTRATOR: Calling Strategy Agent...")
            strategy_response = await self.strategy_agent.process(context, user_message)
            
            self.logger.info(f"🧠 STRATEGY RESPONSE: Success={strategy_response.success}")
            if strategy_response.success:
                self.logger.info(f"🎯 STRATEGY DECISION: {strategy_response.content.get('decision', 'unknown')}")
                self.logger.info(f"📋 STRATEGY OUTPUT: {str(strategy_response.content)[:200]}...")
            else:
                self.logger.error(f"❌ STRATEGY FAILED: {strategy_response.error}")
            
            if not strategy_response.success:
                self.logger.error(f"Strategy agent failed: {strategy_response.error}")
                return self._create_error_response(
                    "I'm having trouble analyzing your request. Could you provide more details about your client's situation?",
                    strategy_response.error
                )
            
            strategy_decision = strategy_response.content
            self.logger.info(f"🎯 STRATEGY DECISION: {strategy_decision.get('decision', 'unknown')}")
            
            # Step 2: Execute the agent sequence defined by strategy
            agents_sequence = strategy_decision.get("agents_sequence", [])
            self.logger.info(f"🔧 ORCHESTRATOR: Executing {len(agents_sequence)} agents in sequence")
            for i, agent_config in enumerate(agents_sequence):
                agent_name = agent_config.get('agent', 'unknown')
                focus = agent_config.get('search_focus', agent_config.get('scope_focus', agent_config.get('response_type', 'N/A')))
                self.logger.info(f"   {i+1}. {agent_name} - {focus}")
            
            execution_results = await self._execute_agent_sequence(context, agents_sequence)
            self.logger.info(f"🔧 EXECUTION RESULTS: {len(execution_results)} agents completed")
            
            # Step 3: Generate final response
            self.logger.info(f"📋 ORCHESTRATOR: Generating final response...")
            final_response = self._generate_final_response(
                context, 
                strategy_decision, 
                execution_results
            )
            
            self.logger.info(f"📝 FINAL RESPONSE TYPE: {final_response.get('type', 'unknown')}")
            self.logger.info(f"📝 FINAL RESPONSE LENGTH: {len(final_response.get('content', ''))}")
            
            # Add AI response to context
            context.add_message("ai", final_response["content"], final_response.get("metadata", {}))
            self.logger.info(f"✅ CONTEXT: AI response added to conversation history")
            
            # Update context manager
            context_manager.update_context(context)
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"⏱️  ORCHESTRATOR: Message processed successfully in {execution_time:.2f}s")
            
            return {
                "success": True,
                "ai_response": final_response,
                "execution_time": execution_time,
                "agents_executed": [result["agent_name"] for result in execution_results if result["success"]],
                "strategy_decision": strategy_decision.get("decision", "unknown")
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Orchestrator failed: {str(e)}"
            self.logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "execution_time": execution_time,
                "ai_response": self._create_error_response(
                    "I encountered an issue processing your request. Let me help you with a general approach - could you tell me more about your client's business challenges?",
                    error_msg
                )
            }
    
    async def _execute_agent_sequence(self, context: ConversationContext, agents_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute the sequence of agents as defined by the strategy decision.
        
        Args:
            context: Conversation context
            agents_sequence: List of agent configurations to execute
            
        Returns:
            List of agent execution results
        """
        execution_results = []
        executed_agents = {}  # Track completed agents by their IDs
        
        self.logger.info(f"🔧 AGENT SEQUENCE: Starting execution of {len(agents_sequence)} agents")
        self.logger.info(f"🔧 EXECUTED AGENTS TRACKER: {list(executed_agents.keys())}")
        
        for i, agent_config in enumerate(agents_sequence):
            agent_name = agent_config.get("agent", "")
            depends_on = agent_config.get("depends_on", [])
            
            self.logger.info(f"🔧 AGENT {i+1}/{len(agents_sequence)}: {agent_name}")
            self.logger.info(f"🔗 DEPENDENCIES: {depends_on}")
            self.logger.info(f"⚙️  CONFIG: {str(agent_config)[:150]}...")
            
            try:
                # Check if dependencies are satisfied
                if not self._dependencies_satisfied(depends_on, executed_agents):
                    self.logger.warning(f"❌ Dependencies not satisfied for {agent_name}: {depends_on}")
                    self.logger.warning(f"❌ Available agents: {list(executed_agents.keys())}")
                    continue
                
                # Execute the agent
                self.logger.info(f"▶️  EXECUTING: {agent_name}...")
                agent_result = await self._execute_single_agent(context, agent_config)
                
                execution_results.append(agent_result)
                
                # Log execution result
                if agent_result["success"]:
                    self.logger.info(f"✅ SUCCESS: {agent_name} completed successfully")
                    self.logger.info(f"📊 OUTPUT: {str(agent_result.get('output', {}))[:100]}...")
                else:
                    self.logger.error(f"❌ FAILED: {agent_name} - {agent_result.get('error', 'Unknown error')}")
                
                # Track successful executions
                if agent_result["success"]:
                    # Use search_id for RAG agents, service name for scoping, or agent name for others
                    agent_id = (agent_config.get("search_id") or 
                               agent_config.get("scope_focus") or 
                               agent_name)
                    executed_agents[agent_id] = agent_result
                    
                    # Also track by generic agent name for dependency resolution
                    if agent_name == "scoping_agent":
                        executed_agents["scoping_agent"] = agent_result
                    elif agent_name == "rag_agent" and "search_id" in agent_config:
                        executed_agents[agent_config["search_id"]] = agent_result
                    
                    self.logger.info(f"📋 TRACKED AS: {agent_id}")
                    self.logger.info(f"📋 EXECUTED AGENTS NOW: {list(executed_agents.keys())}")
                
            except Exception as e:
                self.logger.error(f"Failed to execute agent {agent_config}: {e}")
                execution_results.append({
                    "success": False,
                    "agent_name": agent_config.get("agent", "unknown"),
                    "error": str(e)
                })
        
        return execution_results
    
    def _dependencies_satisfied(self, depends_on: List[str], executed_agents: Dict[str, Any]) -> bool:
        """Check if all dependencies have been executed successfully."""
        
        if not depends_on:
            return True
        
        for dependency in depends_on:
            if dependency not in executed_agents:
                return False
            
            if not executed_agents[dependency]["success"]:
                return False
        
        return True
    
    async def _execute_single_agent(self, context: ConversationContext, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single agent based on its configuration.
        
        Args:
            context: Conversation context
            agent_config: Agent configuration from strategy decision
            
        Returns:
            Agent execution result
        """
        agent_name = agent_config.get("agent", "")
        
        try:
            if agent_name == "rag_agent":
                result = await self.rag_agent.process(context, agent_config)
                
            elif agent_name == "scoping_agent":
                result = await self.scoping_agent.process(context, agent_config)
                
            elif agent_name == "summarizing_agent":
                result = await self.summarizing_agent.process(context, agent_config)
                
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            return {
                "success": result.success,
                "agent_name": agent_name,
                "content": result.content,
                "confidence": result.confidence,
                "execution_time": result.execution_time,
                "error": result.error
            }
            
        except Exception as e:
            self.logger.error(f"Agent {agent_name} execution failed: {e}")
            return {
                "success": False,
                "agent_name": agent_name,
                "error": str(e)
            }
    
    def _generate_final_response(self, context: ConversationContext, strategy_decision: Dict[str, Any], execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate the final response based on strategy decision and agent execution results.
        
        Args:
            context: Conversation context
            strategy_decision: Strategy agent's decision
            execution_results: Results from all executed agents
            
        Returns:
            Final response dictionary
        """
        
        # Find the summarizing agent result (should be the last one)
        summarizing_result = None
        for result in reversed(execution_results):
            if result["agent_name"] == "summarizing_agent" and result["success"]:
                summarizing_result = result
                break
        
        if summarizing_result:
            # Use the summarizing agent's response
            content = summarizing_result["content"]
            
            # Handle different response types
            recommended_services = content.get("recommended_services", [])
            
            # For service_estimates response type, convert service_estimates to recommended_services format
            if content.get("response_type") == "service_estimates":
                service_estimates = content.get("service_estimates", [])
                recommended_services = []
                for estimate in service_estimates:
                    recommended_services.append({
                        "service_name": estimate.get("service_name", ""),
                        "description": "Detailed service estimates",
                        "refined_estimates": estimate.get("refined_estimates", {}),
                        "baseline_estimates": estimate.get("refined_estimates", {}),  # For frontend compatibility
                        "scope_assumptions": estimate.get("scope_assumptions", []),
                        "next_steps": estimate.get("next_steps", [])
                    })
            
            return {
                "content": content.get("consultant_message", "I'm here to help you with your client consultation."),
                "type": content.get("response_type", "conversational"),
                "metadata": {
                    "strategy_decision": strategy_decision.get("decision", "unknown"),
                    "agents_executed": [r["agent_name"] for r in execution_results if r["success"]],
                    "confidence": summarizing_result["confidence"],
                    "recommended_services": recommended_services,
                    "conversation_guidance": content.get("conversation_guidance", ""),
                    "suggested_probes": content.get("suggested_probes", []),
                    "business_focus": content.get("business_focus", "")
                }
            }
        
        else:
            # Fallback: create response based on available information
            successful_results = [r for r in execution_results if r["success"]]
            
            if successful_results:
                return {
                    "content": "I've analyzed the available information. Let me gather a bit more context to provide you with the best service recommendations for your client.",
                    "type": "conversational",
                    "metadata": {
                        "strategy_decision": strategy_decision.get("decision", "unknown"),
                        "agents_executed": [r["agent_name"] for r in successful_results],
                        "confidence": 0.6,
                        "fallback_used": True
                    }
                }
            
            else:
                return {
                    "content": "I'd like to help you identify the right D&T services for your client. Could you tell me more about their business situation? For example, what industry they're in and what challenges they're facing?",
                    "type": "conversational",
                    "metadata": {
                        "strategy_decision": strategy_decision.get("decision", "unknown"),
                        "agents_executed": [],
                        "confidence": 0.4,
                        "all_agents_failed": True
                    }
                }
    
    def _create_error_response(self, message: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Create an error response that's still helpful to the consultant."""
        
        return {
            "content": message,
            "type": "conversational",
            "metadata": {
                "error_occurred": True,
                "error_message": error,
                "confidence": 0.3,
                "suggested_next_steps": [
                    "Provide more details about the client's industry",
                    "Describe specific business challenges they're facing",
                    "Share what's driving their need for change"
                ]
            }
        }
    
    async def generate_analysis_report(self, session_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report for the conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Comprehensive analysis report
        """
        try:
            context = context_manager.get_context(session_id)
            
            if not context.conversation_history:
                return {
                    "success": False,
                    "error": "No conversation history available for analysis"
                }
            
            # Create analysis report
            report = {
                "success": True,
                "session_id": session_id,
                "conversation_summary": self._create_conversation_summary(context),
                "client_analysis": self._create_client_analysis(context),
                "service_recommendations": self._create_service_summary(context),
                "scoping_analysis": self._create_scoping_summary(context),
                "next_steps": self._create_next_steps(context),
                "generated_at": time.time()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate analysis report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_conversation_summary(self, context: ConversationContext) -> Dict[str, Any]:
        """Create a summary of the conversation."""
        
        return {
            "total_messages": len(context.conversation_history),
            "conversation_phase": context.current_phase,
            "duration": "Active session",
            "key_topics_discussed": list(context.discovered_services.keys()) if context.discovered_services else []
        }
    
    def _create_client_analysis(self, context: ConversationContext) -> Dict[str, Any]:
        """Create client analysis from context."""
        
        return {
            "client_context": context.client_context,
            "business_context": context.business_context,
            "pain_points": context.pain_points,
            "analysis_confidence": "High" if (context.client_context and context.pain_points) else "Medium"
        }
    
    def _create_service_summary(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Create summary of recommended services."""
        
        services = []
        
        for search_id, rag_result in context.rag_results.items():
            for service in rag_result.get("relevant_services", []):
                services.append({
                    "service_name": service.get("service_name", ""),
                    "relevance_score": service.get("relevance_score", 0),
                    "description": service.get("description", ""),
                    "source": f"RAG Search {search_id}"
                })
        
        return services
    
    def _create_scoping_summary(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Create summary of scoping analysis."""
        
        scoping_summary = []
        
        for service_name, scoping_data in context.scoping_results.items():
            scoping_summary.append({
                "service_name": service_name,
                "refined_estimates": scoping_data.get("refined_estimates", {}),
                "scope_rationale": scoping_data.get("scope_rationale", ""),
                "confidence": scoping_data.get("confidence", 0)
            })
        
        return scoping_summary
    
    def _create_next_steps(self, context: ConversationContext) -> List[str]:
        """Create recommended next steps."""
        
        next_steps = []
        
        if context.scoping_results:
            next_steps.append("Schedule discovery workshops for recommended services")
            next_steps.append("Prepare detailed proposals based on scoped estimates")
        
        if context.rag_results:
            next_steps.append("Present service recommendations to client")
            next_steps.append("Gather additional requirements for detailed scoping")
        
        if not next_steps:
            next_steps = [
                "Continue gathering client context and requirements",
                "Identify specific business challenges and pain points",
                "Determine client priorities and timeline"
            ]
        
        return next_steps

# Global orchestrator instance
orchestrator = Orchestrator()
