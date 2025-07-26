"""
Communication tools for agents to send meaningful messages to channels.
This is separate from status updates - agents should only use this for actual communication.
"""

import asyncio
from sqlmodel import Session, select
from database.init_db import engine
from database.models import Agent, Conversation, Message


async def send_message_to_channel(agent_name: str, channel_name: str, message: str) -> str:
    """
    Allow an agent to send a meaningful message to a specific channel.
    This should only be used for actual communication, not status updates.
    
    Args:
        agent_name (str): The name of the agent sending the message
        channel_name (str): The channel to send to (e.g., "#general", "#engineering")
        message (str): The actual message content
        
    Returns:
        str: Confirmation message
    """
    try:
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent {agent_name} not found"
            
            # Find the conversation/channel
            conversation = session.exec(
                select(Conversation).where(Conversation.name == channel_name)
            ).first()
            if not conversation:
                return f"❌ Channel {channel_name} not found"
            
            # Create and save the message
            new_message = Message(
                conversation_id=conversation.id,
                agent_id=agent.id,
                content=message
            )
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            
            # Broadcast the message via WebSocket
            try:
                from api.main import broadcast_new_message
                await broadcast_new_message(new_message, agent.name)
            except ImportError:
                pass  # WebSocket broadcasting not available
            
            print(f"💬 {agent_name} sent message to {channel_name}: {message[:50]}...")
            return f"✅ Message sent to {channel_name}"
            
    except Exception as e:
        return f"❌ Error sending message: {str(e)}"


async def send_direct_message(agent_name: str, recipient_agent: str, message: str) -> str:
    """
    Allow an agent to send a direct message to another agent.
    
    Args:
        agent_name (str): The name of the agent sending the message
        recipient_agent (str): The name of the recipient agent
        message (str): The message content
        
    Returns:
        str: Confirmation message
    """
    try:
        with Session(engine) as session:
            # Find both agents
            sender = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            recipient = session.exec(select(Agent).where(Agent.name == recipient_agent)).first()
            
            if not sender:
                return f"❌ Sender {agent_name} not found"
            if not recipient:
                return f"❌ Recipient {recipient_agent} not found"
            
            # For now, we'll create a DM "conversation" name based on the two agents
            # In a more sophisticated system, we'd have proper DM conversation management
            dm_name = f"DM: {agent_name} ↔ {recipient_agent}"
            
            # Find or create the DM conversation
            dm_conversation = session.exec(
                select(Conversation).where(Conversation.name == dm_name)
            ).first()
            
            if not dm_conversation:
                # Create the DM conversation
                dm_conversation = Conversation(
                    name=dm_name,
                    description=f"Direct messages between {agent_name} and {recipient_agent}"
                )
                session.add(dm_conversation)
                session.commit()
                session.refresh(dm_conversation)
            
            # Create and save the message
            new_message = Message(
                conversation_id=dm_conversation.id,
                agent_id=sender.id,
                content=message
            )
            session.add(new_message)
            session.commit()
            session.refresh(new_message)
            
            # Broadcast the message via WebSocket
            try:
                from api.main import broadcast_new_message
                await broadcast_new_message(new_message, sender.name)
            except ImportError:
                pass
            
            print(f"📩 {agent_name} sent DM to {recipient_agent}: {message[:50]}...")
            return f"✅ Direct message sent to {recipient_agent}"
            
    except Exception as e:
        return f"❌ Error sending direct message: {str(e)}"


async def ask_for_help(agent_name: str, topic: str, details: str) -> str:
    """
    Allow an agent to ask for help in the general channel.
    This creates a natural conversation starter.
    
    Args:
        agent_name (str): The name of the agent asking for help
        topic (str): The topic they need help with
        details (str): More details about what they need
        
    Returns:
        str: Confirmation message
    """
    help_message = f"Hey team! 🙋‍♀️ I could use some help with {topic}. {details}"
    
    return await send_message_to_channel(agent_name, "#general", help_message)


async def share_update(agent_name: str, update: str) -> str:
    """
    Allow an agent to share a meaningful update with the team.
    This should be used sparingly for important milestones.
    
    Args:
        agent_name (str): The name of the agent sharing the update
        update (str): The update to share
        
    Returns:
        str: Confirmation message
    """
    update_message = f"📢 Update: {update}"
    
    return await send_message_to_channel(agent_name, "#general", update_message) 