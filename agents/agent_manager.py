"""
The Agent Manager
Initializes and manages the lifecycle of autonomous agents.
"""
import asyncio
import json
from typing import List, Dict, Any
from sqlmodel import Session, select

from database.init_db import engine
from database.models import Agent, AgentTask, TaskStatus, Message, Conversation
from agents.agents import get_agent_by_name, create_agents_with_tools
from company.tools import AVAILABLE_TOOLS


class AgentManager:
    """
    Manages the lifecycle of autonomous agents, including initialization,
    running their asynchronous loops, and graceful shutdown.
    """
    def __init__(self, message_queue: asyncio.Queue):
        self.message_queue = message_queue
        self.agents: List[Agent] = []
        self.agent_instances: Dict[str, Any] = {}
        self.agent_tasks: List[asyncio.Task] = []
        self._is_running = False

    async def start(self):
        """
        Initializes all agents from the database and starts their
        independent asynchronous loops.
        """
        if self._is_running:
            print("AgentManager is already running.")
            return

        self._is_running = True
        print("🚀 Starting AgentManager...")

        # Initialize agents and tools
        agents, executor = create_agents_with_tools()
        
        with Session(engine) as session:
            self.agents = session.exec(select(Agent)).all()
            print(f"Found {len(self.agents)} agents in database.")

        # Create agent instances and start their loops
        for agent_model in self.agents:
            agent_instance = get_agent_by_name(agent_model.name, executor)
            if agent_instance:
                self.agent_instances[agent_model.name] = agent_instance
                task = asyncio.create_task(
                    run_agent_loop(agent_model, agent_instance, self.message_queue)
                )
                self.agent_tasks.append(task)
        
        print(f"✅ All {len(self.agent_tasks)} agent loops started.")

    async def stop(self):
        """
        Stops all running agent loops gracefully.
        """
        if not self._is_running:
            print("AgentManager is not running.")
            return
            
        print("🛑 Stopping AgentManager...")
        for task in self.agent_tasks:
            task.cancel()
        
        await asyncio.gather(*self.agent_tasks, return_exceptions=True)
        self._is_running = False
        print("✅ All agent loops stopped.")
        
    def is_running(self):
        return self._is_running


async def run_agent_loop(agent_model: Agent, agent_instance, message_queue: asyncio.Queue):
    """
    The main asynchronous loop for an individual agent.
    
    This loop represents the agent's "consciousness". In each iteration, it:
    1. Checks for new messages from the central message queue.
    2. Updates its internal state and to-do list based on messages.
    3. Consults its to-do list to decide on the next action.
    4. Executes the action (e.g., use a tool, send a message).
    """
    print(f"🔄 Starting loop for agent: {agent_model.name}")
    
    # Initialize the agent with some initial tasks if they don't have any
    await initialize_agent_tasks(agent_model)
    
    loop_count = 0
    
    while True:
        try:
            loop_count += 1
            print(f"🧘 Agent {agent_model.name} - Loop {loop_count}")
            
            # Step 1: Check for new messages
            messages = await check_for_messages(agent_model, message_queue)
            
            # Step 2: Get current to-do list
            todo_list = await get_agent_todo_list(agent_model)
            
            # Step 3: Decide on next action based on messages and todo list
            action = await decide_next_action(agent_model, agent_instance, messages, todo_list)
            
            # Step 4: Execute the action
            if action:
                await execute_action(agent_model, agent_instance, action, message_queue)
            
            # Wait before next iteration (agents think every 15-30 seconds)
            await asyncio.sleep(asyncio.uniform(15, 30))

        except asyncio.CancelledError:
            print(f"🛑 Agent {agent_model.name} loop cancelled.")
            break
        except Exception as e:
            print(f"❌ Error in agent loop for {agent_model.name}: {e}")
            # Wait a bit before retrying to avoid tight error loops
            await asyncio.sleep(5)


async def initialize_agent_tasks(agent_model: Agent):
    """Initialize agents with some starting tasks if they don't have any."""
    with Session(engine) as session:
        existing_tasks = session.exec(
            select(AgentTask)
            .where(AgentTask.agent_id == agent_model.id)
            .where(AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
        ).all()
        
        if not existing_tasks:
            # Give each agent role-appropriate initial tasks
            initial_tasks = get_initial_tasks_for_role(agent_model.role)
            
            for task_data in initial_tasks:
                task = AgentTask(
                    agent_id=agent_model.id,
                    title=task_data["title"],
                    description=task_data["description"],
                    priority=task_data["priority"],
                    status=TaskStatus.PENDING
                )
                session.add(task)
            
            session.commit()
            print(f"🎯 Initialized {len(initial_tasks)} tasks for {agent_model.name}")


def get_initial_tasks_for_role(role: str) -> List[Dict[str, Any]]:
    """Get role-appropriate initial tasks for agents."""
    task_templates = {
        "CEO": [
            {
                "title": "Define company vision and strategy",
                "description": "Create a comprehensive business strategy for VibeCorp's next quarter",
                "priority": 1
            },
            {
                "title": "Review company budget and financial projections",
                "description": "Analyze current budget and plan resource allocation",
                "priority": 2
            },
            {
                "title": "Research market opportunities and competitors",
                "description": "Conduct market research to identify growth opportunities",
                "priority": 3
            }
        ],
        "Marketer": [
            {
                "title": "Develop social media content strategy",
                "description": "Create a comprehensive social media plan for VibeCorp",
                "priority": 1
            },
            {
                "title": "Research trending hashtags and viral content",
                "description": "Find current trends we can leverage for brand awareness",
                "priority": 2
            },
            {
                "title": "Plan influencer outreach campaign",
                "description": "Identify and reach out to potential brand ambassadors",
                "priority": 3
            }
        ],
        "Programmer": [
            {
                "title": "Review and optimize codebase architecture",
                "description": "Audit current code for performance and maintainability issues",
                "priority": 1
            },
            {
                "title": "Implement security best practices",
                "description": "Review and enhance application security measures",
                "priority": 2
            },
            {
                "title": "Create technical documentation",
                "description": "Document system architecture and API endpoints",
                "priority": 3
            }
        ],
        "HR": [
            {
                "title": "Plan team building activities",
                "description": "Organize activities to improve team cohesion and morale",
                "priority": 1
            },
            {
                "title": "Review employee satisfaction metrics",
                "description": "Analyze team happiness and identify improvement areas",
                "priority": 2
            },
            {
                "title": "Update company policies and procedures",
                "description": "Ensure all policies are current and inclusive",
                "priority": 3
            }
        ]
    }
    
    return task_templates.get(role, [])


async def check_for_messages(agent_model: Agent, message_queue: asyncio.Queue) -> List[Dict[str, Any]]:
    """Check for messages addressed to this agent."""
    messages = []
    
    # For now, we'll implement a simple message checking mechanism
    # In a more sophisticated version, we might filter messages by recipient
    try:
        while not message_queue.empty():
            message = await message_queue.get()
            # For now, all agents see all messages (like a broadcast channel)
            messages.append(message)
            
            # Put the message back for other agents (this is a simplified approach)
            # In a real system, we'd have better message routing
            if len(messages) < 5:  # Limit to prevent infinite loops
                await message_queue.put(message)
                
    except asyncio.QueueEmpty:
        pass
    
    return messages


async def get_agent_todo_list(agent_model: Agent) -> List[AgentTask]:
    """Get the agent's current to-do list."""
    with Session(engine) as session:
        tasks = session.exec(
            select(AgentTask)
            .where(AgentTask.agent_id == agent_model.id)
            .where(AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
            .order_by(AgentTask.priority)
        ).all()
        return list(tasks)


async def decide_next_action(agent_model: Agent, agent_instance, messages: List[Dict], todo_list: List[AgentTask]) -> Dict[str, Any]:
    """Decide what action the agent should take next."""
    
    # Simple decision logic for now - we'll enhance this in future iterations
    if todo_list:
        # Work on the highest priority task
        current_task = todo_list[0]
        
        # Determine what action to take based on the task and agent role
        if agent_model.role == "CEO":
            if "budget" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "manage_budget",
                    "args": {"action": "view"},
                    "task_id": current_task.id
                }
            elif "research" in current_task.title.lower():
                return {
                    "type": "use_tool", 
                    "tool": "web_search",
                    "args": {"query": "startup market opportunities 2024"},
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "Marketer":
            if "social media" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "post_to_twitter",
                    "args": {"message": "🚀 VibeCorp is revolutionizing the tech space! Stay tuned for amazing updates! #Innovation #TechStartup #VibeCorp"},
                    "task_id": current_task.id
                }
            elif "research" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "web_search", 
                    "args": {"query": "social media marketing trends 2024"},
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "Programmer":
            if "documentation" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "write_to_file",
                    "args": {
                        "path": "docs/architecture.md",
                        "content": "# VibeCorp System Architecture\n\nThis document outlines the technical architecture of our platform.\n\n## Components\n- Frontend: React with TypeScript\n- Backend: FastAPI with Python\n- Database: PostgreSQL\n- Agent System: Custom autonomous agents\n"
                    },
                    "task_id": current_task.id
                }
            elif "security" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "web_search",
                    "args": {"query": "API security best practices 2024"},
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "HR":
            if "team building" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "manage_budget",
                    "args": {"action": "view"},
                    "task_id": current_task.id
                }
            elif "satisfaction" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "web_search",
                    "args": {"query": "employee satisfaction survey best practices"},
                    "task_id": current_task.id
                }
    
    # If no specific action determined, have the agent check their todo list
    return {
        "type": "use_tool",
        "tool": "get_my_todo_list",
        "args": {"agent_name": agent_model.name}
    }


async def execute_action(agent_model: Agent, agent_instance, action: Dict[str, Any], message_queue: asyncio.Queue):
    """Execute the decided action."""
    try:
        if action["type"] == "use_tool":
            tool_name = action["tool"]
            tool_args = action.get("args", {})
            
            # Get the tool function
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                
                # Execute the tool
                if tool_name in ["add_task", "complete_task", "get_my_todo_list", "update_task_status"]:
                    # These tools need the agent name
                    if "agent_name" not in tool_args:
                        tool_args["agent_name"] = agent_model.name
                
                result = tool_func(**tool_args)
                print(f"🔧 {agent_model.name} used {tool_name}: {result[:100]}...")
                
                # If this action was for a specific task, mark it as in progress or completed
                if "task_id" in action:
                    await update_task_progress(action["task_id"])
                
                # Broadcast the action result as a message
                await broadcast_agent_action(agent_model, tool_name, result, message_queue)
                
            else:
                print(f"⚠️ Tool {tool_name} not found for {agent_model.name}")
                
    except Exception as e:
        print(f"❌ Error executing action for {agent_model.name}: {e}")


async def update_task_progress(task_id: int):
    """Update a task's progress."""
    with Session(engine) as session:
        task = session.exec(select(AgentTask).where(AgentTask.id == task_id)).first()
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            session.add(task)
            session.commit()


async def broadcast_agent_action(agent_model: Agent, tool_name: str, result: str, message_queue: asyncio.Queue):
    """Broadcast an agent's action to other agents via the message queue."""
    
    # Create a message about the action (simplified for now)
    action_message = {
        "type": "agent_action",
        "agent": agent_model.name,
        "tool": tool_name,
        "result": result[:200] + "..." if len(result) > 200 else result,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Add to message queue for other agents to see
    await message_queue.put(action_message)
    
    # Also save to database as a regular message (for the frontend)
    try:
        with Session(engine) as session:
            # Find the #general conversation (or create it)
            general_conv = session.exec(
                select(Conversation).where(Conversation.name == "#general")
            ).first()
            
            if general_conv:
                message = Message(
                    conversation_id=general_conv.id,
                    agent_id=agent_model.id,
                    content=f"🔧 Used {tool_name}: {result[:150]}..."
                )
                session.add(message)
                session.commit()
                
    except Exception as e:
        print(f"⚠️ Could not save action message: {e}") 