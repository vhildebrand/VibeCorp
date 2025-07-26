import os
import json
import asyncio
from typing import List, Optional, Set, Union
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from pydantic import BaseModel
from dotenv import load_dotenv
import aiohttp
import uvicorn
from contextlib import asynccontextmanager
from fastapi import status

from agents.agent_context import agent_context_manager
from database.init_db import init_database, engine
from database.models import Agent, Conversation, Message, TaskStatus, AgentTask, AgentMemory, AgentMemoryType, MessageType
from agents.agents import get_all_agents, get_agent_by_name, create_agents_with_tools

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

# Global aiohttp session
http_session: Optional[aiohttp.ClientSession] = None

# Global agent manager
agent_manager = None

# WebSocket Manager
websocket_manager = WebSocketManager()

# ==============================================================================
# Global In-Memory Message Queue
# This will be the central communication bus for agents
# ==============================================================================
message_queue = asyncio.Queue()


async def get_http_session():
    """Get the global aiohttp session"""
    return http_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global http_session, agent_manager
    print("🚀 Server starting up...")
    
    # Delete existing database for completely fresh start
    print("🗄️ Creating completely fresh database...")
    db_path = "startup_simulation.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Deleted existing database: {db_path}")
    
    # Initialize fresh database
    init_database()
    print("✅ Fresh database initialized")
    
    # Clear twitter feed for fresh start
    print("🐦 Initializing fresh Twitter feed...")
    twitter_feed_path = "workspace/twitter_feed.json"
    fresh_twitter_feed = {
        "tweets": [],
        "last_updated": "2025-01-01T00:00:00Z",
        "total_tweets": 0,
        "engagement_metrics": {
            "total_likes": 0,
            "total_retweets": 0,
            "total_replies": 0
        }
    }
    os.makedirs("workspace", exist_ok=True)
    with open(twitter_feed_path, "w") as f:
        json.dump(fresh_twitter_feed, f, indent=2)
    
    # Create aiohttp session
    http_session = aiohttp.ClientSession()
    
    # Automatically start fresh simulation
    print("🎬 Starting fresh simulation automatically...")
    try:
        from agents.agent_manager import AgentManager
        
        agent_manager = AgentManager(message_queue)
        
        # Start the agent manager and message queue listener
        asyncio.create_task(agent_manager.start())
        asyncio.create_task(message_queue_listener())
        
        print("✅ Fresh simulation started automatically!")
        
    except Exception as e:
        print(f"❌ Failed to auto-start simulation: {str(e)}")

    yield

    # Clean up resources
    print("🛑 Server shutting down...")
    if http_session:
        await http_session.close()
    
    # Stop the agent manager if running
    if agent_manager and agent_manager.is_running():
        await agent_manager.stop()


app = FastAPI(lifespan=lifespan)

# Database dependency
def get_session():
    with Session(engine) as session:
        yield session

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

class ConversationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    agent_id: int
    agent_name: str
    content: str
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
                status=agent.status
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
                description=conv.description
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
                timestamp=message.timestamp.isoformat()
            )
            for message, agent in results
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

# Legacy task endpoints - temporarily disabled while we focus on agent-specific tasks
# These used the old Task model which has been replaced with AgentTask

# @app.post("/tasks", response_model=TaskResponse)
# async def create_task(...):
#     # Implementation temporarily disabled

# @app.get("/tasks", response_model=List[TaskResponse])
# async def get_tasks(...):
#     # Implementation temporarily disabled

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

async def message_queue_listener():
    """
    Background task that listens to the message queue and broadcasts
    agent activities to WebSocket clients.
    """
    print("🎧 Starting message queue listener...")
    
    while True:
        try:
            # Wait for messages from the agent message queue
            message = await message_queue.get()
            
            # Broadcast different types of messages
            if message.get("type") == "agent_action":
                await websocket_manager.broadcast({
                    "type": "agent_activity",
                    "data": {
                        "agent": message["agent"],
                        "action": message["tool"],
                        "result": message["result"],
                        "timestamp": message["timestamp"]
                    }
                })
                print(f"📡 Broadcasted agent activity: {message['agent']} used {message['tool']}")
                
            elif message.get("type") == "task_update":
                await websocket_manager.broadcast({
                    "type": "task_update",
                    "data": message
                })
                print(f"📡 Broadcasted task update")
                
            # Mark task as done
            message_queue.task_done()
            
        except asyncio.CancelledError:
            print("🛑 Message queue listener cancelled")
            break
        except Exception as e:
            print(f"❌ Error in message queue listener: {e}")
            await asyncio.sleep(1)


async def broadcast_task_list_update(agent_id: int):
    """Broadcast when an agent's task list is updated."""
    try:
        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                return
                
            tasks = session.exec(
                select(AgentTask)
                .where(AgentTask.agent_id == agent_id)
                .order_by(AgentTask.priority)
            ).all()
            
            await websocket_manager.broadcast({
                "type": "agent_tasks_updated",
                "data": {
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "tasks": [
                        {
                            "id": task.id,
                            "title": task.title,
                            "description": task.description,
                            "status": task.status.value,
                            "priority": task.priority
                        }
                        for task in tasks
                    ]
                }
            })
            
    except Exception as e:
        print(f"❌ Error broadcasting task list update: {e}")

# Helper function to broadcast new messages
async def broadcast_new_message(message: Message, agent_name: str):
    """Broadcast a new message to all connected WebSocket clients."""
    await websocket_manager.broadcast({
        "type": "new_message",
        "data": {
            "id": message.id,
            "conversationId": message.conversation_id,
            "agentId": message.agent_id,
            "agentName": agent_name,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }
    })

# Helper function to broadcast agent status updates
async def broadcast_agent_status_update(agent_id: int, status: str):
    """Broadcast an agent status update."""
    await websocket_manager.broadcast({
        "type": "agent_status_update",
        "agent_id": agent_id,
        "status": status
    })

# Helper function to broadcast task updates
async def broadcast_task_update(task: AgentTask):
    """Broadcast a task update to all clients."""
    await websocket_manager.broadcast({
        "type": "agent_task_update",
        "task": {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority,
            "agent_id": task.agent_id
        }
    })

# ==============================================================================
# Global In-Memory Message Queue
# This will be the central communication bus for agents
# ==============================================================================
message_queue = asyncio.Queue()

# ==============================================================================
# API Endpoints
# ==============================================================================

# Simulation Endpoints
@app.post("/simulation/start", status_code=status.HTTP_202_ACCEPTED)
async def start_simulation():
    """
    Starts the autonomous agent simulation.
    Initializes the AgentManager and starts the agent loops.
    """
    global agent_manager
    
    if agent_manager and agent_manager.is_running():
        raise HTTPException(status_code=400, detail="Simulation is already running.")
    
    try:
        from agents.agent_manager import AgentManager
        
        agent_manager = AgentManager(message_queue)
        
        # Start the agent manager and message queue listener
        asyncio.create_task(agent_manager.start())
        asyncio.create_task(message_queue_listener())
        
        return {"message": "Agent simulation started in the background.", "status": "starting"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start simulation: {str(e)}")


@app.post("/simulation/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_simulation():
    """
    Stops the autonomous agent simulation.
    """
    global agent_manager
    
    if not agent_manager or not agent_manager.is_running():
        raise HTTPException(status_code=400, detail="Simulation is not running.")
    
    try:
        await agent_manager.stop()
        agent_manager = None
        
        return {"message": "Agent simulation stopped.", "status": "stopped"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop simulation: {str(e)}")


@app.get("/simulation/status")
async def get_simulation_status():
    """Get the current status of the simulation."""
    global agent_manager
    
    is_running = agent_manager and agent_manager.is_running()
    
    return {
        "running": is_running,
        "message": "Simulation is running" if is_running else "Simulation is stopped"
    }

# Agent Endpoints
@app.get("/agents/{agent_id}/tasks")
def get_agent_tasks(agent_id: int):
    """Get the to-do list for a specific agent."""
    try:
        with Session(engine) as session:
            # Verify agent exists
            agent = session.exec(select(Agent).where(Agent.id == agent_id)).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # Get agent's tasks
            tasks = session.exec(
                select(AgentTask)
                .where(AgentTask.agent_id == agent_id)
                .order_by(AgentTask.priority)
            ).all()
            
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "status": task.status.value,
                        "priority": task.priority
                    }
                    for task in tasks
                ]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching agent tasks: {str(e)}")

# Conversation Endpoints
@app.get("/conversations/{conversation_id}/messages", response_model=List[Message])
def get_conversation_messages(conversation_id: int):
    """
    Get the message history for a specific conversation.
    """
    with Session(engine) as session:
        return session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp)
        ).all()
        

if __name__ == "__main__":
    # This allows running the app directly for development
    # uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
    
    # Example of how to start the app and run the simulation
    # (for local testing without a separate process)
    async def main():
        config = uvicorn.Config("api.main:app", host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        
        # Start the server and the simulation concurrently
        await server.serve()

    asyncio.run(main())
