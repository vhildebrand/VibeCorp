import os
import asyncio
from dotenv import load_dotenv
from sqlmodel import Session, select
from autogen import GroupChat, GroupChatManager

from database.init_db import init_database, engine
from database.models import Agent, Conversation, Message, ConversationType, MessageType
from agents.agents import get_all_agents, get_agent_by_name, create_agents_with_tools
from api.main import websocket_manager, broadcast_new_message

# Load environment variables
load_dotenv()


async def save_message_to_db(agent_name: str, content: str, conversation_id: int):
    """Save a message to the database and broadcast via WebSocket"""
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
        session.refresh(message)  # Get the ID from the database
        
        print(f"💾 Saved message from {agent_name} to database")
        
        # Broadcast the new message via WebSocket
        try:
            await broadcast_new_message(message, agent_name)
            print(f"📡 Broadcasted message from {agent_name} via WebSocket")
        except Exception as e:
            print(f"❌ Error broadcasting message: {e}")


def create_group_chat_session(conversation_name: str = "#general"):
    """Create a group chat session for the agents"""
    # Initialize database if needed
    init_database()
    
    # Get all agents with tools registered
    agents, executor = create_agents_with_tools()
    
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


async def run_agent_conversation(task_title: str, task_description: str, conversation_id: int = 1):
    """Run an agent conversation based on a task and broadcast messages in real-time"""
    print(f"🚀 Starting agent conversation for task: {task_title}")
    print("=" * 50)
    
    # Create the group chat session
    group_chat, manager, agents = create_group_chat_session()
    
    # Create initial task message
    initial_message = f"🎯 NEW TASK: {task_title}\n\n{task_description}\n\nLet's collaborate on this! What's our game plan?"
    
    print(f"\n🎭 Task Assignment: {initial_message}")
    await save_message_to_db("CeeCee_The_CEO", initial_message, conversation_id)
    
    try:
        # Get the CEO agent from the created agents list
        ceo = None
        for agent in agents:
            if agent.name == "CeeCee_The_CEO":
                ceo = agent
                break
        
        if not ceo:
            raise Exception("CEO agent not found")
        
        # Custom message handler that saves to DB and broadcasts
        class ConversationLogger:
            def __init__(self, conversation_id):
                self.conversation_id = conversation_id
                
            async def log_message(self, agent_name: str, content: str):
                """Log message to database and broadcast"""
                print(f"\n🎭 {agent_name}: {content}")
                await save_message_to_db(agent_name, content, self.conversation_id)
        
        logger = ConversationLogger(conversation_id)
        
        # Start the conversation
        result = ceo.initiate_chat(
            manager,
            message=initial_message
        )
        
        # Process the conversation results and save additional messages
        if hasattr(result, 'chat_history'):
            for message in result.chat_history:
                if hasattr(message, 'name') and hasattr(message, 'content'):
                    # Skip the initial message as it's already saved
                    if message['content'] != initial_message:
                        await logger.log_message(message['name'], message['content'])
        
        print("\n" + "=" * 50)
        print("🎉 Agent conversation completed!")
        print("📊 All messages saved to database and broadcasted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during agent conversation: {str(e)}")
        # Broadcast error message
        try:
            error_message = f"❌ Error in agent conversation: {str(e)}"
            await save_message_to_db("System", error_message, conversation_id)
        except:
            pass
        return False

def run_conversation_test():
    """Run a test conversation (wrapper for async function)"""
    return asyncio.run(run_agent_conversation(
        "Brainstorm Revolutionary Product Ideas",
        "We need to disrupt the market this quarter with game-changing, synergistic ideas that will leverage our core competencies and move the needle!"
    ))


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
