"""
Summarizing Agent - Client Communication Specialist

This agent crafts consultant-friendly responses that guide conversations toward 
successful D&T service recommendations or gather targeted context through 
business-focused follow-up questions.
"""

import json
import time
from typing import Dict, Any, List
from app.core.base_agent import BaseAgent, ConversationContext, AgentResponse

class SummarizingAgent(BaseAgent):
    """
    Summarizing Agent that creates compelling business cases for D&T services
    or crafts targeted follow-up questions to gather essential context.
    """
    
    def __init__(self):
        super().__init__("summarizing_agent")
    
    async def process(self, context: ConversationContext, summarizing_config: Dict[str, Any]) -> AgentResponse:
        """
        Create consultant-friendly responses for service recommendations or follow-up questions.
        
        Args:
            context: Current conversation context
            summarizing_config: Dictionary containing response_type, question_focus, etc.
        """
        start_time = time.time()
        
        try:
            response_type = summarizing_config.get("response_type", "service_recommendations")
            
            self.logger.info(f"Generating {response_type} response")
            
            if response_type == "service_recommendations":
                summary_response = await self._create_service_recommendations(context, summarizing_config)
            elif response_type == "targeted_follow_up":
                summary_response = await self._create_targeted_follow_up(context, summarizing_config)
            elif response_type == "service_estimates":
                summary_response = await self._create_service_estimates(context, summarizing_config)
            else:
                raise ValueError(f"Unknown response type: {response_type}")
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Generated {response_type} response successfully")
            
            return AgentResponse(
                success=True,
                agent_name=self.agent_name,
                content=summary_response,
                confidence=summary_response.get("confidence", 0.8),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Summarizing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide fallback response
            fallback_response = self._create_fallback_response(summarizing_config, context)
            
            return AgentResponse(
                success=False,
                agent_name=self.agent_name,
                content=fallback_response,
                confidence=0.4,
                execution_time=execution_time,
                error=error_msg
            )
    
    async def _create_service_recommendations(self, context: ConversationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create compelling service recommendations for the consultant."""
        
        # Gather all available information
        service_data = self._gather_service_data(context)
        
        if not service_data:
            # No services found - create general advisory recommendation
            return self._create_general_advisory_response(context)
        
        # Create recommendation prompt
        recommendation_prompt = self._create_recommendation_prompt(context, service_data)
        
        # Generate recommendations
        response_text = await self._generate_response(recommendation_prompt, temperature=0.4)
        
        try:
            # Parse JSON response
            recommendations = self._parse_json_response(response_text)
            
            # Validate and enhance recommendations
            validated_recommendations = self._validate_service_recommendations(recommendations, service_data)
            
            return validated_recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to parse recommendation response: {e}")
            
            # Fallback: create structured recommendations from available data
            return self._create_structured_recommendations(service_data, context)
    
    async def _create_service_estimates(self, context: ConversationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed service estimates based on scoping results."""
        
        # Gather scoping data from context
        estimates_data = self._gather_estimates_data(context)
        
        if not estimates_data:
            # No scoping data found - create fallback estimates
            return self._create_fallback_estimates_response(context)
        
        # Create estimates prompt
        estimates_prompt = self._create_estimates_prompt(context, estimates_data)
        
        # Generate estimates response
        response_text = await self._generate_response(estimates_prompt, temperature=0.3)
        
        try:
            # Parse JSON response
            estimates = self._parse_json_response(response_text)
            
            # Validate and enhance estimates
            validated_estimates = self._validate_service_estimates(estimates, estimates_data)
            
            return validated_estimates
            
        except Exception as e:
            self.logger.error(f"Failed to parse estimates response: {e}")
            
            # Fallback: create structured estimates from available data
            return self._create_structured_estimates(estimates_data, context)
    
    async def _create_targeted_follow_up(self, context: ConversationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create targeted follow-up questions to gather specific context."""
        
        question_focus = config.get("question_focus", "business_context")
        
        # Create follow-up prompt
        follow_up_prompt = self._create_follow_up_prompt(context, question_focus)
        
        # Generate follow-up questions
        response_text = await self._generate_response(follow_up_prompt, temperature=0.5)
        
        try:
            # Parse JSON response
            follow_up = self._parse_json_response(response_text)
            
            # Validate and enhance follow-up
            validated_follow_up = self._validate_follow_up_response(follow_up, question_focus)
            
            return validated_follow_up
            
        except Exception as e:
            self.logger.error(f"Failed to parse follow-up response: {e}")
            
            # Fallback: create structured follow-up questions
            return self._create_structured_follow_up(question_focus, context)
    
    def _gather_service_data(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Gather all available service information from RAG and scoping results."""
        
        service_data = []
        
        # Collect services from RAG results
        for search_id, rag_result in context.rag_results.items():
            for service in rag_result.get("relevant_services", []):
                service_info = {
                    "service_name": service.get("service_name", ""),
                    "description": service.get("description", ""),
                    "relevance_score": service.get("relevance_score", 0.5),
                    "baseline_estimates": service.get("baseline_estimates", {}),
                    "source": f"rag_{search_id}"
                }
                
                # Check if we have scoping results for this service
                service_name = service_info["service_name"]
                if service_name in context.scoping_results:
                    scoping_data = context.scoping_results[service_name]
                    service_info["refined_estimates"] = scoping_data.get("refined_estimates", {})
                    service_info["scope_rationale"] = scoping_data.get("scope_rationale", "")
                    service_info["risk_factors"] = scoping_data.get("risk_factors", [])
                
                service_data.append(service_info)
        
        # Sort by relevance score
        service_data.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return service_data[:3]  # Top 3 services
    
    def _create_recommendation_prompt(self, context: ConversationContext, service_data: List[Dict[str, Any]]) -> str:
        """Create prompt for service recommendations."""
        
        context_summary = self._summarize_conversation(context)
        services_summary = json.dumps(service_data, indent=2)
        
        prompt = f"""
{self.system_prompt}

## Client Context:
{context_summary}

## Available Service Data:
{services_summary}

## Task:
Create compelling service recommendations that help the consultant sell D&T services effectively. Focus on:

1. **Business Value**: Clear ROI and business outcomes
2. **Client-Friendly Language**: Avoid technical jargon
3. **Investment Guidance**: Present costs as investments in business outcomes
4. **Next Steps**: Clear actions for the consultant to take
5. **Positioning Advice**: How to present these recommendations to the client

## Guidelines:
- Use the exact service names provided
- Emphasize business benefits over technical features
- Present estimates as investment ranges tied to business value
- Provide specific guidance for the consultant on positioning
- Include confidence level based on available information

Respond with valid JSON following the service_recommendations format.
"""
        
        return prompt
    
    def _create_follow_up_prompt(self, context: ConversationContext, question_focus: str) -> str:
        """Create prompt for targeted follow-up questions."""
        
        context_summary = self._summarize_conversation(context)
        
        prompt = f"""
{self.system_prompt}

## Current Context:
{context_summary}

## Follow-up Focus:
{question_focus}

## Task:
Create targeted, business-focused questions to gather the specific information needed. The questions should:

1. **Be Business-Focused**: Frame in terms of business impact and outcomes
2. **Uncover Pain Points**: Identify what problems are costing them money/time
3. **Discover Drivers**: Understand what's forcing them to act now
4. **Guide Conversation**: Lead toward service recommendations
5. **Be Consultant-Friendly**: Help non-technical consultants ask the right questions

## Guidelines:
- Ask open-ended questions that encourage detailed responses
- Focus on business impact rather than technical details
- Help identify urgency and decision-making factors
- Provide context on why this information matters for recommendations

Respond with valid JSON following the targeted_follow_up format.
"""
        
        return prompt
    
    def _validate_service_recommendations(self, recommendations: Dict[str, Any], service_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and enhance service recommendations."""
        
        # Ensure required fields
        if "response_type" not in recommendations:
            recommendations["response_type"] = "service_recommendations"
        
        if "consultant_message" not in recommendations:
            recommendations["consultant_message"] = "Based on our analysis, here are the recommended D&T services for your client:"
        
        if "recommended_services" not in recommendations:
            recommendations["recommended_services"] = []
        
        # Validate each recommended service
        validated_services = []
        for service in recommendations["recommended_services"]:
            if "service_name" not in service:
                continue
            
            # Ensure required fields
            if "business_value" not in service:
                service["business_value"] = "Addresses key business challenges and drives operational efficiency"
            
            if "estimated_scope" not in service:
                service["estimated_scope"] = {
                    "investment_range": "To be determined in discovery phase",
                    "timeline": "3-6 months",
                    "team_approach": "Dedicated consultant team"
                }
            
            if "next_steps" not in service:
                service["next_steps"] = "Schedule discovery workshop to define detailed scope"
            
            validated_services.append(service)
        
        recommendations["recommended_services"] = validated_services
        
        # Ensure guidance for consultant
        if "conversation_guidance" not in recommendations:
            recommendations["conversation_guidance"] = "Position these services as strategic investments in business transformation"
        
        # Ensure confidence
        if "confidence" not in recommendations:
            recommendations["confidence"] = 0.8
        
        return recommendations
    
    def _validate_follow_up_response(self, follow_up: Dict[str, Any], question_focus: str) -> Dict[str, Any]:
        """Validate and enhance follow-up response."""
        
        # Ensure required fields
        if "response_type" not in follow_up:
            follow_up["response_type"] = "targeted_follow_up"
        
        if "consultant_message" not in follow_up:
            follow_up["consultant_message"] = "To better understand your client's needs, could you share more details?"
        
        if "information_needed" not in follow_up:
            follow_up["information_needed"] = question_focus
        
        if "suggested_probes" not in follow_up:
            follow_up["suggested_probes"] = [
                "What specific challenges are they facing?",
                "What's driving their need for change right now?"
            ]
        
        if "business_focus" not in follow_up:
            follow_up["business_focus"] = "Understanding business impact helps identify the right services"
        
        return follow_up
    
    def _create_structured_recommendations(self, service_data: List[Dict[str, Any]], context: ConversationContext) -> Dict[str, Any]:
        """Create structured recommendations when LLM generation fails."""
        
        recommended_services = []
        
        for service in service_data[:3]:  # Top 3 services
            service_name = service.get("service_name", "D&T Advisory Service")
            
            # Use refined estimates if available, otherwise baseline
            estimates = service.get("refined_estimates", service.get("baseline_estimates", {}))
            
            recommended_service = {
                "service_name": service_name,
                "business_value": f"Addresses key business challenges with {service_name.split(':')[-1].strip()} solutions",
                "estimated_scope": {
                    "investment_range": estimates.get("pricing_range", "To be determined"),
                    "timeline": estimates.get("duration", "3-6 months"),
                    "team_approach": estimates.get("team_composition", estimates.get("team_size", "2-4 consultants"))
                },
                "next_steps": "Schedule discovery workshop to define detailed requirements and scope"
            }
            
            recommended_services.append(recommended_service)
        
        return {
            "response_type": "service_recommendations",
            "consultant_message": "Based on the client context provided, here are our recommended D&T services:",
            "recommended_services": recommended_services,
            "conversation_guidance": "Present these as strategic investments that address their specific business challenges",
            "confidence": 0.7
        }
    
    def _create_structured_follow_up(self, question_focus: str, context: ConversationContext) -> Dict[str, Any]:
        """Create structured follow-up questions when LLM generation fails."""
        
        focus_questions = {
            "business_context": [
                "What industry is your client in, and what makes their business unique?",
                "What are the main business challenges they're trying to solve?",
                "What's driving their urgency to address these issues now?"
            ],
            "pain_points": [
                "What specific problems are costing them time or money?",
                "How are these issues impacting their daily operations?",
                "What would success look like for them?"
            ],
            "priorities": [
                "What are their top 3 business priorities this year?",
                "What's their timeline for addressing these challenges?",
                "Who are the key decision makers involved?"
            ]
        }
        
        questions = focus_questions.get(question_focus, focus_questions["business_context"])
        
        return {
            "response_type": "targeted_follow_up",
            "consultant_message": f"To provide the best service recommendations, I need to understand more about {question_focus.replace('_', ' ')}. Could you share:",
            "information_needed": question_focus,
            "suggested_probes": questions,
            "business_focus": "This information helps us identify which D&T services will deliver the most value for your client"
        }
    
    def _create_general_advisory_response(self, context: ConversationContext) -> Dict[str, Any]:
        """Create general advisory response when no specific services are identified."""
        
        return {
            "response_type": "service_recommendations",
            "consultant_message": "Based on the initial context, I recommend starting with our Technology Advisory service to better understand your client's specific needs.",
            "recommended_services": [
                {
                    "service_name": "Strategy & Design: Technology Advisory",
                    "business_value": "Comprehensive assessment of technology landscape and strategic recommendations for digital transformation",
                    "estimated_scope": {
                        "investment_range": "Typically 15-25% of total project budget",
                        "timeline": "2-4 weeks for initial assessment",
                        "team_approach": "Senior consultants with industry expertise"
                    },
                    "next_steps": "Schedule initial consultation to understand business objectives and current state"
                }
            ],
            "conversation_guidance": "Position this as a strategic first step that ensures we recommend the right solutions for their specific situation",
            "confidence": 0.6
        }
    
    def _create_fallback_response(self, config: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Create fallback response when all else fails."""
        
        response_type = config.get("response_type", "service_recommendations")
        
        if response_type == "service_recommendations":
            return {
                "response_type": "service_recommendations",
                "consultant_message": "I'm here to help you recommend the right D&T services. Let me gather some additional context to provide better recommendations.",
                "recommended_services": [],
                "conversation_guidance": "Consider starting with a discovery conversation to understand their business challenges better",
                "confidence": 0.3
            }
        else:
            return {
                "response_type": "targeted_follow_up",
                "consultant_message": "To provide the best recommendations, could you tell me more about your client's business situation?",
                "information_needed": "general_context",
                "suggested_probes": [
                    "What business challenges are they facing?",
                    "What's their industry and company size?",
                    "What's driving their need for change?"
                ],
                "business_focus": "Understanding their business context helps identify the most valuable services"
            }
    
    def _gather_estimates_data(self, context: ConversationContext) -> List[Dict[str, Any]]:
        """Gather estimates data from scoping results."""
        
        estimates_data = []
        
        # Collect data from scoping results
        for service_name, scoping_result in context.scoping_results.items():
            estimates_data.append({
                "service_name": service_name,
                "refined_estimates": scoping_result.get("refined_estimates", {}),
                "scope_rationale": scoping_result.get("scope_rationale", ""),
                "confidence": scoping_result.get("confidence", 0.7),
                "risk_factors": scoping_result.get("risk_factors", [])
            })
        
        return estimates_data
    
    def _create_estimates_prompt(self, context: ConversationContext, estimates_data: List[Dict[str, Any]]) -> str:
        """Create prompt for service estimates."""
        
        context_summary = self._summarize_conversation(context)
        estimates_summary = json.dumps(estimates_data, indent=2)
        
        prompt = f"""
{self.system_prompt}

## Client Context:
{context_summary}

## Available Estimates Data:
{estimates_summary}

## Task:
Provide detailed, consultant-friendly estimates for the recommended services. Focus on:

1. **Clear Investment Ranges**: Present costs as business investments with rationale
2. **Timeline Details**: Realistic delivery schedules with key milestones  
3. **Team Structure**: Specific roles and expertise required
4. **Scope Assumptions**: Key assumptions that affect the estimates
5. **Next Steps**: Clear actions for the consultant to take

Respond with valid JSON following the service_estimates format.
"""
        
        return prompt
    
    def _validate_service_estimates(self, estimates: Dict[str, Any], estimates_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and enhance service estimates."""
        
        # Ensure required fields
        if "service_estimates" not in estimates:
            estimates["service_estimates"] = []
        
        if "consultant_message" not in estimates:
            estimates["consultant_message"] = "Here are the detailed estimates for the recommended services:"
        
        # Validate each service estimate
        for i, service_estimate in enumerate(estimates["service_estimates"]):
            if "service_name" not in service_estimate:
                service_estimate["service_name"] = f"Service {i+1}"
            
            if "refined_estimates" not in service_estimate:
                service_estimate["refined_estimates"] = {
                    "investment_range": "To be determined based on scope",
                    "timeline": "4-8 weeks typical",
                    "team_composition": "Senior consultant + specialist resources"
                }
        
        return estimates
    
    def _create_structured_estimates(self, estimates_data: List[Dict[str, Any]], context: ConversationContext) -> Dict[str, Any]:
        """Create structured estimates from available data."""
        
        service_estimates = []
        
        for estimate_data in estimates_data:
            service_estimates.append({
                "service_name": estimate_data["service_name"],
                "refined_estimates": estimate_data.get("refined_estimates", {
                    "investment_range": "Scope-dependent - typically $50K-200K",
                    "timeline": "6-12 weeks",
                    "team_composition": "Senior consultant + 2-3 specialists"
                }),
                "scope_assumptions": estimate_data.get("risk_factors", ["Standard complexity assumed"]),
                "next_steps": ["Schedule detailed scoping session", "Prepare formal proposal"]
            })
        
        return {
            "response_type": "service_estimates",
            "consultant_message": "Based on our analysis, here are the detailed estimates for the recommended services:",
            "service_estimates": service_estimates,
            "confidence": 0.75
        }
    
    def _create_fallback_estimates_response(self, context: ConversationContext) -> Dict[str, Any]:
        """Create fallback estimates when no scoping data is available."""
        
        return {
            "response_type": "service_estimates",
            "consultant_message": "I don't have specific scoping data available, but here are typical estimates for D&T services:",
            "service_estimates": [
                {
                    "service_name": "Strategy & Design Services",
                    "refined_estimates": {
                        "investment_range": "$75K - $150K",
                        "timeline": "4-8 weeks",
                        "team_composition": "Senior consultant + strategy specialist"
                    },
                    "scope_assumptions": ["Standard complexity", "Client collaboration available"],
                    "next_steps": ["Conduct detailed scoping session", "Validate assumptions with client"]
                }
            ],
            "confidence": 0.5
        }
