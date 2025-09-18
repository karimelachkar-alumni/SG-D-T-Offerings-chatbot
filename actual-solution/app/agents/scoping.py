"""
Scoping Agent - Project Scoping and Estimation Refinement

This agent takes baseline estimates from RAG searches and refines them based on
client-specific factors like company size, industry complexity, and technical maturity.
"""

import json
import time
from typing import Dict, Any, Optional
from app.core.base_agent import BaseAgent, ConversationContext, AgentResponse
from app.core.baseline_estimates import baseline_estimates_manager

class ScopingAgent(BaseAgent):
    """
    Scoping Agent that refines baseline estimates from RAG searches based on
    client-specific complexity factors and business context.
    """
    
    def __init__(self):
        super().__init__("scoping_agent")
        
        # Complexity multipliers for different factors
        self.complexity_multipliers = {
            "client_size": {
                "startup": 0.7,
                "sme": 1.0, 
                "enterprise": 1.5,
                "large_enterprise": 2.0
            },
            "industry_complexity": {
                "low": 0.9,
                "medium": 1.0,
                "high": 1.3,
                "regulated": 1.6
            },
            "technical_maturity": {
                "modern": 0.8,
                "mixed": 1.0,
                "legacy": 1.4,
                "very_legacy": 1.8
            },
            "urgency": {
                "standard": 1.0,
                "urgent": 1.2,
                "critical": 1.5
            }
        }
    
    async def process(self, context: ConversationContext, scoping_config: Dict[str, Any]) -> AgentResponse:
        """
        Refine baseline estimates based on client-specific factors.
        
        Args:
            context: Current conversation context
            scoping_config: Dictionary containing scope_focus, baseline_source, etc.
        """
        start_time = time.time()
        
        try:
            service_name = scoping_config.get("scope_focus", "")
            baseline_source = scoping_config.get("baseline_source", "")
            
            self.logger.info(f"Scoping service: {service_name} using baseline from {baseline_source}")
            
            # Get baseline estimates from RAG results
            baseline_estimates = self._get_baseline_estimates(context, baseline_source, service_name)
            
            if not baseline_estimates:
                raise ValueError(f"No baseline estimates found for {service_name} from {baseline_source}")
            
            # Analyze client context factors
            client_factors = self._analyze_client_factors(context)
            
            # Refine estimates based on client factors
            refined_estimates = await self._refine_estimates(baseline_estimates, client_factors, context)
            
            # Structure the scoping response
            scoping_response = {
                "service_name": service_name,
                "baseline_source": baseline_source,
                "client_context_factors": client_factors,
                "refined_estimates": refined_estimates.get("estimates", refined_estimates.get("refined_estimates", {})),
                "scope_rationale": refined_estimates.get("rationale", ""),
                "risk_factors": refined_estimates.get("risks", []),
                "confidence": refined_estimates.get("confidence", 0.5)
            }
            
            # Store results in context
            context.scoping_results[service_name] = scoping_response
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Scoping completed for {service_name}")
            
            return AgentResponse(
                success=True,
                agent_name=self.agent_name,
                content=scoping_response,
                confidence=refined_estimates["confidence"],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Scoping failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide fallback scoping
            fallback_response = self._create_fallback_scoping(scoping_config, context)
            
            return AgentResponse(
                success=False,
                agent_name=self.agent_name,
                content=fallback_response,
                confidence=0.3,
                execution_time=execution_time,
                error=error_msg
            )
    
    def _get_baseline_estimates(self, context: ConversationContext, baseline_source: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Get baseline estimates from direct lookup table."""
        
        # Try direct lookup first
        estimates_tiers = baseline_estimates_manager.get_baseline_estimates(service_name)
        
        if estimates_tiers:
            self.logger.info(f"Found baseline estimates for {service_name} in lookup table")
            
            # Convert tiers to a consolidated baseline estimate
            # Use the middle tier as the baseline, or create a range from all tiers
            if len(estimates_tiers) >= 2:
                # Use the middle tier (Tier 2) as baseline
                baseline_tier = estimates_tiers[1]  # Index 1 = Tier 2
            else:
                # Use the only available tier
                baseline_tier = estimates_tiers[0]
            
            return {
                "pricing_range": baseline_tier["price_range"],
                "team_size": baseline_tier["team_size"],
                "duration": baseline_tier["duration"],
                "description": baseline_tier["description"],
                "tier": baseline_tier["tier"],
                "all_tiers": estimates_tiers,  # Include all tiers for reference
                "complexity_factors": ["Client size", "Technical complexity", "Integration requirements", "Timeline constraints"]
            }
        
        # Try fuzzy search if exact match not found
        matching_services = baseline_estimates_manager.search_services(service_name)
        if matching_services:
            # Use the first match
            matched_service = matching_services[0]
            estimates_tiers = baseline_estimates_manager.get_baseline_estimates(matched_service)
            
            if estimates_tiers:
                self.logger.info(f"Found baseline estimates for {service_name} via fuzzy match: {matched_service}")
                
                # Use middle tier as baseline
                if len(estimates_tiers) >= 2:
                    baseline_tier = estimates_tiers[1]
                else:
                    baseline_tier = estimates_tiers[0]
                
                return {
                    "pricing_range": baseline_tier["price_range"],
                    "team_size": baseline_tier["team_size"],
                    "duration": baseline_tier["duration"],
                    "description": baseline_tier["description"],
                    "tier": baseline_tier["tier"],
                    "all_tiers": estimates_tiers,
                    "matched_service": matched_service,
                    "complexity_factors": ["Client size", "Technical complexity", "Integration requirements", "Timeline constraints"]
                }
        
        # Fallback: create generic baseline estimates
        self.logger.warning(f"No baseline estimates found for {service_name}, creating fallback estimates")
        return {
            "pricing_range": "$100K - $500K (varies by complexity)",
            "team_size": "3-6 consultants",
            "duration": "4-8 months",
            "complexity_factors": ["Client size", "Technical complexity", "Integration requirements", "Timeline constraints"]
        }
    
    def _analyze_client_factors(self, context: ConversationContext) -> Dict[str, Any]:
        """Analyze client context to determine scoping factors."""
        
        factors = {
            "size": "sme",  # default
            "industry": "standard",
            "complexity": "medium",
            "urgency": "standard",
            "technical_maturity": "mixed",
            "integration_needs": "moderate"
        }
        
        # Analyze client context
        if context.client_context:
            # Company size
            if "company_size" in context.client_context:
                size = context.client_context["company_size"].lower()
                if any(keyword in size for keyword in ["startup", "small"]):
                    factors["size"] = "startup"
                elif any(keyword in size for keyword in ["sme", "medium"]):
                    factors["size"] = "sme"
                elif "large" in size:
                    factors["size"] = "large_enterprise"
                elif "enterprise" in size:
                    factors["size"] = "enterprise"
            
            # Industry
            if "industry" in context.client_context:
                industry = context.client_context["industry"].lower()
                if any(keyword in industry for keyword in ["financial", "banking", "healthcare", "government"]):
                    factors["industry"] = "regulated"
                    factors["complexity"] = "high"
        
        # Analyze business context
        if context.business_context:
            # Urgency indicators
            if any(keyword in str(context.business_context).lower() 
                   for keyword in ["urgent", "asap", "immediately", "critical"]):
                factors["urgency"] = "urgent"
            
            # Technical maturity indicators
            if any(keyword in str(context.business_context).lower() 
                   for keyword in ["legacy", "old system", "mainframe"]):
                factors["technical_maturity"] = "legacy"
            elif any(keyword in str(context.business_context).lower() 
                     for keyword in ["modern", "cloud", "microservices"]):
                factors["technical_maturity"] = "modern"
        
        # Analyze pain points for complexity
        if context.pain_points:
            pain_point_text = " ".join([
                str(pp.get("description", "")) if isinstance(pp, dict) else str(pp) 
                for pp in context.pain_points
            ]).lower()
            
            if any(keyword in pain_point_text 
                   for keyword in ["integration", "multiple systems", "complex"]):
                factors["integration_needs"] = "high"
                factors["complexity"] = "high"
        
        return factors
    
    async def _refine_estimates(self, baseline_estimates: Dict[str, Any], client_factors: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Refine baseline estimates using client factors and LLM analysis."""
        
        # Create refinement prompt
        refinement_prompt = self._create_refinement_prompt(baseline_estimates, client_factors, context)
        
        # Generate refinement response
        response_text = await self._generate_response(refinement_prompt, temperature=0.2)
        
        try:
            # Parse JSON response
            refinement_result = self._parse_json_response(response_text)
            
            # Validate and enhance the refinement
            validated_refinement = self._validate_refinement(refinement_result, baseline_estimates, client_factors)
            
            return validated_refinement
            
        except Exception as e:
            self.logger.error(f"Failed to parse refinement response: {e}")
            
            # Fallback: use mathematical refinement
            return self._mathematical_refinement(baseline_estimates, client_factors)
    
    def _create_refinement_prompt(self, baseline_estimates: Dict[str, Any], client_factors: Dict[str, Any], context: ConversationContext) -> str:
        """Create prompt for estimate refinement."""
        
        context_summary = self._summarize_conversation(context)
        
        prompt = f"""
{self.system_prompt}

## Baseline Estimates to Refine:
{json.dumps(baseline_estimates, indent=2)}

## Client Context Factors:
{json.dumps(client_factors, indent=2)}

## Full Client Context:
{context_summary}

## Task:
Refine the baseline estimates based on the client-specific factors. Consider:

1. **Company Size Impact**: Larger companies typically need more governance, stakeholders, and complexity
2. **Industry Complexity**: Regulated industries require more compliance and security measures
3. **Technical Maturity**: Legacy systems increase integration complexity and timeline
4. **Urgency**: Compressed timelines may require more resources or premium rates
5. **Integration Needs**: Complex integrations significantly impact scope

## Refinement Guidelines:
- Narrow down broad ranges to specific estimates
- Explain your reasoning for each adjustment
- Consider both optimistic and realistic scenarios
- Identify key assumptions and risk factors
- Provide confidence level based on available information

Respond with valid JSON following your specified format.
"""
        
        return prompt
    
    def _validate_refinement(self, refinement: Dict[str, Any], baseline_estimates: Dict[str, Any], client_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the refinement response."""
        
        # Ensure required fields exist
        if "refined_estimates" not in refinement:
            refinement["refined_estimates"] = {}
        
        estimates = refinement["refined_estimates"]
        
        # Validate pricing range
        if "pricing_range" not in estimates:
            estimates["pricing_range"] = baseline_estimates.get("pricing_range", "To be determined")
        
        # Validate team composition
        if "team_composition" not in estimates:
            estimates["team_composition"] = baseline_estimates.get("team_size", "2-4 consultants")
        
        # Validate duration
        if "duration" not in estimates:
            estimates["duration"] = baseline_estimates.get("duration", "3-6 months")
        
        # Ensure key assumptions
        if "key_assumptions" not in estimates:
            estimates["key_assumptions"] = [
                "Standard complexity assumed",
                "Client resources available as needed",
                "No major technical blockers"
            ]
        
        # Ensure rationale
        if "scope_rationale" not in refinement:
            refinement["scope_rationale"] = "Estimates refined based on client size and industry factors"
        
        # Ensure risk factors
        if "risk_factors" not in refinement:
            refinement["risk_factors"] = [
                "Scope creep potential",
                "Resource availability",
                "Technical complexity discoveries"
            ]
        
        # Ensure confidence
        if "confidence" not in refinement:
            refinement["confidence"] = 0.7
        
        return refinement
    
    def _mathematical_refinement(self, baseline_estimates: Dict[str, Any], client_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback mathematical refinement when LLM fails."""
        
        # Calculate complexity multiplier
        total_multiplier = 1.0
        
        for factor_type, factor_value in client_factors.items():
            if factor_type in self.complexity_multipliers:
                multiplier = self.complexity_multipliers[factor_type].get(factor_value, 1.0)
                total_multiplier *= multiplier
        
        # Apply multiplier to estimates
        refined_estimates = {
            "pricing_range": self._adjust_pricing_range(baseline_estimates.get("pricing_range", ""), total_multiplier),
            "team_composition": self._adjust_team_size(baseline_estimates.get("team_size", ""), total_multiplier),
            "duration": self._adjust_duration(baseline_estimates.get("duration", ""), total_multiplier),
            "key_assumptions": [
                f"Complexity multiplier: {total_multiplier:.1f}x",
                "Standard delivery approach",
                "Client resources available"
            ]
        }
        
        return {
            "estimates": refined_estimates,
            "rationale": f"Mathematical refinement applied with {total_multiplier:.1f}x complexity factor",
            "risks": ["Estimate based on limited context", "May require adjustment after discovery"],
            "confidence": 0.6
        }
    
    def _adjust_pricing_range(self, baseline_range: str, multiplier: float) -> str:
        """Adjust pricing range with multiplier."""
        if "to be determined" in baseline_range.lower():
            return f"Estimated {multiplier:.1f}x standard rates - to be refined in discovery"
        
        return f"{baseline_range} (adjusted for complexity: {multiplier:.1f}x)"
    
    def _adjust_team_size(self, baseline_team: str, multiplier: float) -> str:
        """Adjust team size with multiplier."""
        if multiplier > 1.3:
            return f"{baseline_team} + additional specialists for complexity"
        elif multiplier < 0.8:
            return f"Streamlined team: {baseline_team}"
        else:
            return baseline_team
    
    def _adjust_duration(self, baseline_duration: str, multiplier: float) -> str:
        """Adjust duration with multiplier."""
        if multiplier > 1.3:
            return f"{baseline_duration} + buffer for complexity"
        elif multiplier < 0.8:
            return f"Accelerated timeline: {baseline_duration}"
        else:
            return baseline_duration
    
    def _create_fallback_scoping(self, scoping_config: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Create fallback scoping when everything fails."""
        
        service_name = scoping_config.get("scope_focus", "Unknown Service")
        
        return {
            "service_name": service_name,
            "baseline_source": scoping_config.get("baseline_source", "fallback"),
            "client_context_factors": {
                "size": "sme",
                "complexity": "medium",
                "urgency": "standard"
            },
            "refined_estimates": {
                "pricing_range": "To be determined in discovery phase",
                "team_composition": "2-4 consultants",
                "duration": "3-6 months",
                "key_assumptions": ["Standard complexity", "Client resources available"]
            },
            "scope_rationale": "Fallback estimates - detailed scoping required",
            "risk_factors": ["Limited context for accurate scoping", "May require significant adjustment"],
            "confidence": 0.3
        }
