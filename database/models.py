from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConversationType(str, Enum):
    GROUP = "group"
    DM = "dm"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class MessageType(str, Enum):
    MESSAGE = "message"
    ACTION = "action"


class AgentMemoryType(str, Enum):
    WORK_ITEM = "work_item"           # Something the agent is working on
    CONVERSATION_CONTEXT = "conversation_context"  # Recent conversation awareness
    PERSONAL_NOTE = "personal_note"   # Agent's personal observations
    ACHIEVEMENT = "achievement"       # Completed work or accomplishments


# Removed rigid AgentStatus enum - agents can now set any status they want
# This allows for dynamic, context-aware status updates based on their actual activities


# Agent table - stores information about each AI agent
class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    role: str  # CEO, Marketer, Programmer, HR
    persona: str  # Detailed personality description
    status: str = Field(default="idle")  # Flexible status - agents can set any status they want
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to messages
    messages: List["Message"] = Relationship(back_populates="agent")


# Conversation table - represents channels and DMs
class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # e.g., "#general", "#random", "CEO-Programmer"
    type: ConversationType
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to messages
    messages: List["Message"] = Relationship(back_populates="conversation")
    # Relationship to conversation members
    members: List["ConversationMember"] = Relationship(back_populates="conversation")


# Junction table for many-to-many relationship between agents and conversations
class ConversationMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    conversation_id: int = Field(foreign_key="conversation.id")
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    agent: Optional[Agent] = Relationship()
    conversation: Optional[Conversation] = Relationship(back_populates="members")


# Message table - stores all messages and actions
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    agent_id: int = Field(foreign_key="agent.id")
    content: str
    type: MessageType = Field(default=MessageType.MESSAGE)
    extra_data: Optional[str] = None  # JSON string for additional data
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    agent: Optional[Agent] = Relationship(back_populates="messages")


# Task table - high-level tasks for the agent team
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assigned_conversation_id: Optional[int] = Field(foreign_key="conversation.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Relationship to the conversation where this task is being worked on
    conversation: Optional[Conversation] = Relationship()


# Agent Memory System - New models for contextual awareness

# AgentMemory - Stores what each agent remembers and is working on
class AgentMemory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    memory_type: AgentMemoryType
    title: str  # Brief title of what this memory is about
    content: str  # Detailed content of the memory
    context: Optional[str] = None  # Additional context or metadata
    importance: int = Field(default=5)  # 1-10 scale, helps prioritize what to remember
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Some memories can expire
    
    # Relationships
    agent: Optional[Agent] = Relationship()


# AgentWorkSession - Tracks what agents are currently working on
class AgentWorkSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    session_title: str  # What they're working on
    description: str  # Detailed description
    status: str = Field(default="active")  # active, completed, paused
    progress_notes: Optional[str] = None  # Agent's notes on progress
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Relationships
    agent: Optional[Agent] = Relationship()


# ConversationSummary - AI-generated summaries of recent conversations
class ConversationSummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    summary: str  # AI-generated summary of key points
    key_participants: str  # Which agents were most active
    key_topics: str  # Main topics discussed
    action_items: Optional[str] = None  # Any action items identified
    time_period_start: datetime
    time_period_end: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    conversation: Optional[Conversation] = Relationship() 