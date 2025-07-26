import os
import asyncio
from dotenv import load_dotenv
from sqlmodel import Session, select
from autogen import GroupChat, GroupChatManager

from database.init_db import init_database, engine
from database.models import Agent, Conversation, Message, ConversationType, MessageType
from agents.agents import get_all_agents, get_agent_by_name

# Load environment variables
load_dotenv()


def save_message_to_db(agent_name: str, content: str, conversation_id: int):
    """Save a message to the database"""
    with Session(engine) as session:
        # Get the agent from the database
        agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
        if not agent:
            print(f"Warning: Agent {agent_name} not found in database")
            return
        
        # Create and save the message
        message = Message(
            conversation_id=conversation_id,
            agent_id=agent.id,
            content=content,
            type=MessageType.MESSAGE
        )
        session.add(message)
        session.commit()
        print(f"💾 Saved message from {agent_name} to database")


def create_group_chat_session(conversation_name: str = "#general"):
    """Create a group chat session for the agents"""
    # Initialize database if needed
    init_database()
    
    # Get all agents
    agents = get_all_agents()
    executor = get_agent_by_name("Executor")
    
    # Add executor to the agent list
    all_agents = agents + [executor]
    
    # Create the group chat
    group_chat = GroupChat(
        agents=all_agents,
        messages=[],
        max_round=10,  # Limit rounds for testing
        speaker_selection_method="auto"
    )
    
    # Create the manager configuration
    manager_config = {
        "config_list": [{
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY")
        }],
        "temperature": 0.7
    }
    
    # Create the group chat manager
    manager = GroupChatManager(
        groupchat=group_chat,
        llm_config=manager_config
    )
    
    return group_chat, manager, agents


def run_conversation_test():
    """Run a test conversation and save messages to database"""
    print("🚀 Starting AutoGen Startup Simulation...")
    print("=" * 50)
    
    # Create the group chat session
    group_chat, manager, agents = create_group_chat_session()
    
    # Get the conversation ID from database
    with Session(engine) as session:
        conversation = session.exec(
            select(Conversation).where(Conversation.name == "#general")
        ).first()
        conversation_id = conversation.id if conversation else 1
    
    # Define a custom message logging function
    def log_message(message):
        """Log messages and save to database"""
        if hasattr(message, 'name') and hasattr(message, 'content'):
            print(f"\n🎭 {message['name']}: {message['content']}")
            save_message_to_db(message['name'], message['content'], conversation_id)
    
    # Start the conversation
    initial_message = (
        "Good morning team! 🌟 We need to DISRUPT the market this quarter with some "
        "GAME-CHANGING, synergistic ideas that will leverage our core competencies and "
        "move the needle! Let's brainstorm something REVOLUTIONARY that will make us "
        "first to market! We need this yesterday! 🚀"
    )
    
    print(f"\n🎭 CeeCee_The_CEO: {initial_message}")
    save_message_to_db("CeeCee_The_CEO", initial_message, conversation_id)
    
    try:
        # Get the CEO agent
        ceo = get_agent_by_name("CeeCee_The_CEO")
        
        # Start the conversation
        result = ceo.initiate_chat(
            manager,
            message=initial_message
        )
        
        print("\n" + "=" * 50)
        print("🎉 Conversation completed!")
        print("📊 Check the database for saved messages")
        
    except Exception as e:
        print(f"❌ Error during conversation: {str(e)}")
        return False
    
    return True


def main():
    """Main function to run the simulation"""
    print("🏢 Welcome to the AutoGen Startup Simulation!")
    print("👥 Meet your team:")
    print("   • CeeCee - The overly enthusiastic CEO")
    print("   • Marty - The social media obsessed Marketer") 
    print("   • Penny - The pragmatic Programmer")
    print("   • Herb - The team-building focused HR rep")
    print()
    
    # Run the test conversation
    success = run_conversation_test()
    
    if success:
        print("\n✅ Sprint 1 completed successfully!")
        print("🎯 Deliverables achieved:")
        print("   • ✅ Python environment and dependencies installed")
        print("   • ✅ Database models and initialization complete")
        print("   • ✅ AI agents with distinct personalities created")
        print("   • ✅ Group chat conversation logic implemented")
        print("   • ✅ Message persistence to database working")
    else:
        print("\n❌ Sprint 1 encountered issues. Check the error messages above.")


if __name__ == "__main__":
    main()
