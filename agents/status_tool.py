"""
Tool for agents to update their own status dynamically
"""

import asyncio
from sqlmodel import Session, select
from database.init_db import engine
from database.models import Agent


async def update_agent_status(agent_name: str, new_status: str, activity_description: str = None) -> str:
    """
    Allow an agent to update their own status to reflect their current activity.
    
    Args:
        agent_name (str): The name of the agent updating their status
        new_status (str): The new status (can be any descriptive string)
        activity_description (str, optional): Optional description of what they're doing
        
    Returns:
        str: Confirmation message
    """
    try:
        # Ensure new_status is a reasonable length and format
        new_status = new_status.lower().replace(' ', '_')[:50]  # Max 50 chars, underscore format
        
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent {agent_name} not found"
            
            # Update status
            old_status = agent.status
            agent.status = new_status
            session.add(agent)
            session.commit()
            
            # Broadcast status update via WebSocket if available
            try:
                from api.main import broadcast_agent_status_update
                await broadcast_agent_status_update(agent.id, new_status)
            except ImportError:
                pass  # WebSocket broadcasting not available
            
            # Create confirmation message
            status_msg = f"📊 Status updated: {old_status} → {new_status}"
            if activity_description:
                status_msg += f"\n💼 Activity: {activity_description}"
            
            print(f"🤖 {agent_name} status changed to: {new_status}")
            return status_msg
            
    except Exception as e:
        return f"❌ Error updating status: {str(e)}"


def set_agent_status(agent_name: str, new_status: str, activity_description: str = None) -> str:
    """
    Synchronous wrapper for agents to update their status.
    
    Args:
        agent_name (str): The name of the agent updating their status
        new_status (str): The new status (can be any descriptive string)
        activity_description (str, optional): Optional description of what they're doing
        
    Returns:
        str: Confirmation message
    """
    try:
        # Run the async function in the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run()
                # Create a task instead (this might not work in all contexts)
                task = loop.create_task(update_agent_status(agent_name, new_status, activity_description))
                # For now, just update synchronously without WebSocket broadcast
                pass
        except RuntimeError:
            # No event loop running, create a new one
            pass
        
        # Fallback to synchronous database update
        new_status = new_status.lower().replace(' ', '_')[:50]
        
        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent {agent_name} not found"
            
            old_status = agent.status
            agent.status = new_status
            session.add(agent)
            session.commit()
            
            status_msg = f"📊 Status updated: {old_status} → {new_status}"
            if activity_description:
                status_msg += f"\n💼 Activity: {activity_description}"
            
            print(f"🤖 {agent_name} status changed to: {new_status}")
            return status_msg
            
    except Exception as e:
        return f"❌ Error updating status: {str(e)}"


# Common status suggestions for agents (they can use any status they want)
SUGGESTED_STATUSES = {
    # Development work
    "coding": "Writing or debugging code",
    "code_review": "Reviewing code changes",
    "testing": "Running tests or QA",
    "debugging": "Fixing bugs or issues",
    "deploying": "Deploying code to production",
    "refactoring": "Improving code structure",
    
    # Research and analysis
    "researching": "Conducting research or analysis", 
    "analyzing_data": "Analyzing metrics or data",
    "market_research": "Researching market trends",
    "competitor_analysis": "Analyzing competitors",
    
    # Communication and meetings
    "in_meeting": "In a meeting or discussion",
    "presenting": "Giving a presentation",
    "interviewing": "Conducting interviews",
    "onboarding": "Training or onboarding someone",
    
    # Creative work
    "writing": "Writing content or documentation",
    "designing": "Creating designs or mockups",
    "content_creation": "Creating marketing content",
    "brainstorming": "Brainstorming ideas",
    
    # Marketing activities
    "social_media": "Managing social media",
    "campaign_planning": "Planning marketing campaigns",
    "user_outreach": "Reaching out to users",
    "analytics_review": "Reviewing marketing analytics",
    
    # Administrative
    "planning": "Planning projects or tasks",
    "organizing": "Organizing processes or events",
    "documenting": "Writing documentation",
    "email": "Handling emails and communication",
    
    # HR and team activities  
    "team_building": "Planning team activities",
    "policy_review": "Reviewing company policies",
    "performance_review": "Conducting performance reviews",
    "recruiting": "Recruiting new team members",
    
    # General states
    "idle": "Available and not actively working",
    "thinking": "Thinking through a problem",
    "working": "General productive work",
    "break": "Taking a break",
    "learning": "Learning new skills or technologies"
}


if __name__ == "__main__":
    # Test the status update function
    result = set_agent_status("test_agent", "testing_status_system", "Testing the new flexible status system")
    print(result) 