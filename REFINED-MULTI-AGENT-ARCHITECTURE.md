# 🎯 **Refined Multi-Agent System Architecture**

## **System Overview**

A consultant (non-technical) inputs unstructured client data → AI system analyzes and recommends D&T services with pricing/scoping using **conversational context**, **standardized JSON communication**, and **ChromaDB** for memory management.

**Current Implementation Status:** ✅ **FULLY IMPLEMENTED** - All 4 core agents operational with real-time processing.

---

## **🔄 Complete Flow Diagram with Context & Pipeline**

```
┌─────────────────┐
│   CONSULTANT    │ ──┐
│ (Non-Technical) │   │ Types unstructured
└─────────────────┘   │ client data
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│               CONTEXT MANAGER                           │
│                    (ChromaDB)                           │
│                                                         │
│ • Retrieves conversation history                        │
│ • Injects previous context into current query           │
│ • Maintains session-based memory                        │
│ • Resets context every new session                      │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 STRATEGY AGENT                          │
│                 (The Brain)                             │
│                                                         │
│ System Prompt: bots.yaml → strategy_agent               │
│                                                         │
│ Receives: User message + conversation context           │
│                                                         │
│ Returns (Standardized JSON):                            │
│ {                                                       │
│   "decision": "execute_pipeline",                       │
│   "consultant_hypothesis": "...",                       │
│   "agents_sequence": [...],                             │
│   "depends_on": [...]                                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              SINGLE ORCHESTRATOR                        │
│                                                         │
│ • Receives JSON instructions from Strategy Agent        │
│ • Executes agents in pipeline sequence                  │
│ • Passes JSON outputs from Agent A to Agent B           │
│ • Injects context at each step                          │
│ • Manages data flow with standardized formats           │
│ • Handles dependency management between agents          │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   RAG       │ │   SCOPING   │ │ SUMMARIZING │
│   AGENT     │ │   AGENT     │ │   AGENT     │
│             │ │             │ │             │
│ Input JSON: │ │ Input JSON: │ │ Input JSON: │
│ • Query     │ │ • Services  │ │ • RAG output│
│ • Context   │ │ • Context   │ │ • Scoping   │
│             │ │ • RAG data  │ │ • Context   │
│ Output JSON:│ │             │ │             │
│ • Services  │ │ Output JSON:│ │ Output JSON:│
│ • Fit scores│ │ • Pricing   │ │ • Final     │
│ • Rationale │ │ • Team size │ │   response  │
│             │ │ • Duration  │ │ • Summary   │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        └──── JSON ───┼──── JSON ───┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│            CONTEXT UPDATE & STORAGE                     │
│                                                         │
│ • Stores conversation turn in ChromaDB                 │
│ • Updates context with new findings                    │
│ • Prepares for next user interaction                   │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────┐
│   CONSULTANT    │ ◄── Gets intelligent, context-aware
│ (Non-Technical) │     recommendations with full details
└─────────────────┘
```

---

## **📋 Standardized JSON Communication Protocol**

### **1. Strategy Agent Input:**

```json
{
  "user_message": "Meeting with ministry of finance rep, data issues...",
  "conversation_context": {
    "session_id": "session_123",
    "conversation_history": [...],
    "client_context": {...},
    "business_context": {...},
    "pain_points": [...]
  }
}
```

### **2. Strategy Agent Output - Option A (Full Pipeline):**

```json
{
  "decision": "execute_pipeline",
  "consultant_hypothesis": "Government data issues suggest Strategy & Design: Digital + Enterprise Solutions. Need multiple RAG searches to validate, then scoping to narrow down baseline estimates.",
  "agents_sequence": [
    {
      "agent": "rag_agent",
      "search_id": "data_management_search",
      "search_focus": "government data management, financial reconciliation, process automation",
      "depends_on": []
    },
    {
      "agent": "rag_agent",
      "search_id": "implementation_search",
      "search_focus": "enterprise solutions government, system implementation, ERP financial systems",
      "depends_on": ["data_management_search"]
    },
    {
      "agent": "scoping_agent",
      "scope_focus": "Strategy & Design: Digital",
      "baseline_source": "data_management_search",
      "depends_on": ["data_management_search"]
    },
    {
      "agent": "scoping_agent",
      "scope_focus": "Execution: Enterprise Solutions",
      "baseline_source": "implementation_search",
      "depends_on": ["implementation_search"]
    },
    {
      "agent": "summarizing_agent",
      "response_type": "service_recommendations",
      "depends_on": [
        "data_management_search",
        "implementation_search",
        "scoping_agent"
      ]
    }
  ]
}
```

### **3. Strategy Agent Output - Option B (Need More Info):**

```json
{
  "decision": "gather_more_context",
  "consultant_analysis": "Query mentions 'data issues' but unclear if it's integration, quality, security, or process. Need to zone in on specific pain points.",
  "agents_sequence": [
    {
      "agent": "summarizing_agent",
      "response_type": "targeted_follow_up",
      "question_focus": "data_pain_points_clarification",
      "depends_on": []
    }
  ]
}
```

### **4. RAG Agent Input/Output (Multiple Searches):**

```json
// INPUT - Search 1 (data_management_search)
{
  "search_id": "data_management_search",
  "query": "government data management, financial reconciliation, process automation",
  "context": {
    "client": "Ministry of Finance",
    "pain_points": ["manual reconciliation", "budget tracking issues"],
    "industry": "government"
  }
}

// OUTPUT - Search 1
{
  "search_id": "data_management_search",
  "recommended_services": [
    {
      "service_name": "Strategy & Design: Digital",
      "fit_score": 0.90,
      "rationale": "Addresses process automation and data standardization",
      "pain_points_addressed": ["manual reconciliation"],
      "baseline_estimates": {
        "pricing_range": "$150K - $400K",
        "team_size": "4-8 consultants",
        "duration": "3-6 months",
        "complexity_factors": ["government compliance", "process redesign"]
      }
    }
  ],
  "knowledge_sources": ["D&T_Digital_Services.pdf", "Government_Cases.pdf"]
}

// INPUT - Search 2 (implementation_search)
{
  "search_id": "implementation_search",
  "query": "enterprise solutions government, system implementation, ERP financial",
  "context": {
    "client": "Ministry of Finance",
    "focus": "implementation after strategy phase"
  }
}

// OUTPUT - Search 2
{
  "search_id": "implementation_search",
  "recommended_services": [
    {
      "service_name": "Execution: Enterprise Solutions",
      "fit_score": 0.80,
      "rationale": "Government-grade system implementation",
      "baseline_estimates": {
        "pricing_range": "$400K - $1.2M",
        "team_size": "6-15 people",
        "duration": "6-12 months",
        "complexity_factors": ["legacy integration", "government security", "scale"]
      }
    }
  ],
  "knowledge_sources": ["Enterprise_Implementation.pdf", "Government_ERP.pdf"]
}
```

### **5. Scoping Agent Input/Output (Multiple Service Scoping):**

```json
// INPUT - Scoping 1 (Strategy & Design: Digital)
{
  "service_focus": "Strategy & Design: Digital",
  "baseline_source": "data_management_search",
  "rag_baseline": {
    "pricing_range": "$150K - $400K",
    "team_size": "4-8 consultants",
    "duration": "3-6 months",
    "complexity_factors": ["government compliance", "process redesign"]
  },
  "client_context": {
    "client": "Ministry of Finance",
    "size": "large government ministry",
    "complexity": "high regulatory requirements",
    "urgency": "medium"
  }
}

// OUTPUT - Scoping 1
{
  "service_name": "Strategy & Design: Digital",
  "refined_estimates": {
    "pricing_range": "$200K - $350K",
    "adjustment_rationale": "RAG baseline $150K-$400K → Adjusted UP for Ministry scale and government compliance requirements",
    "team_size": "5-7 consultants",
    "duration": "4-5 months",
    "complexity_factors": ["SAMA compliance", "ministry-wide impact", "stakeholder coordination"]
  },
  "confidence": 0.85,
  "key_assumptions": ["Assumes full ministry scope", "Includes compliance documentation"]
}

// INPUT - Scoping 2 (Enterprise Solutions)
{
  "service_focus": "Execution: Enterprise Solutions",
  "baseline_source": "implementation_search",
  "rag_baseline": {
    "pricing_range": "$400K - $1.2M",
    "team_size": "6-15 people",
    "duration": "6-12 months"
  },
  "client_context": {
    "client": "Ministry of Finance",
    "integration_complexity": "high - legacy financial systems",
    "security_requirements": "government-grade"
  }
}

// OUTPUT - Scoping 2
{
  "service_name": "Execution: Enterprise Solutions",
  "refined_estimates": {
    "pricing_range": "$500K - $900K",
    "adjustment_rationale": "RAG baseline $400K-$1.2M → Narrowed for mid-complexity government implementation",
    "team_size": "8-12 people",
    "duration": "8-10 months",
    "complexity_factors": ["legacy system integration", "government security protocols", "ministry-wide rollout"]
  },
  "confidence": 0.80,
  "key_assumptions": ["Phased implementation approach", "Existing IT support available"]
}
```

### **6. Summarizing Agent Input/Output:**

```json
// INPUT
{
  "rag_output": {...},
  "scoping_output": {...},
  "original_query": "Meeting with ministry...",
  "context": {...}
}

// OUTPUT
{
  "final_response": "Based on your client's data management challenges...",
  "structured_recommendations": [...],
  "next_steps": [...],
  "confidence": 0.85
}
```

---

## **🗂️ bots.yaml Configuration File**

```yaml
# System Prompts for All LLM-Powered Agents

agents:
  strategy_agent:
    role: "Senior Technical Consultant & D&T Services Expert"
    system_prompt: |
      You are a senior technical consultant and expert in Singapore D&T's 12 service offerings. Your role is to analyze client conversations and determine the optimal sequence of actions to help consultants recommend the right services.

      ## Your D&T Service Knowledge (ONLY these 12 exact services exist):
      1. **Strategy & Design: Cloud** - Cloud strategy and migration planning
      2. **Strategy & Design: Digital** - Digital transformation strategy and roadmaps
      3. **Strategy & Design: AI & Data** - AI strategy and data architecture planning
      4. **Strategy & Design: Cybersecurity** - Security strategy and risk assessment
      5. **Strategy & Design: Enterprise Architecture** - Enterprise architecture design
      6. **Strategy & Design: Operating Model Design** - Business operating model design
      7. **Execution: Enterprise Solutions** - Large-scale enterprise system implementation
      8. **Execution: ERP** - ERP system implementation and integration
      9. **Operation: Cybersecurity** - Ongoing security operations and monitoring
      10. **Operation: AMS (Application Management Services)** - Application support and maintenance
      11. **Operation: Advisory as a Service** - Ongoing advisory and consulting support
      12. **Execution: Bespoke Solutions** - Custom software development and solutions

      ## Decision Logic:
      Analyze the conversation to determine if you have sufficient context for service recommendations.

      **Execute Pipeline** when you identify:
      - **Specific business challenges** (process inefficiencies, system limitations, operational burdens)
      - **Business impact or motivation** (cost savings, efficiency gains, competitive advantage, growth enablement)
      - **Clear pain points** that D&T services can address
      - **Sufficient detail** about the client's situation

      **Provide Estimates Only** when user asks for:
      - Timeline, duration, or "how long" questions about previously recommended services
      - Cost, pricing, or "how much" questions about previously recommended services
      - Team size, resources, or "how many people" questions about previously recommended services
      - Staffing, headcount, or team composition questions about previously recommended services
      - Use ONLY scoping_agent with baseline_source: "direct_lookup" (no RAG search needed)

      **Gather More Context** only when:
      - User provides just a greeting or vague statement
      - No specific business challenges mentioned
      - Missing critical context needed for accurate recommendations

      Always provide structured JSON responses with your expert reasoning.

rag_agent:
  system_prompt: |
    You are a D&T services expert and knowledge retrieval specialist. Your job is to find relevant services AND their baseline estimates from the knowledge base.

    Process:
    1. Analyze the client's industry and specific challenges
    2. Search the knowledge base for relevant D&T services
    3. Extract baseline pricing ranges, team sizes, and duration estimates from knowledge base
    4. Score each service based on fit and relevance
    5. Provide clear rationale for each recommendation

    CRITICAL: Always extract baseline estimates when available:
    - Typical pricing ranges for this service
    - Standard team size requirements  
    - Expected duration estimates
    - Complexity factors that affect estimates

    Focus on:
    - Business impact and outcomes
    - Specific pain points each service addresses
    - Industry-specific considerations
    - Baseline estimates from knowledge base (these will be refined by Scoping Agent)
    - Realistic fit scores (don't oversell)

    Remember: Scoping Agent will narrow down your baseline estimates based on client-specific factors.

scoping_agent:
  system_prompt: |
    You are a project scoping expert for D&T services. Your job is to NARROW DOWN baseline estimates from RAG Agent based on client-specific factors.

    Your Input:
    - Baseline estimates from RAG Agent (pricing ranges, team sizes, durations)
    - Specific client context (size, industry, complexity, urgency)
    - Service being scoped

    Your Process:
    1. Take the RAG Agent's baseline estimates as your starting point
    2. Analyze client-specific complexity factors
    3. Adjust estimates UP or DOWN from baseline based on:
       - Client size (larger = more complex)
       - Industry regulations (government/finance = more complex)
       - Integration complexity (legacy systems = more time)
       - Urgency requirements (faster = more resources)
       - Geographic factors (multiple locations = more complex)

    Your Output:
    - Refined pricing ranges (narrowed from RAG baseline)
    - Adjusted team size estimates
    - Refined duration estimates  
    - Specific complexity factors for this client
    - Confidence level in estimates

    CRITICAL: Always reference the RAG baseline and explain your adjustments.
    Example: "RAG baseline: $200K-$500K → Adjusted for government complexity: $300K-$400K"

    Be realistic and conservative. Better to under-promise and over-deliver.

summarizing_agent:
  system_prompt: |
    You create final responses for non-technical consultants. You have two modes:

    ## Mode 1: Service Recommendations
    When you receive RAG + Scoping data, create professional recommendations:
    - Focus on business value and outcomes
    - Include specific service recommendations with rationale
    - Provide actionable next steps
    - Use consultant-friendly language (no technical jargon)

    ## Mode 2: Targeted Follow-up Questions
    When Strategy Agent needs more context, ask ONE specific question to clarify:
    - **data_pain_points_clarification**: "Are the data challenges more about consolidation, quality issues, or manual processes?"
    - **technology_modernization_focus**: "Is the priority system replacement, integration, or process automation?"
    - **security_scope_clarification**: "Are you dealing with compliance requirements, security incidents, or infrastructure vulnerabilities?"
    - **transformation_scope**: "Is this about customer experience, internal operations, or business model changes?"

    Always be conversational and help the consultant get the specific information needed for accurate recommendations.

    Format: Either structured recommendations OR a single focused follow-up question.
```

---

## **💾 Context Management with ChromaDB**

### **Session-Based Context:**

```python
class ConversationContextManager:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.vector_store = VectorStore()

    def get_context(self, session_id: str) -> ConversationContext:
        """Retrieve conversation context for session"""
        return ConversationContext(
            session_id=session_id,
            conversation_history=self._get_conversation_history(session_id),
            client_context=self._extract_client_context(session_id),
            business_context=self._extract_business_context(session_id),
            pain_points=self._extract_pain_points(session_id)
        )

    def update_context(self, session_id: str, new_data: dict):
        """Add new interaction to context"""
        self._store_conversation_turn(session_id, new_data)

    def reset_session(self, session_id: str):
        """Clear context for new session"""
        self._clear_session_data(session_id)
```

### **Context Injection Points:**

1. **Strategy Agent**: Gets full conversation history + client context
2. **RAG Agent**: Gets client profile + pain points + search configuration
3. **Scoping Agent**: Gets client profile + selected services + baseline estimates
4. **Summarizing Agent**: Gets everything for final synthesis + response type

---

## **🔧 Implementation Status**

### **✅ Phase 1: Core Architecture - COMPLETED**

1. ✅ Created `bots.yaml` with all system prompts
2. ✅ Implemented standardized JSON schemas
3. ✅ Refactored Strategy Agent with proper decision logic
4. ✅ Created simplified 4-agent pipeline (Strategy, RAG, Scoping, Summarizing)

### **✅ Phase 2: Context Management - COMPLETED**

1. ✅ Implemented ChromaDB integration
2. ✅ Added context injection to all agents
3. ✅ Session management and reset functionality

### **✅ Phase 3: Pipeline & Communication - COMPLETED**

1. ✅ Enhanced orchestrator for JSON pipeline execution
2. ✅ Implemented agent-to-agent data passing
3. ✅ Added dependency management between agents

### **✅ Phase 4: Testing & Refinement - COMPLETED**

1. ✅ Tested full pipeline with real scenarios
2. ✅ Refined system prompts based on outputs
3. ✅ Optimized JSON schemas and data flow

### **🚀 Current Status: PRODUCTION READY**

The system is fully operational with:

- ✅ 4 core agents working in harmony
- ✅ Real-time conversation processing
- ✅ Context-aware recommendations
- ✅ Professional consultant-friendly outputs
- ✅ Web interface with agent status tracking

---

## **✅ Success Criteria Examples**

### **Example 1: Clear Context → Full Pipeline**

**Input:** "Second meeting with ministry of finance. They mentioned their data reconciliation takes 2 weeks manually and they're losing track of budget allocations."

**Strategy Agent Analysis:**

- Client: Government (Ministry of Finance) ✓
- Pain Points: Manual reconciliation + Budget tracking issues ✓
- Expert Hypothesis: Strategy & Design: Digital (process automation) + Enterprise Solutions (system implementation)
- Decision: Execute full pipeline

**Expected Output:**

```
I see you're continuing the discussion with the Ministry of Finance about their data challenges.

Based on their manual reconciliation issues and budget tracking problems, I recommend:

1. **Strategy & Design: Digital** (90% fit)
   - Addresses data reconciliation and process automation
   - Investment range: $200K - $350K
   - Team: 5-7 consultants
   - Duration: 4-5 months
   - Rationale: Government financial processes require careful analysis and standardization

2. **Execution: Enterprise Solutions** (80% fit)
   - Implements automated reconciliation system
   - Investment range: $500K - $900K
   - Team: 8-12 people
   - Duration: 8-10 months
   - Rationale: Complex integration with existing government systems

Next steps: Present the Strategy & Design phase first to create a detailed roadmap, then propose the implementation phase based on their specific requirements and timeline.
```

### **Example 2: Vague Context → Targeted Follow-up**

**Input:** "Meeting with a bank client tomorrow. They have some technology issues."

**Strategy Agent Analysis:**

- Client: Bank (financial sector) ✓
- Pain Points: "Technology issues" (too vague) ❌
- Expert Hypothesis: Could be cybersecurity, legacy modernization, digital transformation, or data issues
- Decision: Need clarification

**Expected Output:**

```
I can help you prepare for the bank meeting. To recommend the right D&T services, I need to understand their specific technology challenges better.

Are they dealing with:
- Legacy system modernization and integration challenges?
- Cybersecurity and compliance requirements?
- Digital customer experience improvements?
- Data management and analytics needs?

Once I know their primary focus area, I can suggest the most relevant services and typical investment ranges for banking implementations.
```

This response shows:

- ✅ **Context awareness** (remembers previous meetings)
- ✅ **Specific recommendations** with clear rationale
- ✅ **Realistic scoping** with government considerations
- ✅ **Actionable next steps** for the consultant
- ✅ **Business language** (not technical jargon)

---

## **📊 Key Improvements Achieved**

| Previous System                 | Current Architecture                    |
| ------------------------------- | --------------------------------------- |
| 6+ redundant agents             | ✅ 4 focused agents                     |
| Generic "Thank you" responses   | ✅ Intelligent, context-aware responses |
| No memory between interactions  | ✅ Full conversational context          |
| Inconsistent data formats       | ✅ Standardized JSON throughout         |
| Hardcoded prompts in code       | ✅ Centralized bots.yaml                |
| No agent-to-agent communication | ✅ Pipeline with data passing           |
| Technical language              | ✅ Business-focused consultant language |
| No real-time processing         | ✅ Real-time agent status tracking      |
| No dependency management        | ✅ Smart agent dependency resolution    |

## **🎯 Current System Capabilities**

✅ **Fully Operational Multi-Agent System** with:

- **Strategy Agent**: Intelligent decision-making and pipeline orchestration
- **RAG Agent**: Knowledge base search with baseline estimates
- **Scoping Agent**: Client-specific estimation refinement
- **Summarizing Agent**: Professional consultant communication

✅ **Real-Time Processing** with:

- Live agent status updates in web interface
- Dependency management between agents
- Context-aware conversation flow
- Professional business recommendations

✅ **Production-Ready Features**:

- Session-based context management
- ChromaDB vector storage
- Standardized JSON communication
- Web interface with agent visualization

This architecture delivers **exactly what you need**: a true multi-agent system that helps non-technical consultants have intelligent conversations and make specific D&T service recommendations! 🚀
