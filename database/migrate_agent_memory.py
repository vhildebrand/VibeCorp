"""
Migration script to add agent memory tables to existing database
"""

import os
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
from database.models import AgentMemory, AgentWorkSession, ConversationSummary

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./startup_simulation.db")

if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    engine = create_engine(DATABASE_URL, echo=True)
else:
    engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})


def migrate_agent_memory_tables():
    """Add new agent memory tables to existing database"""
    try:
        print("🔄 Adding agent memory tables to database...")
        print("💭 This will enable agents to have memory and contextual awareness")
        
        # Create only the new tables
        AgentMemory.metadata.create_all(engine)
        AgentWorkSession.metadata.create_all(engine) 
        ConversationSummary.metadata.create_all(engine)
        
        print("✅ Agent memory tables created successfully!")
        print("🧠 New tables added:")
        print("   - AgentMemory: Stores agent memories and observations")
        print("   - AgentWorkSession: Tracks what agents are working on")
        print("   - ConversationSummary: AI-generated conversation summaries")
        print("")
        print("🎯 Agents can now:")
        print("   - Remember past conversations and work")
        print("   - Reference recent discussions in new messages")
        print("   - Track ongoing projects and progress")
        print("   - Generate contextual, natural responses")
        
    except Exception as e:
        print(f"❌ Error creating agent memory tables: {e}")
        print("💡 This might be because the tables already exist")


if __name__ == "__main__":
    migrate_agent_memory_tables() 