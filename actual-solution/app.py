#!/usr/bin/env python3
"""Flask Frontend for SG D&T AI Co-Pilot Demo."""

import os
import asyncio
import json
import logging
import time
import threading
from datetime import datetime

# Disable ChromaDB telemetry at startup
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'true'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Import our AI Co-Pilot system
from app.core.orchestrator import orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sg-dt-ai-copilot-demo-2025'
app.config['DEBUG'] = True

# Enable CORS and SocketIO
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active sessions
active_sessions = {}


@app.route('/')
def index():
    """Main chatbot interface."""
    return render_template('index.html')


@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        health_status = orchestrator.get_agent_health()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system_health": health_status
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    session_id = request.sid
    logger.info(f"Client connected: {session_id}")
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = request.sid
    logger.info(f"Client disconnected: {session_id}")
    if session_id in active_sessions:
        del active_sessions[session_id]


@socketio.on('start_consultation')
def handle_start_consultation(data):
    """Start a new consultation with the AI Co-Pilot."""
    session_id = request.sid
    client_input = data.get('message', '').strip()
    
    if not client_input:
        emit('error', {'message': 'Please provide client information to start the consultation.'})
        return
    
    logger.info(f"Starting consultation for session {session_id}")
    
    # Store session
    active_sessions[session_id] = {
        'start_time': datetime.now(),
        'client_input': client_input,
        'status': 'processing'
    }
    
    # Emit start message
    emit('consultation_started', {
        'session_id': session_id,
        'message': 'AI Co-Pilot is analyzing your client information...'
    })
    
    # Run the consultation in a separate thread to avoid event loop conflicts
    import threading
    consultation_thread = threading.Thread(
        target=run_consultation, 
        args=(session_id, client_input),
        daemon=True
    )
    consultation_thread.start()


def run_consultation(session_id, client_input):
    """Run the complete AI Co-Pilot consultation workflow."""
    import threading
    
    try:
        # Ensure we're in a clean thread with no existing event loop
        try:
            existing_loop = asyncio.get_running_loop()
            logger.warning(f"Found existing event loop in thread: {existing_loop}")
        except RuntimeError:
            # Good - no existing event loop
            pass
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info(f"Created new event loop for consultation {session_id}")
        
        # Emit workflow start
        socketio.emit('agent_update', {
            'stage': 'initialization',
            'message': '🚀 Initializing AI Co-Pilot workflow...',
            'progress': 10
        }, room=session_id)
        
        # Execute the workflow with proper error handling
        try:
            result = loop.run_until_complete(
                orchestrator.execute_workflow(
                    conversation_input=client_input,
                    conversation_id=f"demo-{session_id}",
                    presentation_type="comprehensive",
                    enable_parallel_processing=False  # Disable parallel processing to avoid loop issues
                )
            )
        except Exception as workflow_error:
            logger.error(f"Workflow execution failed: {workflow_error}")
            raise
        
        # Update session status
        if session_id in active_sessions:
            active_sessions[session_id]['status'] = 'completed' if result.success else 'failed'
            active_sessions[session_id]['result'] = result
        
        if result.success:
            # Emit agent progress updates
            progress_updates = [
                {'stage': 'strategy', 'message': '🧠 Strategy Agent: Analyzing client context and determining approach...', 'progress': 25},
                {'stage': 'rag', 'message': '🔍 RAG Agent: Searching knowledge base for relevant services...', 'progress': 50},
                {'stage': 'scoping', 'message': '💰 Scoping Agent: Refining estimates based on client context...', 'progress': 75},
                {'stage': 'summarizing', 'message': '📝 Summarizing Agent: Creating consultant-friendly response...', 'progress': 95}
            ]
            
            for update in progress_updates:
                socketio.emit('agent_update', update, room=session_id)
                socketio.sleep(0.5)  # Small delay for demo effect
            
            # Format results for display
            consultation_results = format_consultation_results(result)
            
            # Emit completion
            socketio.emit('consultation_completed', {
                'success': True,
                'execution_time': result.execution_time,
                'results': consultation_results,
                'progress': 100
            }, room=session_id)
            
        else:
            # Emit failure
            socketio.emit('consultation_failed', {
                'success': False,
                'error': result.error_message,
                'stage': result.stage.value if result.stage else 'unknown'
            }, room=session_id)
            
    except Exception as e:
        logger.error(f"Consultation failed for session {session_id}: {e}")
        socketio.emit('consultation_failed', {
            'success': False,
            'error': str(e),
            'stage': 'execution_error'
        }, room=session_id)
    
    finally:
        # Clean up the event loop
        try:
            current_loop = asyncio.get_event_loop()
            if current_loop and not current_loop.is_closed():
                logger.info(f"Closing event loop for session {session_id}")
                current_loop.close()
        except Exception as cleanup_error:
            logger.warning(f"Error during loop cleanup: {cleanup_error}")
        
        # Clean up session
        if session_id in active_sessions:
            logger.info(f"Cleaning up session {session_id}")
            del active_sessions[session_id]


# New Conversational Routes
@socketio.on('send_message')
def handle_send_message(data):
    """Handle conversational messages."""
    session_id = request.sid
    user_message = data.get('message', '').strip()
    
    logger.info(f"📨 FLASK: Received message from session {session_id}")
    logger.info(f"📝 MESSAGE: '{user_message}'")
    logger.info(f"📊 MESSAGE LENGTH: {len(user_message)} characters")
    
    if not user_message:
        logger.warning(f"❌ FLASK: Empty message received from session {session_id}")
        emit('error', {'message': 'Message cannot be empty.'})
        return
    
    logger.info(f"🚀 FLASK: Starting background processing for session {session_id}")
    
    # Process message asynchronously
    import threading
    message_thread = threading.Thread(
        target=process_conversational_message,
        args=(session_id, user_message),
        daemon=True
    )
    message_thread.start()


def process_conversational_message(session_id, user_message):
    """Process conversational message in separate thread."""
    logger.info(f"🔄 FLASK THREAD: Starting message processing for session {session_id}")
    logger.info(f"🧵 THREAD ID: {threading.current_thread().ident}")
    
    loop = None
    try:
        # Create event loop for this thread
        logger.info(f"🔄 FLASK THREAD: Creating new event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Process message with new orchestrator
        logger.info(f"🚀 FLASK THREAD: Calling orchestrator.process_message...")
        result = loop.run_until_complete(
            orchestrator.process_message(session_id, user_message)
        )
        
        logger.info(f"📊 FLASK THREAD: Orchestrator result - Success: {result.get('success', False)}")
        if result.get('success'):
            logger.info(f"⏱️  FLASK THREAD: Processing completed in {result.get('execution_time', 0):.2f}s")
        
        if result["success"]:
            ai_response = result["ai_response"]
            metadata = ai_response.get("metadata", {})
            
            # Debug: Log what we're sending to frontend
            recommended_services = metadata.get("recommended_services", [])
            print(f"🔍 DEBUG: Sending {len(recommended_services)} recommended services to frontend")
            if recommended_services:
                for i, service in enumerate(recommended_services):
                    print(f"   Service {i+1}: {service.get('service_name', 'Unknown')}")
            else:
                print("   No services found in metadata")
            
            # Emit AI response
            socketio.emit('conversation_response', {
                'response': ai_response["content"],
                'type': ai_response.get("type", "conversation"),
                'metadata': metadata,
                'agents_executed': result.get("agents_executed", []),
                'strategy_decision': result.get("strategy_decision", "unknown"),
                'recommended_services': recommended_services,
                'suggested_probes': metadata.get("suggested_probes", []),
                'conversation_guidance': metadata.get("conversation_guidance", ""),
                'confidence': metadata.get("confidence", 0.7)
            }, room=session_id)
        else:
            socketio.emit('error', {
                'message': result.get("error", "Failed to process message"),
                'ai_response': result.get("ai_response", {})
            }, room=session_id)
            
    except Exception as e:
        logger.error(f"Error processing conversational message: {e}")
        socketio.emit('error', {
            'message': f"An error occurred: {str(e)}"
        }, room=session_id)
    
    finally:
        if loop and not loop.is_closed():
            loop.close()


@socketio.on('generate_report')
def handle_generate_report(data):
    """Generate comprehensive analysis report."""
    session_id = request.sid
    
    logger.info(f"Generating report for session {session_id}")
    
    # Generate report asynchronously
    import threading
    report_thread = threading.Thread(
        target=generate_conversation_report,
        args=(session_id,),
        daemon=True
    )
    report_thread.start()


def generate_conversation_report(session_id):
    """Generate comprehensive report in separate thread."""
    loop = None
    try:
        # Create event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Generate report using new orchestrator
        result = loop.run_until_complete(
            orchestrator.generate_analysis_report(session_id)
        )
        
        if result["success"]:
            socketio.emit('report_generated', {
                'report': {
                    'conversation_summary': result.get("conversation_summary", {}),
                    'client_analysis': result.get("client_analysis", {}),
                    'service_recommendations': result.get("service_recommendations", []),
                    'scoping_analysis': result.get("scoping_analysis", []),
                    'next_steps': result.get("next_steps", [])
                },
                'session_id': result.get("session_id", session_id),
                'generated_at': result.get("generated_at", time.time())
            }, room=session_id)
        else:
            socketio.emit('error', {
                'message': f"Failed to generate report: {result.get('error', 'Unknown error')}"
            }, room=session_id)
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        socketio.emit('error', {
            'message': f"An error occurred while generating the report: {str(e)}"
        }, room=session_id)
    
    finally:
        if loop and not loop.is_closed():
            loop.close()


@socketio.on('get_conversation_status')
def handle_get_conversation_status(data):
    """Get current conversation status."""
    session_id = request.sid
    
    try:
        status = conversational_orchestrator.get_conversation_status(session_id)
        emit('conversation_status', status)
    except Exception as e:
        logger.error(f"Error getting conversation status: {e}")
        emit('error', {'message': 'Failed to get conversation status'})


def format_consultation_results(result):
    """Format consultation results for frontend display."""
    
    # Extract key metrics
    agent_results = {}
    for agent_name, agent_result in result.agent_results.items():
        agent_results[agent_name] = {
            'success': agent_result.success,
            'confidence': f"{agent_result.confidence:.1%}",
            'summary': agent_result.content[:200] + "..." if len(agent_result.content) > 200 else agent_result.content
        }
    
    # Extract business intelligence
    business_intelligence = {}
    if result.context:
        business_intelligence = {
            'pain_points_identified': len(result.context.pain_points),
            'services_recommended': len(result.context.recommended_services),
            'client_context_elements': len(result.context.client_context)
        }
        
        # Add scoping results if available
        if result.context.scoping_results:
            scopes = result.context.scoping_results.get('service_scopes', [])
            business_intelligence['services_scoped'] = len(scopes)
            
            # Calculate total investment estimate
            total_investment = 0
            for scope in scopes:
                price_range = scope.get('recommended_tier', {}).get('price_range', '0')
                # Simple price parsing
                import re
                numbers = re.findall(r'[\d,]+', price_range.replace(',', ''))
                if numbers:
                    val = int(numbers[0])
                    if 'K' in price_range.upper():
                        val *= 1000
                    elif 'M' in price_range.upper():
                        val *= 1000000
                    total_investment += val
            
            business_intelligence['total_investment_estimate'] = f"${total_investment:,}" if total_investment > 0 else "Contact for pricing"
    
    # Extract key recommendations
    recommendations = []
    if result.context and result.context.recommended_services:
        for rec in result.context.recommended_services[:3]:  # Top 3
            recommendations.append({
                'service_name': rec.get('service_name', 'Unknown Service'),
                'fit_score': f"{rec.get('fit_score', 0):.0%}",
                'business_value': rec.get('business_value', 'Addresses business challenges')
            })
    
    # Extract scoping highlights
    scoping_highlights = []
    if result.context and result.context.scoping_results:
        scopes = result.context.scoping_results.get('service_scopes', [])
        for scope in scopes[:2]:  # Top 2
            tier = scope.get('recommended_tier', {})
            scoping_highlights.append({
                'service_name': scope.get('service_name', 'Unknown Service'),
                'tier': tier.get('tier_name', 'Standard'),
                'investment': tier.get('price_range', 'Contact for pricing'),
                'team_size': tier.get('team_size', 'TBD'),
                'duration': tier.get('duration', 'TBD'),
                'confidence': f"{scope.get('rationale', {}).get('confidence', 0.5):.0%}"
            })
    
    return {
        'workflow_stats': {
            'execution_time': f"{result.execution_time:.1f} seconds",
            'workflow_efficiency': f"{result.workflow_stats.get('performance_metrics', {}).get('workflow_efficiency_score', 0):.0%}",
            'data_quality': f"{result.workflow_stats.get('performance_metrics', {}).get('data_quality_score', 0):.0%}",
            'average_confidence': f"{result.workflow_stats.get('performance_metrics', {}).get('average_agent_confidence', 0):.0%}"
        },
        'agent_results': agent_results,
        'business_intelligence': business_intelligence,
        'recommendations': recommendations,
        'scoping_highlights': scoping_highlights,
        'final_presentation': result.final_presentation[:1000] + "..." if result.final_presentation and len(result.final_presentation) > 1000 else result.final_presentation
    }


@app.route('/demo-data')
def get_demo_data():
    """Get sample client scenarios for demo purposes."""
    demo_scenarios = [
        {
            'title': 'Regional Bank - Digital Transformation',
            'description': 'Large regional bank with legacy systems and cybersecurity challenges',
            'content': '''Client Meeting Notes - Al-Ahli Financial (Regional Bank)

Company Profile:
- Large regional bank with 12,000 employees across 150 branches
- Established in 1985, traditional banking operations
- Annual revenue ~$2.8 billion, regulated by SAMA

Current Challenges:
1. Legacy core banking system from 2005 causing frequent outages
2. Customer complaints about slow digital services and limited mobile banking
3. Recent cybersecurity audit revealed significant vulnerabilities
4. Manual processes in loan approval taking 2-3 weeks vs competitors' 2-3 days
5. Regulatory pressure to comply with new SAMA digital banking guidelines

Business Goals:
- Become the most digitally advanced regional bank by 2027
- Reduce operational costs by 30% through automation
- Improve customer satisfaction scores from 3.2/5 to 4.5/5
- Achieve 100% compliance with SAMA regulations

Budget Context:
- Board approved $50M digital transformation budget over 3 years
- Willing to invest significantly in cybersecurity after recent threats
- Looking for phased approach to manage risk and cash flow'''
        },
        {
            'title': 'Oil & Gas Company - Enterprise Modernization',
            'description': 'Large energy company seeking comprehensive digital transformation',
            'content': '''CONFIDENTIAL CLIENT CONSULTATION NOTES

Client: Emirates National Oil Company (ENOC)
Company Profile:
- Large state-owned oil & gas company in UAE
- 8,500 employees across upstream, downstream, and retail operations
- Annual revenue: $18.5 billion (2024)
- Operations in 15 countries with 500+ retail stations

Current Business Challenges:
1. Manual processes across supply chain causing 15% cost overruns
2. Inventory management systems from 2010 leading to $50M in excess inventory
3. Recent penetration testing revealed 47 critical vulnerabilities
4. Legacy SCADA systems with no security updates since 2018
5. UAE Energy Strategy 2050 requires 30% emissions reduction by 2030

Strategic Business Objectives:
1. Become the most digitally advanced energy company in the Middle East
2. Reduce operational costs by 25% through automation and optimization
3. Achieve 100% regulatory compliance (cybersecurity, ESG, ISO standards)
4. Launch integrated digital ecosystem connecting all business units

Budget & Investment Context:
- Board approved $200M digital transformation budget over 3 years
- Additional $50M cybersecurity investment approved after recent audit
- CEO mandate: "Think big, move fast, but manage risk"'''
        },
        {
            'title': 'Manufacturing Company - Industry 4.0',
            'description': 'Mid-size manufacturer looking to modernize operations',
            'content': '''Client Consultation - Advanced Manufacturing Solutions LLC

Company Profile:
- Mid-size manufacturing company with 2,500 employees
- Specializes in automotive components and aerospace parts
- Annual revenue: $850M, family-owned business established 1978
- Operations across 8 facilities in Middle East and North Africa

Current Challenges:
1. Production planning still done manually with Excel spreadsheets
2. Quality control processes are paper-based and inconsistent
3. Supply chain visibility limited - frequent material shortages
4. Equipment maintenance is reactive, leading to 15% unplanned downtime
5. Customer demands for real-time order tracking and delivery updates

Business Objectives:
- Implement Industry 4.0 technologies to improve efficiency
- Reduce production costs by 20% through automation
- Achieve 99.5% on-time delivery performance
- Improve product quality scores from 94% to 99%
- Enable predictive maintenance to reduce downtime

Investment Context:
- Family board approved $25M modernization budget over 2 years
- Focus on ROI and proven technologies
- Preference for phased implementation to minimize disruption'''
        }
    ]
    
    return jsonify(demo_scenarios)


if __name__ == '__main__':
    print("🚀 Starting SG D&T AI Co-Pilot Demo Server...")
    print("🌐 Access the demo at: http://localhost:8080")
    print("🤖 AI Co-Pilot system ready for consultations!")
    
    # Install Flask dependencies if needed
    try:
        socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Try running: pip install -r requirements.txt")
