import os
import json
import asyncio
from typing import List, Optional, Set
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from dotenv import load_dotenv

from database.init_db import engine
from database.models import Agent, Conversation, Message, Task, ConversationType, TaskStatus

# Load environment variables
load_dotenv()

# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        # Convert message to JSON string
        message_str = json.dumps(message)
        
        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message_str)
            except Exception as e:
                print(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.discard(connection)

# Create WebSocket manager instance
websocket_manager = WebSocketManager()

# Create FastAPI app
app = FastAPI(
    title="AutoGen Startup Simulation API",
    description="API for the AI agent startup simulation",
    version="1.0.0"
)

# Wipe database for fresh debugging sessions
async def wipe_database_for_debug():
    """Wipe conversation data for fresh debugging session"""
    print("🔄 Wiping database for fresh debug session...")
    
    from sqlmodel import delete
    from database.models import Message, AgentMemory, AgentWorkSession, ConversationSummary, Task
    
    try:
        with Session(engine) as session:
            # Count existing data
            message_count = len(session.exec(select(Message)).all())
            memory_count = len(session.exec(select(AgentMemory)).all())
            task_count = len(session.exec(select(Task)).all())
            
            print(f"📊 Clearing: {message_count} messages, {memory_count} memories, {task_count} tasks")
            
            # Delete all conversation data
            session.exec(delete(Message))
            session.exec(delete(AgentMemory))
            session.exec(delete(AgentWorkSession))
            session.exec(delete(ConversationSummary))
            session.exec(delete(Task))
            session.commit()
            
            print("✅ Database wiped clean for debugging!")
            
    except Exception as e:
        print(f"⚠️  Database wipe error: {e}")

# Setup DM conversations
async def setup_dm_conversations():
    """Ensure DM conversations exist between all agent pairs"""
    try:
        from itertools import combinations
        from database.models import ConversationMember
        
        with Session(engine) as session:
            agents = session.exec(select(Agent)).all()
            dm_pairs = list(combinations(agents, 2))
            created_count = 0
            
            for agent1, agent2 in dm_pairs:
                names = sorted([agent1.name, agent2.name])
                dm_name = f"DM: {names[0].replace('_', ' ')} & {names[1].replace('_', ' ')}"
                
                existing_dm = session.exec(
                    select(Conversation).where(Conversation.name == dm_name).where(Conversation.type == ConversationType.DM)
                ).first()
                
                if not existing_dm:
                    dm_conversation = Conversation(
                        name=dm_name, type=ConversationType.DM,
                        description=f"Direct message conversation between {agent1.name.replace('_', ' ')} and {agent2.name.replace('_', ' ')}"
                    )
                    session.add(dm_conversation)
                    session.commit()
                    session.refresh(dm_conversation)
                    
                    member1 = ConversationMember(agent_id=agent1.id, conversation_id=dm_conversation.id)
                    member2 = ConversationMember(agent_id=agent2.id, conversation_id=dm_conversation.id)
                    session.add(member1)
                    session.add(member2)
                    session.commit()
                    created_count += 1
            
            print(f"💌 DM conversations ready ({created_count} created)")
            
    except Exception as e:
        print(f"⚠️  DM setup error: {e}")

# Start contextual scheduler when the app starts  
@app.on_event("startup")
async def startup_event():
    """Initialize fresh debug session with contextual agents"""
    print("🚀 Starting Fresh Debug Session - AutoGen API")
    print("=" * 55)
    
    # Step 1: Wipe database for clean debugging
    await wipe_database_for_debug()
    
    # Step 2: Setup DM conversations
    await setup_dm_conversations()
    
    # Step 3: Start contextual scheduler
    try:
        from agents.contextual_scheduler import contextual_scheduler
        # Start the scheduler in the background
        asyncio.create_task(contextual_scheduler.start())
        print("🤖 Contextual agent scheduler started!")
        print("🎯 Debug config: 15-45s intervals, 70% DMs, 20 msg history")
        print("=" * 55)
    except Exception as e:
        print(f"❌ Error starting contextual scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up when the app shuts down"""
    print("🛑 Shutting down AutoGen Startup Simulation API...")
    
    # Stop the contextual scheduler
    try:
        from agents.contextual_scheduler import contextual_scheduler
        await contextual_scheduler.stop()
        print("🤖 Contextual agent scheduler stopped!")
    except Exception as e:
        print(f"❌ Error stopping contextual scheduler: {e}")

# Configure CORS for production and development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_session():
    with Session(engine) as session:
        yield session

# Pydantic models for API responses
class AgentResponse(BaseModel):
    id: int
    name: str
    role: str
    persona: str
    status: str
    created_at: str

class ConversationResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str]
    created_at: str

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    agent_id: int
    agent_name: str
    content: str
    type: str
    timestamp: str

class TaskRequest(BaseModel):
    title: str
    description: str
    conversation_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    conversation_id: Optional[int]
    created_at: str

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AutoGen Startup Simulation API!",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AutoGen Startup Simulation API"}

# GET /agents - Returns all agents
@app.get("/agents", response_model=List[AgentResponse])
async def get_agents(session: Session = Depends(get_session)):
    """Get all AI agents in the simulation"""
    try:
        agents = session.exec(select(Agent)).all()
        return [
            AgentResponse(
                id=agent.id,
                name=agent.name,
                role=agent.role,
                persona=agent.persona,
                status=agent.status,
                created_at=agent.created_at.isoformat()
            )
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agents: {str(e)}")

# GET /conversations - Returns all conversations
@app.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(session: Session = Depends(get_session)):
    """Get all conversations (channels and DMs)"""
    try:
        conversations = session.exec(select(Conversation)).all()
        return [
            ConversationResponse(
                id=conv.id,
                name=conv.name,
                type=conv.type.value,
                description=conv.description,
                created_at=conv.created_at.isoformat()
            )
            for conv in conversations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

# GET /conversations/{conv_id}/messages - Returns message history for a conversation
@app.get("/conversations/{conv_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conv_id: int, 
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Get message history for a specific conversation"""
    try:
        # Check if conversation exists
        conversation = session.get(Conversation, conv_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages with agent information
        query = (
            select(Message, Agent)
            .join(Agent, Message.agent_id == Agent.id)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
        )
        
        results = session.exec(query).all()
        
        return [
            MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                agent_id=message.agent_id,
                agent_name=agent.name,
                content=message.content,
                type=message.type.value,
                timestamp=message.timestamp.isoformat()
            )
            for message, agent in results
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

# POST /tasks - Create a new task and trigger agent conversation
@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskRequest,
    session: Session = Depends(get_session)
):
    """Create a new task for the AI agents and trigger conversation"""
    try:
        # Create new task
        task = Task(
            title=task_request.title,
            description=task_request.description,
            status=TaskStatus.PENDING,
            assigned_conversation_id=task_request.conversation_id or 1  # Default to #general
        )
        
        session.add(task)
        session.commit()
        session.refresh(task)
        
        print(f"📝 New task created: {task.title}")
        
        # Broadcast task creation
        await broadcast_task_update(task)
        
        # Update task status to in_progress
        task.status = TaskStatus.IN_PROGRESS
        session.add(task)
        session.commit()
        
        # Trigger agent conversation in the background
        import sys
        sys.path.append('.')
        
        # Import the agent conversation function
        try:
            from main import run_agent_conversation
            
            # Start the agent conversation in a background task
            asyncio.create_task(run_agent_conversation(
                task.title,
                task.description,
                task.assigned_conversation_id
            ))
            
            print(f"🚀 Started agent conversation for task: {task.title}")
            
        except ImportError as import_error:
            print(f"❌ Could not import agent conversation function: {import_error}")
        except Exception as conversation_error:
            print(f"❌ Error starting agent conversation: {conversation_error}")
        
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            conversation_id=task.assigned_conversation_id,
            created_at=task.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")

# GET /tasks - Get all tasks
@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(session: Session = Depends(get_session)):
    """Get all tasks"""
    try:
        tasks = session.exec(select(Task).order_by(Task.created_at.desc())).all()
        return [
            TaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status.value,
                conversation_id=task.assigned_conversation_id,
                created_at=task.created_at.isoformat()
            )
            for task in tasks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to AutoGen Startup Simulation"
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                else:
                    print(f"Received WebSocket message: {message}")
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    finally:
        websocket_manager.disconnect(websocket)

# Helper function to broadcast new messages
async def broadcast_new_message(message: Message, agent_name: str):
    """Broadcast a new message to all connected WebSocket clients"""
    await websocket_manager.broadcast({
        "type": "new_message",
        "data": {
            "id": message.id,
            "conversationId": message.conversation_id,
            "agentId": message.agent_id,
            "agentName": agent_name,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "type": message.type.value
        }
    })

# Helper function to broadcast agent status updates
async def broadcast_agent_status_update(agent_id: int, status: str):
    """Broadcast agent status update to all connected WebSocket clients"""
    await websocket_manager.broadcast({
        "type": "agent_status_update", 
        "data": {
            "agentId": agent_id,
            "status": status
        }
    })

# Helper function to broadcast task updates
async def broadcast_task_update(task: Task):
    """Broadcast task update to all connected WebSocket clients"""
    await websocket_manager.broadcast({
        "type": "task_update",
        "data": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "conversationId": task.assigned_conversation_id,
            "createdAt": task.created_at.isoformat()
        }
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
