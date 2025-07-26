"""
Agent Context & Memory System
Provides agents with conversation history awareness and personal memory
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlmodel import Session, select, desc
from database.init_db import engine
from database.models import (
    Agent, Message, AgentMemory, AgentWorkSession,
    AgentMemoryType, Conversation
)
import os
from dotenv import load_dotenv

load_dotenv()


class AgentContextManager:
    """Manages agent memory, context, and contextual message generation"""
    
    def __init__(self):
        self.summarization_enabled = True
        
    async def get_agent_context(self, agent_name: str, conversation_id: int) -> Dict:
        """Get comprehensive context for an agent in a specific conversation"""
        with Session(engine) as session:
            # Get the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return {}
            
            # Get recent conversation history (last 20 messages as requested)
            recent_messages = await self._get_recent_conversation_history(conversation_id, limit=20)
            
            # Get agent's personal memories
            memories = await self._get_agent_memories(agent.id)
            
            # Get current work session
            work_session = await self._get_current_work_session(agent.id)
            
            # Get conversation summary if available
            conversation_summary = await self._get_recent_conversation_summary(conversation_id)
            
            return {
                "agent": agent,
                "recent_messages": recent_messages,
                "memories": memories,
                "current_work": work_session,
                "conversation_summary": conversation_summary,
                "timestamp": datetime.now()
            }
    
    async def _get_recent_conversation_history(self, conversation_id: int, limit: int = 20) -> List[Dict]:
        """Get recent messages from a conversation"""
        with Session(engine) as session:
            query = (
                select(Message, Agent)
                .join(Agent, Message.agent_id == Agent.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.timestamp))
                .limit(limit)
            )
            
            results = session.exec(query).all()
            
            messages = []
            for message, agent in reversed(results):  # Reverse to get chronological order
                messages.append({
                    "agent_name": agent.name,
                    "content": message.content,
                    "timestamp": message.timestamp,
                    "type": message.type
                })
            
            return messages
    
    async def _get_agent_memories(self, agent_id: int) -> List[Dict]:
        """Get agent's memories, prioritized by importance and recency"""
        with Session(engine) as session:
            query = (
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id)
                .where(
                    (AgentMemory.expires_at.is_(None)) | 
                    (AgentMemory.expires_at > datetime.utcnow())
                )
                .order_by(desc(AgentMemory.importance), desc(AgentMemory.last_accessed))
                .limit(20)
            )
            
            memories = session.exec(query).all()
            
            return [
                {
                    "type": memory.memory_type,
                    "title": memory.title,
                    "content": memory.content,
                    "importance": memory.importance,
                    "created_at": memory.created_at
                }
                for memory in memories
            ]
    
    async def _get_current_work_session(self, agent_id: int) -> Optional[Dict]:
        """Get agent's current active work session"""
        with Session(engine) as session:
            query = (
                select(AgentWorkSession)
                .where(AgentWorkSession.agent_id == agent_id)
                .where(AgentWorkSession.status == "active")
                .order_by(desc(AgentWorkSession.last_updated))
            )
            
            work_session = session.exec(query).first()
            
            if work_session:
                return {
                    "title": work_session.session_title,
                    "description": work_session.description,
                    "progress_notes": work_session.progress_notes,
                    "started_at": work_session.started_at,
                    "last_updated": work_session.last_updated
                }
            
            return None
    
    async def _get_recent_conversation_summary(self, conversation_id: int) -> Optional[Dict]:
        """Get recent conversation summary if available"""
        with Session(engine) as session:
            query = (
                select(ConversationSummary)
                .where(ConversationSummary.conversation_id == conversation_id)
                .order_by(desc(ConversationSummary.created_at))
            )
            
            summary = session.exec(query).first()
            
            if summary:
                return {
                    "summary": summary.summary,
                    "key_topics": summary.key_topics,
                    "action_items": summary.action_items,
                    "key_participants": summary.key_participants
                }
            
            return None
    
    async def generate_contextual_message(self, agent_name: str, conversation_id: int, message_type: str = "spontaneous") -> Optional[str]:
        """Generate a contextual message based on agent's memory and conversation history"""
        try:
            # Get comprehensive context
            context = await self.get_agent_context(agent_name, conversation_id)
            
            if not context.get("agent"):
                return None
            
            agent = context["agent"]
            
            # Build context prompt
            context_prompt = await self._build_context_prompt(context, message_type)
            
            # Generate message using OpenAI (new API syntax)
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": await self._get_agent_system_prompt(agent)
                    },
                    {
                        "role": "user",
                        "content": context_prompt
                    }
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            message = response.choices[0].message.content.strip()
            
            # Update agent's last_accessed time for relevant memories
            await self._update_memory_access_times(agent.id)
            
            return message
            
        except Exception as e:
            print(f"❌ Error generating contextual message for {agent_name}: {e}")
            return None
    
    async def _build_context_prompt(self, context: Dict, message_type: str) -> str:
        """Build a context-aware prompt for message generation"""
        agent = context["agent"]
        recent_messages = context.get("recent_messages", [])
        memories = context.get("memories", [])
        current_work = context.get("current_work")
        conversation_summary = context.get("conversation_summary")
        
        prompt_parts = [
            f"You are {agent.name} ({agent.role}) at VibeCorp.",
            f"Current status: {agent.status}",
            ""
        ]
        
        # Add current work context
        if current_work:
            prompt_parts.extend([
                "CURRENT WORK:",
                f"- Working on: {current_work['title']}",
                f"- Description: {current_work['description']}",
                f"- Progress: {current_work.get('progress_notes', 'In progress')}",
                ""
            ])
        
        # Add recent conversation context (full 20 messages for better context)
        if recent_messages:
            prompt_parts.append("RECENT CONVERSATION HISTORY (last 20 messages):")
            for msg in recent_messages[-15:]:  # Show last 15 messages for better context
                agent_display = msg["agent_name"].replace("_", " ")
                # Truncate very long messages but keep more content for context
                content = msg['content'][:200] + ('...' if len(msg['content']) > 200 else '')
                prompt_parts.append(f"- {agent_display}: {content}")
            prompt_parts.append("")
            prompt_parts.append("💡 Use this conversation history to respond naturally and build on recent discussions.")
        
        # Add relevant memories
        if memories:
            prompt_parts.append("YOUR RECENT MEMORIES:")
            for memory in memories[:5]:  # Top 5 most relevant
                prompt_parts.append(f"- {memory['title']}: {memory['content'][:100]}...")
            prompt_parts.append("")
        
        # Add conversation summary if available
        if conversation_summary:
            prompt_parts.extend([
                "RECENT DISCUSSION SUMMARY:",
                f"- Key topics: {conversation_summary.get('key_topics', 'N/A')}",
                f"- Action items: {conversation_summary.get('action_items', 'None')}",
                ""
            ])
        
        # Add instruction based on message type
        if message_type == "spontaneous":
            prompt_parts.extend([
                "Generate a natural, contextual message that:",
                "1. References your current work or recent conversations when relevant",
                "2. Feels like a natural continuation of team discussions", 
                "3. Shows awareness of what's been happening",
                "4. Stays true to your personality and role",
                "5. Is 1-3 sentences long",
                "",
                "Your message:"
            ])
        elif message_type == "direct_message":
            prompt_parts.extend([
                "Generate a personal, direct message that:",
                "1. Is more casual and personal than public group messages",
                "2. References shared work or experiences with this specific person",
                "3. Shows awareness of recent conversations you've had together",
                "4. Stays true to your personality but is more conversational",
                "5. Is 1-2 sentences long and feels like a private conversation",
                "",
                "Your direct message:"
            ])
        elif message_type == "work_update":
            prompt_parts.extend([
                "Share a brief update about your current work that:",
                "1. References your current work session",
                "2. Shows progress or challenges you're facing",
                "3. Connects to recent team discussions if relevant",
                "4. Stays in character",
                "",
                "Your update:"
            ])
        
        return "\n".join(prompt_parts)
    
    async def _get_agent_system_prompt(self, agent: Agent) -> str:
        """Get the agent's personality system prompt"""
        # Import agent creation functions to get their system messages
        try:
            from agents.agents import get_agent_by_name
            temp_agent = get_agent_by_name(agent.name)
            if temp_agent and hasattr(temp_agent, 'system_message'):
                return temp_agent.system_message
        except:
            pass
        
        # Fallback to basic persona
        return f"You are {agent.name}, a {agent.role} at VibeCorp. {agent.persona}"
    
    async def _update_memory_access_times(self, agent_id: int):
        """Update last_accessed time for agent's memories"""
        with Session(engine) as session:
            memories = session.exec(
                select(AgentMemory)
                .where(AgentMemory.agent_id == agent_id)
                .where(AgentMemory.importance >= 7)  # Only update high-importance memories
            ).all()
            
            for memory in memories:
                memory.last_accessed = datetime.utcnow()
                session.add(memory)
            
            session.commit()
    
    async def add_agent_memory(self, agent_id: int, memory_type: AgentMemoryType, 
                              title: str, content: str, importance: int = 5,
                              context: str = None, expires_at: datetime = None) -> bool:
        """Add a new memory for an agent"""
        try:
            with Session(engine) as session:
                memory = AgentMemory(
                    agent_id=agent_id,
                    memory_type=memory_type,
                    title=title,
                    content=content,
                    importance=importance,
                    context=context,
                    expires_at=expires_at
                )
                
                session.add(memory)
                session.commit()
                
                print(f"💭 Added memory for agent {agent_id}: {title}")
                return True
                
        except Exception as e:
            print(f"❌ Error adding agent memory: {e}")
            return False
    
    async def update_work_session(self, agent_id: int, title: str, description: str, 
                                 progress_notes: str = None) -> bool:
        """Update or create agent's current work session"""
        try:
            with Session(engine) as session:
                # Check for existing active session
                existing = session.exec(
                    select(AgentWorkSession)
                    .where(AgentWorkSession.agent_id == agent_id)
                    .where(AgentWorkSession.status == "active")
                ).first()
                
                if existing:
                    existing.session_title = title
                    existing.description = description
                    existing.progress_notes = progress_notes
                    existing.last_updated = datetime.utcnow()
                    session.add(existing)
                else:
                    session.add(AgentWorkSession(
                        agent_id=agent_id,
                        session_title=title,
                        description=description,
                        progress_notes=progress_notes
                    ))
                
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ Error updating work session: {e}")
            return False


# Global context manager instance
agent_context_manager = AgentContextManager() 