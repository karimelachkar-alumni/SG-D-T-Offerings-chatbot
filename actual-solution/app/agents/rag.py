"""
RAG Agent - Knowledge Base Search and Information Extraction

This agent searches the D&T knowledge base to find relevant services and extract
baseline estimates (pricing, team size, duration) for client situations.
"""

import json
import time
from typing import Dict, Any, List
from app.core.base_agent import BaseAgent, ConversationContext, AgentResponse
from app.rag.vector_store import vector_store

class RAGAgent(BaseAgent):
    """
    RAG Agent that searches the knowledge base and extracts service information
    and baseline estimates for client situations.
    """
    
    def __init__(self):
        super().__init__("rag_agent")
        self.d_and_t_services = [
            "Strategy & Design: Cloud",
            "Strategy & Design: Digital",
            "Strategy & Design: AI & Data",
            "Strategy & Design: Cybersecurity",
            "Strategy & Design: Enterprise Architecture",
            "Strategy & Design: Operating Model Design",
            "Execution: Enterprise Solutions",
            "Execution: ERP",
            "Operation: Cybersecurity",
            "Operation: AMS (Application Management Services)",
            "Operation: Advisory as a Service",
            "Execution: Bespoke Solutions"
        ]
    
    async def process(self, context: ConversationContext, search_config: Dict[str, Any]) -> AgentResponse:
        """
        Search knowledge base for relevant services and extract baseline estimates.
        
        Args:
            context: Current conversation context
            search_config: Dictionary containing search_id, search_focus, etc.
        """
        start_time = time.time()
        
        search_id = search_config.get("search_id", "search_1")
        search_focus = search_config.get("search_focus", "")
        
        self.logger.info(f"🔍 RAG AGENT: Starting search for session {context.session_id}")
        self.logger.info(f"🆔 SEARCH ID: {search_id}")
        self.logger.info(f"🎯 SEARCH FOCUS: '{search_focus}'")
        self.logger.info(f"📊 CONTEXT: {len(context.conversation_history)} messages in history")
        
        try:
            # Perform semantic search
            self.logger.info(f"🔍 RAG SEARCH: Performing semantic search...")
            search_results = self._perform_semantic_search(search_focus, context)
            self.logger.info(f"📄 SEARCH RESULTS: Found {len(search_results)} documents")
            
            # Extract service information and baselines
            self.logger.info(f"🔍 RAG EXTRACTION: Extracting service information from search results...")
            extracted_info = await self._extract_service_information(search_results, search_focus, context)
            
            services_found = extracted_info["services"]
            self.logger.info(f"📋 SERVICES EXTRACTED: {len(services_found)} services identified")
            for i, service in enumerate(services_found[:3]):  # Log first 3 services
                service_name = service.get("service_name", "Unknown")
                relevance = service.get("relevance_score", 0)
                has_estimates = bool(service.get("baseline_estimates"))
                self.logger.info(f"   {i+1}. {service_name} (relevance: {relevance}, estimates: {has_estimates})")
            
            # Structure the response
            rag_response = {
                "search_id": search_id,
                "search_query": search_focus,
                "relevant_services": services_found,
                "key_insights": extracted_info["insights"],
                "confidence": extracted_info["confidence"]
            }
            
            self.logger.info(f"📊 RAG CONFIDENCE: {rag_response['confidence']}")
            self.logger.info(f"🔑 KEY INSIGHTS: {rag_response['key_insights'][:100]}...")
            
            # Store results in context for other agents
            context.rag_results[search_id] = rag_response
            self.logger.info(f"💾 CONTEXT STORAGE: RAG results stored under key '{search_id}'")
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"⏱️  RAG AGENT: Search {search_id} completed in {execution_time:.2f}s")
            
            return AgentResponse(
                success=True,
                agent_name=self.agent_name,
                content=rag_response,
                confidence=extracted_info["confidence"],
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"RAG search failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Provide fallback response
            fallback_response = self._create_fallback_response(search_config, context)
            
            return AgentResponse(
                success=False,
                agent_name=self.agent_name,
                content=fallback_response,
                confidence=0.2,
                execution_time=execution_time,
                error=error_msg
            )
    
    def _perform_semantic_search(self, search_focus: str, context: ConversationContext, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search on the knowledge base."""
        
        try:
            # Enhance search query with context
            enhanced_query = self._enhance_search_query(search_focus, context)
            
            # Search vector store
            search_results = vector_store.search(enhanced_query, n_results=top_k)
            
            # Convert SearchResult objects to dictionaries expected by the agent
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata
                })
            
            self.logger.debug(f"Found {len(formatted_results)} results for query: {enhanced_query}")
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Semantic search failed: {e}")
            return []
    
    def _enhance_search_query(self, base_query: str, context: ConversationContext) -> str:
        """Enhance search query with conversation context."""
        
        query_parts = [base_query]
        
        # Add pain points to search context
        if context.pain_points:
            pain_point_terms = []
            for pain_point in context.pain_points:
                if isinstance(pain_point, dict):
                    pain_point_terms.append(pain_point.get("description", ""))
                else:
                    pain_point_terms.append(str(pain_point))
            
            if pain_point_terms:
                query_parts.append(" ".join(pain_point_terms))
        
        # Add business context
        if context.business_context:
            if "industry" in context.business_context:
                query_parts.append(f"industry {context.business_context['industry']}")
            
            if "company_size" in context.business_context:
                query_parts.append(f"{context.business_context['company_size']} company")
        
        enhanced_query = " ".join(query_parts)
        self.logger.debug(f"Enhanced query: {enhanced_query}")
        
        return enhanced_query
    
    async def _extract_service_information(self, search_results: List[Dict[str, Any]], search_focus: str, context: ConversationContext) -> Dict[str, Any]:
        """Extract service information and baseline estimates from search results."""
        
        if not search_results:
            return {
                "services": [],
                "insights": ["No relevant information found in knowledge base"],
                "confidence": 0.1
            }
        
        # Create extraction prompt
        extraction_prompt = self._create_extraction_prompt(search_results, search_focus, context)
        
        # Generate extraction response
        response_text = await self._generate_response(extraction_prompt, temperature=0.2)
        
        # Parse JSON response
        try:
            extraction_result = self._parse_json_response(response_text)
            
            # Validate and enhance service information
            validated_services = self._validate_service_information(extraction_result.get("relevant_services", []))
            
            return {
                "services": validated_services,
                "insights": extraction_result.get("key_insights", []),
                "confidence": min(extraction_result.get("confidence", 0.5), 1.0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse extraction response: {e}")
            
            # Fallback: create services based on search results
            fallback_services = self._create_fallback_services(search_results)
            
            return {
                "services": fallback_services,
                "insights": ["Extracted basic service information from search results"],
                "confidence": 0.3
            }
    
    def _create_extraction_prompt(self, search_results: List[Dict[str, Any]], search_focus: str, context: ConversationContext) -> str:
        """Create prompt for extracting service information from search results."""
        
        # Format search results
        results_text = "\n\n".join([
            f"Result {i+1}:\n{result.get('content', '')}\nRelevance: {result.get('score', 0):.2f}"
            for i, result in enumerate(search_results)
        ])
        
        # Context summary
        context_summary = self._summarize_conversation(context)
        
        prompt = f"""
{self.system_prompt}

## Search Focus:
{search_focus}

## Search Results from Knowledge Base:
{results_text}

## Client Context:
{context_summary}

## Task:
Analyze the search results and extract information about D&T services that are relevant to the search focus and client context.

For each relevant service:
1. Use the exact D&T service name from this list: {', '.join(self.d_and_t_services)}
2. Extract or estimate baseline pricing ranges, team sizes, and durations
3. Identify complexity factors that affect scope
4. Provide relevance score based on client needs

Focus on extracting quantitative baselines (costs, timelines, resources) that can be refined by the scoping agent later.

Respond with valid JSON following your specified format.
"""
        
        return prompt
    
    def _validate_service_information(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance service information."""
        
        validated_services = []
        
        for service in services:
            # Ensure service has required fields
            if "service_name" not in service:
                continue
            
            # Validate service name against known D&T services
            service_name = service["service_name"]
            if not any(dt_service.lower() in service_name.lower() or service_name.lower() in dt_service.lower() 
                      for dt_service in self.d_and_t_services):
                # Try to map to closest D&T service
                service_name = self._map_to_dt_service(service_name)
                service["service_name"] = service_name
            
            # Ensure baseline estimates structure
            if "baseline_estimates" not in service:
                service["baseline_estimates"] = {}
            
            baseline = service["baseline_estimates"]
            
            # Add default estimates if missing
            if "pricing_range" not in baseline:
                baseline["pricing_range"] = "To be determined based on scope"
            
            if "team_size" not in baseline:
                baseline["team_size"] = "2-5 consultants"
            
            if "duration" not in baseline:
                baseline["duration"] = "3-6 months"
            
            if "complexity_factors" not in baseline:
                baseline["complexity_factors"] = ["Client size", "Integration complexity", "Timeline requirements"]
            
            # Ensure relevance score
            if "relevance_score" not in service:
                service["relevance_score"] = 0.7
            
            validated_services.append(service)
        
        return validated_services
    
    def _map_to_dt_service(self, service_name: str) -> str:
        """Map a generic service name to the closest D&T service."""
        
        service_lower = service_name.lower()
        
        # Keyword mapping to actual D&T services
        if any(keyword in service_lower for keyword in ["cloud", "infrastructure", "aws", "azure"]):
            return "Strategy & Design: Cloud"
        
        elif any(keyword in service_lower for keyword in ["data", "analytics", "ai", "ml", "machine learning"]):
            return "Strategy & Design: AI & Data"
        
        elif any(keyword in service_lower for keyword in ["digital", "automation", "process", "workflow"]):
            return "Strategy & Design: Digital"
        
        elif any(keyword in service_lower for keyword in ["security", "cybersecurity", "cyber"]):
            return "Strategy & Design: Cybersecurity"
        
        elif any(keyword in service_lower for keyword in ["enterprise", "architecture", "system"]):
            if any(keyword in service_lower for keyword in ["sap", "erp", "enterprise resource"]):
                return "Execution: ERP"
            else:
                return "Strategy & Design: Enterprise Architecture"
        
        elif any(keyword in service_lower for keyword in ["operating model", "business model", "operating"]):
            return "Strategy & Design: Operating Model Design"
        
        elif any(keyword in service_lower for keyword in ["implementation", "development", "build", "custom"]):
            if any(keyword in service_lower for keyword in ["enterprise", "large"]):
                return "Execution: Enterprise Solutions"
            else:
                return "Execution: Bespoke Solutions"
        
        elif any(keyword in service_lower for keyword in ["operation", "support", "maintenance", "ams"]):
            if any(keyword in service_lower for keyword in ["application", "app"]):
                return "Operation: AMS (Application Management Services)"
            elif any(keyword in service_lower for keyword in ["security", "cyber"]):
                return "Operation: Cybersecurity"
            else:
                return "Operation: Advisory as a Service"
        
        # Default fallback
        return "Strategy & Design: Cloud"
    
    def _create_fallback_services(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback service information when LLM extraction fails."""
        
        if not search_results:
            return []
        
        # Simple keyword-based service detection
        services = []
        
        for result in search_results:
            content = result.get("content", "").lower()
            
            # Try to identify service type from content
            if "cloud" in content:
                services.append({
                    "service_name": "Strategy & Design: Cloud",
                    "relevance_score": result.get("score", 0.5),
                    "description": "Cloud transformation services identified from search results",
                    "baseline_estimates": {
                        "pricing_range": "To be determined",
                        "team_size": "3-6 consultants",
                        "duration": "4-8 months",
                        "complexity_factors": ["Current infrastructure", "Migration complexity"]
                    }
                })
            
            elif "data" in content or "analytics" in content:
                services.append({
                    "service_name": "Strategy & Design: AI & Data",
                    "relevance_score": result.get("score", 0.5),
                    "description": "Data and analytics services identified from search results",
                    "baseline_estimates": {
                        "pricing_range": "To be determined",
                        "team_size": "2-5 consultants",
                        "duration": "3-6 months",
                        "complexity_factors": ["Data volume", "Integration requirements"]
                    }
                })
        
        # Ensure at least one service with proper baseline estimates
        if not services:
            # Create comprehensive fallback services for banking/legacy scenarios
            services = [
                {
                    "service_name": "Strategy & Design: Cloud",
                    "relevance_score": 0.8,
                    "description": "Legacy system modernization and cloud migration strategy for scalable banking infrastructure",
                    "baseline_estimates": {
                        "pricing_range": "$150K - $500K depending on complexity",
                        "team_size": "4-8 consultants (architects, engineers, project managers)",
                        "duration": "6-12 months for full transformation",
                        "complexity_factors": ["Legacy system complexity", "Data migration scope", "Regulatory compliance", "Integration requirements"]
                    }
                },
                {
                    "service_name": "Execution: Bespoke Solutions",
                    "relevance_score": 0.7,
                    "description": "Custom application development for modern account opening and data processing systems",
                    "baseline_estimates": {
                        "pricing_range": "$200K - $800K for enterprise applications",
                        "team_size": "3-6 developers plus architects",
                        "duration": "4-8 months development cycle",
                        "complexity_factors": ["Feature complexity", "Integration points", "Performance requirements", "Security standards"]
                    }
                },
                {
                    "service_name": "Strategy & Design: AI & Data",
                    "relevance_score": 0.6,
                    "description": "Modern data architecture and processing solutions for banking operations",
                    "baseline_estimates": {
                        "pricing_range": "$100K - $400K for data platform",
                        "team_size": "2-5 data engineers and architects",
                        "duration": "3-6 months implementation",
                        "complexity_factors": ["Data volume", "Real-time requirements", "Compliance needs", "Integration complexity"]
                    }
                }
            ]
        
        # Ensure all services have proper baseline estimates
        for service in services:
            if "baseline_estimates" not in service or not service["baseline_estimates"]:
                service["baseline_estimates"] = {
                    "pricing_range": "$50K - $300K (varies by scope)",
                    "team_size": "2-5 consultants",
                    "duration": "3-6 months",
                    "complexity_factors": ["Client size", "Technical complexity", "Timeline requirements"]
                }
        
        return services[:3]  # Limit to top 3
    
    def _create_fallback_response(self, search_config: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Create fallback response when RAG search completely fails."""
        
        search_id = search_config.get("search_id", "search_1")
        
        return {
            "search_id": search_id,
            "search_query": search_config.get("search_focus", "general search"),
            "relevant_services": [
                {
                    "service_name": "Strategy & Design: Cloud",
                    "relevance_score": 0.3,
                    "description": "General cloud strategy services (fallback)",
                    "baseline_estimates": {
                        "pricing_range": "To be determined based on requirements",
                        "team_size": "2-4 consultants",
                        "duration": "2-4 months",
                        "complexity_factors": ["Business requirements", "Technical complexity", "Timeline constraints"]
                    }
                }
            ],
            "key_insights": ["Search failed - using fallback service recommendation"],
            "confidence": 0.2
        }
