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