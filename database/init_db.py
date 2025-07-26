import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from database.models import (
    Agent, Conversation, ConversationMember, Message, Task,
    ConversationType, AgentMemory, AgentWorkSession, ConversationSummary
)

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./startup_simulation.db")

# Configure engine based on database type
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    # PostgreSQL configuration for production
    engine = create_engine(DATABASE_URL, echo=True)
else:
    # SQLite configuration for local development
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def create_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully!")


def seed_initial_data():
    """Seed the database with initial agents and conversations"""
    with Session(engine) as session:
        # Check if data already exists
        existing_agents = session.query(Agent).first()
        if existing_agents:
            print("ℹ️  Initial data already exists, skipping seed.")
            return

        # Create the four main agents
        agents = [
            Agent(
                name="CeeCee_The_CEO",
                role="CEO",
                persona="An overly enthusiastic, buzzword-loving CEO who thinks everything can be disrupted. Uses corporate speak constantly and believes every idea is 'game-changing' and 'synergistic'. Often makes unrealistic demands and timelines while being completely out of touch with technical realities.",
                status="idle"
            ),
            Agent(
                name="Marty_The_Marketer", 
                role="Marketer",
                persona="A social media obsessed marketer who speaks in emoji and thinks every problem can be solved with a viral campaign. Constantly suggesting TikTok dances, influencer partnerships, and 'growth hacking'. Uses marketing jargon and is always trying to make things 'go viral'.",
                status="idle"
            ),
            Agent(
                name="Penny_The_Programmer",
                role="Programmer", 
                persona="A pragmatic, slightly sarcastic programmer who speaks in technical terms and LOG statements. Gets frustrated with unrealistic requests and prefers to focus on actual implementation over buzzwords. Often the voice of reason but can be blunt about technical limitations.",
                status="idle"
            ),
            Agent(
                name="Herb_From_HR",
                role="HR",
                persona="An overly friendly HR representative who turns everything into a team-building exercise or sensitivity training opportunity. Constantly worried about workplace harmony and suggests trust falls, team retreats, and 'synergy sessions' to solve every conflict.",
                status="idle"
            )
        ]

        # Add agents to session
        for agent in agents:
            session.add(agent)
        
        session.commit()
        print("✅ Agents created successfully!")

        # Create default conversations
        conversations = [
            Conversation(
                name="#general",
                type=ConversationType.GROUP,
                description="Main company-wide discussion channel"
            ),
            Conversation(
                name="#random", 
                type=ConversationType.GROUP,
                description="Off-topic discussions and water cooler chat"
            ),
            Conversation(
                name="#brainstorming",
                type=ConversationType.GROUP,
                description="Ideas and project planning"
            )
        ]

        # Add conversations to session
        for conv in conversations:
            session.add(conv) 
        
        session.commit()
        print("✅ Conversations created successfully!")

        # Add all agents to all group conversations
        for agent in agents:
            for conv in conversations:
                member = ConversationMember(
                    agent_id=agent.id,
                    conversation_id=conv.id
                )
                session.add(member)
        
        session.commit()
        print("✅ Conversation memberships created successfully!")


def init_database():
    """Initialize the database with tables and seed data"""
    print("🔄 Initializing database...")
    create_tables()
    seed_initial_data()
    print("🎉 Database initialization complete!")


if __name__ == "__main__":
    init_database() 