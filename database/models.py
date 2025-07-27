from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
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
    BLOCKED = "blocked"


class MessageType(str, Enum):
    MESSAGE = "message"
    ACTION = "action"


class AgentMemoryType(str, Enum):
    CONVERSATION_CONTEXT = "conversation_context"
    WORK_ITEM = "work_item"
    OBSERVATION = "observation"


# Agent table - stores information about each AI agent
class Agent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    role: str
    persona: str
    system_prompt: str
    status: str = Field(default="idle")
    
    messages: List["Message"] = Relationship(back_populates="agent")
    tasks: List["AgentTask"] = Relationship(back_populates="agent")


# Conversation table - represents channels and DMs
class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str
    type: ConversationType = Field(default=ConversationType.GROUP)
    members: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    
    messages: List["Message"] = Relationship(back_populates="conversation")


# Message table - stores all messages and actions
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    agent_id: int = Field(foreign_key="agent.id")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    agent: Agent = Relationship(back_populates="messages")
    conversation: Conversation = Relationship(back_populates="messages")


# AgentTask table - individual agent to-do lists
class AgentTask(SQLModel, table=True):
    __tablename__ = "agent_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    title: str
    description: str
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: int = Field(default=10)
    dependencies: Optional[str] = Field(default=None)  # Storing dependencies as a comma-separated string of task IDs
    
    agent: Agent = Relationship(back_populates="tasks")


# Agent Memory System - New models for contextual awareness

# AgentMemory - Stores what each agent remembers and is working on
class AgentMemory(SQLModel, table=True):
    __tablename__ = "agent_memories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    memory_type: AgentMemoryType
    title: str
    content: str
    importance: int = Field(default=5)  # Importance score from 1-10
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# AgentWorkSession - Tracks what agents are currently working on
class AgentWorkSession(SQLModel, table=True):
    __tablename__ = "agent_work_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id", unique=True)
    title: str
    description: str
    progress: str
    last_updated: datetime = Field(default_factory=datetime.utcnow)