"""
Baseline Estimates Data

Direct lookup table for D&T service baseline estimates.
Replace the BASELINE_ESTIMATES dictionary below with your table data.
"""

# Replace this dictionary with your table data
# Format: service_name -> list of tiers with estimates
BASELINE_ESTIMATES = {
    "Strategy & Design: Cloud": [
        {
            "tier": "Tier 1: Focused Strategy",
            "price_range": "$75,000 - $200,000",
            "team_size": "2-4 people",
            "duration": "4-8 weeks",
            "description": "A focused strategy for an SMB, single department, or limited scope."
        },
        {
            "tier": "Tier 2: Comprehensive Strategy",
            "price_range": "$200,000 - $600,000",
            "team_size": "5-12+ people",
            "duration": "3-7 months",
            "description": "A comprehensive strategy for mid-market clients, including detailed financial and security planning."
        },
        {
            "tier": "Tier 3: Enterprise Transformation Roadmap",
            "price_range": "$600,000 - $2,500,000+",
            "team_size": "5-12+ people",
            "duration": "3-7 months",
            "description": "A full transformation roadmap for a large, regulated enterprise with complex legacy systems."
        }
    ],
    "Strategy & Design: Digital": [
        {
            "tier": "Tier 1: Functional Optimization",
            "price_range": "$150,000 - $400,000",
            "team_size": "3-5 people",
            "duration": "2-4 months",
            "description": "A focused strategy for functional optimization, such as digital marketing or supply chain."
        },
        {
            "tier": "Tier 2: Comprehensive Experience Strategy",
            "price_range": "$400,000 - $900,000",
            "team_size": "6-15+ people",
            "duration": "5-9 months",
            "description": "An end-to-end customer or employee journey transformation strategy."
        },
        {
            "tier": "Tier 3: Enterprise Business Model Transformation",
            "price_range": "$900,000 - $3,000,000+",
            "team_size": "6-15+ people",
            "duration": "5-9 months",
            "description": "A full business model transformation, including launching new digital businesses."
        }
    ],
    "Strategy & Design: AI & Data": [
        {
            "tier": "Tier 1: Foundational Data Strategy",
            "price_range": "$200,000 - $500,000",
            "team_size": "3-6 people",
            "duration": "3-5 months",
            "description": "A foundational strategy covering data governance, BI, and a roadmap for a single department."
        },
        {
            "tier": "Tier 2: Predictive AI Strategy",
            "price_range": "$500,000 - $1,200,000",
            "team_size": "7-15+ people",
            "duration": "6-12 months",
            "description": "A strategy and business case for a core predictive model like customer churn or demand forecasting."
        },
        {
            "tier": "Tier 3: Enterprise AI Transformation Strategy",
            "price_range": "$1,200,000 - $5,000,000+",
            "team_size": "7-15+ people",
            "duration": "6-12 months",
            "description": "A multi-year roadmap for becoming an AI-driven enterprise, including generative AI and a full governance model."
        }
    ],
    "Strategy & Design: Cybersecurity": [
        {
            "tier": "Tier 1: Compliance Readiness",
            "price_range": "$150,000 - $450,000",
            "team_size": "3-5 people",
            "duration": "2-4 months",
            "description": "An NCA ECC gap analysis and roadmap for a medium-sized enterprise."
        },
        {
            "tier": "Tier 2: Comprehensive Security Program",
            "price_range": "$450,000 - $1,000,000",
            "team_size": "6-12+ people",
            "duration": "5-9 months",
            "description": "A full risk assessment, governance design, and 3-year roadmap for a large enterprise."
        },
        {
            "tier": "Tier 3: Critical Infrastructure Strategy",
            "price_range": "$1,000,000 - $4,000,000+",
            "team_size": "6-12+ people",
            "duration": "5-9 months",
            "description": "An advanced strategy for a high-risk entity, including threat modeling and red teaming."
        }
    ],
    "Strategy & Design: Enterprise Architecture": [
        {
            "tier": "Tier 1: Domain Architecture",
            "price_range": "$250,000 - $600,000",
            "team_size": "3-5 people",
            "duration": "3-5 months",
            "description": "An 'as-is' assessment and 'to-be' design for the application portfolio of a single division."
        },
        {
            "tier": "Tier 2: Comprehensive Business Unit EA",
            "price_range": "$600,000 - $1,500,000",
            "team_size": "6-10+ people",
            "duration": "6-12 months",
            "description": "A complete Business, Data, Application, and Technology blueprint for a single business unit."
        },
        {
            "tier": "Tier 3: Full Enterprise Transformation Blueprint",
            "price_range": "$1,500,000 - $5,000,000+",
            "team_size": "6-10+ people",
            "duration": "6-12 months",
            "description": "A multi-year enterprise architecture roadmap for a large, complex organization undergoing a major transformation."
        }
    ],
    "Strategy & Design: Operating Model Design": [
        {
            "tier": "Tier 1: Functional Redesign",
            "price_range": "$300,000 - $700,000",
            "team_size": "3-5 people",
            "duration": "3-5 months",
            "description": "Redesigning the operating model for a single function like IT or Finance."
        },
        {
            "tier": "Tier 2: Business Unit TOM",
            "price_range": "$700,000 - $1,800,000",
            "team_size": "6-12+ people",
            "duration": "6-12 months",
            "description": "Designing a new Target Operating Model (TOM) for a specific business unit or geography."
        },
        {
            "tier": "Tier 3: Enterprise Transformation Model",
            "price_range": "$1,800,000 - $6,000,000+",
            "team_size": "6-12+ people",
            "duration": "6-12 months",
            "description": "A complete redesign for a large enterprise driven by a merger, acquisition, or major strategic pivot."
        }
    ],
    "Execution: Enterprise Solutions": [
        {
            "tier": "Tier 1: Single-Module Cloud",
            "price_range": "$400,000 - $1,000,000",
            "team_size": "5-10 people",
            "duration": "4-7 months",
            "description": "Implementing a core HR or Finance cloud module for a mid-sized company."
        },
        {
            "tier": "Tier 2: Multi-Module Cloud",
            "price_range": "$1,000,000 - $5,000,000",
            "team_size": "15-50+ people",
            "duration": "9-24+ months",
            "description": "Implementing Finance and Supply Chain for a large enterprise."
        },
        {
            "tier": "Tier 3: Complex Transformation",
            "price_range": "$5,000,000 - $20,000,000+",
            "team_size": "15-50+ people",
            "duration": "9-24+ months",
            "description": "A multi-module implementation with heavy customization, complex integrations, and a global rollout."
        }
    ],
    "Execution: ERP": [
        {
            "tier": "Tier 1: Core Process Unification",
            "price_range": "$800,000 - $2,500,000",
            "team_size": "10-20 people",
            "duration": "7-12 months",
            "description": "Cloud ERP implementation for Finance & HR with minimal customization."
        },
        {
            "tier": "Tier 2: Multi-Function Integration",
            "price_range": "$2,500,000 - $8,000,000",
            "team_size": "30-100+ people",
            "duration": "15-30+ months",
            "description": "Integrating Finance, HR, and Supply Chain with moderate Business Process Re-engineering (BPR)."
        },
        {
            "tier": "Tier 3: Full Enterprise Transformation",
            "price_range": "$8,000,000 - $30,000,000+",
            "team_size": "30-100+ people",
            "duration": "15-30+ months",
            "description": "A global, single-instance ERP rollout with heavy BPR and complex data migration."
        }
    ],
    "Operation: Cybersecurity": [
        {
            "tier": "Tier 1: Endpoint MDR",
            "price_range": "$15,000 - $40,000 per month",
            "team_size": "Shared SOC Team",
            "duration": "4-10 weeks to go-live",
            "description": "Monitoring 250-1,000 laptops and servers with a standard SLA."
        },
        {
            "tier": "Tier 2: Expanded MDR",
            "price_range": "$40,000 - $100,000 per month",
            "team_size": "Shared SOC Team",
            "duration": "4-10 weeks to go-live",
            "description": "Includes endpoints plus cloud infrastructure and network monitoring for a mid-sized enterprise."
        },
        {
            "tier": "Tier 3: Comprehensive SOC-as-a-Service",
            "price_range": "$100,000 - $300,000+ per month",
            "team_size": "Shared SOC Team",
            "duration": "4-10 weeks to go-live",
            "description": "A fully outsourced security operations function with strict SLAs and proactive threat hunting."
        }
    ],
    "Operation: AMS (Application Management Services)": [
        {
            "tier": "Tier 1: Single Application Support",
            "price_range": "$20,000 - $60,000 per month",
            "team_size": "Shared Team",
            "duration": "5-10 weeks to go-live",
            "description": "Supporting a single, standard cloud application like Salesforce for a mid-sized company."
        },
        {
            "tier": "Tier 2: Application Portfolio Support",
            "price_range": "$60,000 - $150,000 per month",
            "team_size": "Shared Team",
            "duration": "5-10 weeks to go-live",
            "description": "Supporting a suite of 3-5 standard applications like an ERP and CRM."
        },
        {
            "tier": "Tier 3: Complex & Custom Application Management",
            "price_range": "$150,000 - $400,000+ per month",
            "team_size": "Shared Team",
            "duration": "5-10 weeks to go-live",
            "description": "Supporting a large, complex portfolio including legacy and custom-built applications with strict 24/7 SLAs."
        }
    ],
    "Operation: Advisory as a Service": [
        {
            "tier": "Tier 1: Senior Advisor Retainer",
            "price_range": "$10,000 - $25,000 per month",
            "team_size": "Single Advisor",
            "duration": "6-18 month contract",
            "description": "2-3 days per month of a senior consultant's time for project-specific guidance."
        },
        {
            "tier": "Tier 2: Partner-Level Advisory",
            "price_range": "$25,000 - $60,000 per month",
            "team_size": "Single Advisor",
            "duration": "6-18 month contract",
            "description": "4-6 days per month of a partner's time for strategic planning and executive coaching."
        },
        {
            "tier": "Tier 3: Expert Council / Fractional Executive",
            "price_range": "$60,000 - $120,000+ per month",
            "team_size": "Single Advisor (+ optional support)",
            "duration": "6-18 month contract",
            "description": "A significant time commitment from a top-tier expert to fill a key leadership gap or guide a major transformation."
        }
    ],
    "Execution: Bespoke Solutions": [
        {
            "tier": "Tier 1: Departmental Solution",
            "price_range": "$250,000 - $750,000",
            "team_size": "4-7 people",
            "duration": "3-6 months",
            "description": "An internal tool to automate a specific business process."
        },
        {
            "tier": "Tier 2: Core Business Application",
            "price_range": "$750,000 - $2,500,000",
            "team_size": "8-20+ people",
            "duration": "8-18+ months",
            "description": "A custom application to manage a core business function not served by off-the-shelf software."
        },
        {
            "tier": "Tier 3: Customer-Facing Digital Platform",
            "price_range": "$2,500,000 - $10,000,000+",
            "team_size": "8-20+ people",
            "duration": "8-18+ months",
            "description": "A large-scale, highly available, and secure platform that serves as a primary interface for customers."
        }
    ]
}
