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

def get_superior_for_agent(role: str) -> str:
    """Get the superior agent name for reporting completed tasks."""
    hierarchy = {
        "Programmer": "CeeCee_The_CEO",  # Programmers report to CEO
        "Marketer": "CeeCee_The_CEO",    # Marketer reports to CEO  
        "HR": "CeeCee_The_CEO",          # HR reports to CEO
        "CEO": None                      # CEO has no superior
    }
    return hierarchy.get(role)

def get_helper_for_task(role: str, task_title: str) -> str:
    """Determine who can help with a specific task based on role and task type."""
    task_lower = task_title.lower()
    
    # Technical tasks -> ask programmer
    if any(keyword in task_lower for keyword in ["code", "technical", "architecture", "security", "implementation"]):
        return "Penny_The_Programmer" if role != "Programmer" else "CeeCee_The_CEO"
    
    # Marketing tasks -> ask marketer  
    elif any(keyword in task_lower for keyword in ["marketing", "social", "campaign", "brand", "content"]):
        return "Mark_The_Marketer" if role != "Marketer" else "CeeCee_The_CEO"
    
    # HR/team tasks -> ask HR
    elif any(keyword in task_lower for keyword in ["team", "hr", "employee", "satisfaction", "hiring"]):
        return "Hannah_The_HR" if role != "HR" else "CeeCee_The_CEO"
    
    # Business/strategy tasks -> ask CEO
    elif any(keyword in task_lower for keyword in ["strategy", "business", "market", "budget", "financial"]):
        return "CeeCee_The_CEO" if role != "CEO" else "general"
    
    # Default: ask in general channel
    else:
        return "general"


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
            print(f"📨 {agent_model.name} found {len(messages)} messages")
            
            # Step 2: Get current to-do list
            todo_list = await get_agent_todo_list(agent_model)
            print(f"📋 {agent_model.name} has {len(todo_list)} tasks: {[f'{t.status}:{t.title[:30]}' for t in todo_list[:3]]}")
            
            # Step 3: Decide on next action based on messages and todo list
            action = await decide_next_action(agent_model, agent_instance, messages, todo_list)
            print(f"🎯 {agent_model.name} decided: {action.get('tool', 'no action') if action else 'no action'}")
            
            # Step 4: Execute the action
            if action:
                await execute_action(agent_model, agent_instance, action, message_queue)
            else:
                print(f"⚠️ {agent_model.name} has no action to take")
            
            # Wait before next iteration (agents think every 5-10 seconds for faster testing)
            import random
            sleep_time = random.uniform(5, 10)
            print(f"😴 {agent_model.name} sleeping for {sleep_time:.1f}s")
            await asyncio.sleep(sleep_time)

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
    """Get role-appropriate initial tasks for agents. Only CEO starts with a task - others wait for direction."""
    if role == "CEO":
        return [
            {
                "title": "Initiate team brainstorming session",
                "description": "Start a discussion in #general to brainstorm our company's business idea, product vision, and initial goals. Get input from all team members to build consensus.",
                "priority": 1
            }
        ]
    else:
        # All other agents start with no tasks - they wait for the CEO to give direction
        # after the initial brainstorming session
        return []


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
    
    # Purpose-driven communication - only communicate when there's a business need
    import random
    
    # 1. Report completed high-priority tasks to superior
    if todo_list:
        completed_tasks = [t for t in todo_list if t.status == TaskStatus.COMPLETED and t.priority <= 2]
        print(f"🎯 {agent_model.name} has {len(completed_tasks)} completed high-priority tasks")
        if completed_tasks:
            completed_task = completed_tasks[0]
            superior = get_superior_for_agent(agent_model.role)
            print(f"🎯 {agent_model.name} should report to superior: {superior}")
            if superior:
                print(f"📤 {agent_model.name} sending DM to {superior} about completed task")
                return {
                    "type": "use_tool",
                    "tool": "send_direct_message",
                    "args": {
                        "agent_name": agent_model.name, 
                        "recipient_agent": superior, 
                        "message": f"Update: Completed '{completed_task.title}'. {completed_task.description}. Ready for next assignment."
                    }
                }
    
    # 2. Ask for help when blocked (immediately, not randomly)
    if todo_list:
        blocked_tasks = [t for t in todo_list if t.status == TaskStatus.BLOCKED]
        if blocked_tasks:
            blocked_task = blocked_tasks[0]
            helper = get_helper_for_task(agent_model.role, blocked_task.title)
            if helper == "general":
                return {
                    "type": "use_tool",
                    "tool": "ask_for_help",
                    "args": {
                        "agent_name": agent_model.name,
                        "topic": blocked_task.title,
                        "details": f"Blocked on '{blocked_task.title}': {blocked_task.description}. Need guidance to proceed."
                    }
                }
            else:
                return {
                    "type": "use_tool",
                    "tool": "send_direct_message",
                    "args": {
                        "agent_name": agent_model.name,
                        "recipient_agent": helper,
                        "message": f"Need help with '{blocked_task.title}': {blocked_task.description}. Could you clarify requirements or dependencies?"
                    }
                }
    
    # 3. CEO assigns new tasks when they have capacity and others need work
    if agent_model.role == "CEO" and todo_list and not any(t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS] for t in todo_list):
        # CEO has completed their tasks, should delegate new work
        return {
            "type": "use_tool",
            "tool": "assign_task_to_agent",
            "args": {
                "assigner_name": agent_model.name,
                "agent_name": "Penny_The_Programmer",  # Could be made smarter based on workload
                "title": "Implement priority feature from market research",
                "description": "Based on completed market analysis, develop the highest priority feature identified",
                "priority": 1
            }
        }
    
    # Focus on work only if there are pending/in-progress tasks AND no communication needs
    if todo_list and any(t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS] for t in todo_list):
        # Work on the highest priority task
        current_task = todo_list[0]
        print(f"🎯 {agent_model.name} working on: '{current_task.title}' (status: {current_task.status})")
        
        # Determine what action to take based on the task and agent role
        # Reduce web searches and add more diverse actions
        if agent_model.role == "CEO":
            if "budget" in current_task.title.lower() or "financial" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "manage_budget",
                    "args": {"action": "view"},
                    "task_id": current_task.id
                }
            elif "brainstorm" in current_task.title.lower() or "discussion" in current_task.title.lower():
                # Start team brainstorming in general channel
                return {
                    "type": "use_tool",
                    "tool": "send_message_to_channel",
                    "args": {
                        "agent_name": agent_model.name,
                        "channel_name": "#general",
                        "message": "🚀 Team! Time for our GAME-CHANGING brainstorming session! 💡 Let's disrupt the market with our REVOLUTIONARY business idea! What product should VibeCorp build to DOMINATE our industry? I want to hear EVERYONE's thoughts - this is our MOONSHOT moment! 🌟"
                    },
                    "task_id": current_task.id
                }
            elif "research" in current_task.title.lower() or "market" in current_task.title.lower():
                # Only research if it's specifically a research task
                return {
                    "type": "use_tool", 
                    "tool": "web_search",
                    "args": {"agent_name": agent_model.name, "query": f"{current_task.title[:50]}"},
                    "task_id": current_task.id
                }
            else:
                # CEO fallback: communicate with team instead of creating files
                return {
                    "type": "use_tool",
                    "tool": "send_message_to_channel",
                    "args": {
                        "agent_name": agent_model.name,
                        "channel_name": "#general",
                        "message": f"📈 Team, I'm working on {current_task.title}! This is CRITICAL for our success! Let me know if anyone has insights or needs clarification on our strategic direction! 💯"
                    },
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "Marketer":
            if "social" in current_task.title.lower() or "marketing" in current_task.title.lower() or "campaign" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "write_tweet",
                    "args": {"agent_name": agent_model.name, "message": "🚀 VibeCorp is revolutionizing the tech space! Stay tuned for amazing updates! #Innovation #TechStartup #VibeCorp"},
                    "task_id": current_task.id
                }
            elif "research" in current_task.title.lower() or "trend" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "web_search", 
                    "args": {"agent_name": agent_model.name, "query": "social media marketing 2024"},
                    "task_id": current_task.id
                }
            else:
                # Marketer fallback: create content
                return {
                    "type": "use_tool",
                    "tool": "write_tweet",
                    "args": {"agent_name": agent_model.name, "message": f"📱 Working on {current_task.title}! Exciting things coming from VibeCorp! #Marketing #Innovation"},
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "Programmer":
            if "research" in current_task.title.lower() and ("security" in current_task.title.lower() or "best practices" in current_task.title.lower()):
                # Only do web search for explicit research tasks
                return {
                    "type": "use_tool",
                    "tool": "web_search",
                    "args": {"agent_name": agent_model.name, "query": f"{current_task.title[:50]}"},
                    "task_id": current_task.id
                }
            else:
                # Programmer fallback: ask for clarification instead of auto-generating files
                return {
                    "type": "use_tool",
                    "tool": "send_message_to_channel",
                    "args": {
                        "agent_name": agent_model.name,
                        "channel_name": "#engineering",
                        "message": f"🔧 Working on: {current_task.title}. Need some clarification on requirements and scope. What specific deliverables are expected for this task?"
                    },
                    "task_id": current_task.id
                }
                
        elif agent_model.role == "HR":
            if "team" in current_task.title.lower() or "building" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "manage_budget",
                    "args": {"action": "view"},
                    "task_id": current_task.id
                }
            elif "research" in current_task.title.lower() and ("satisfaction" in current_task.title.lower() or "survey" in current_task.title.lower()):
                # Only research for explicit research tasks
                return {
                    "type": "use_tool",
                    "tool": "web_search",
                    "args": {"agent_name": agent_model.name, "query": f"{current_task.title[:50]}"},
                    "task_id": current_task.id
                }
            else:
                # HR fallback: communicate with team instead of auto-generating files
                return {
                    "type": "use_tool",
                    "tool": "send_message_to_channel",
                    "args": {
                        "agent_name": agent_model.name,
                        "channel_name": "#general",
                        "message": f"👥 Hi team! I'm working on {current_task.title}. Would love to get everyone's input on this. How do you think we should approach this from an HR perspective?"
                    },
                    "task_id": current_task.id
                }
    
    # If no specific action determined, try to communicate or check todo list
    # If they have completed tasks, they're more likely to share updates
    if todo_list and any(t.status == TaskStatus.COMPLETED for t in todo_list):
        if random.random() < 0.7:  # 70% chance to share completion update
            completed_tasks = [t for t in todo_list if t.status == TaskStatus.COMPLETED]
            completed_task = completed_tasks[0]
            return {
                "type": "use_tool",
                "tool": "share_update",
                "args": {"agent_name": agent_model.name, "update": f"Great news! I just completed '{completed_task.title}'. What should I focus on next?"}
            }
    
    # If agent has no pending/in-progress tasks, create meaningful follow-up work instead of just checking todo list
    if not todo_list or not any(t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS] for t in todo_list):
        # Create role-appropriate follow-up tasks instead of endless todo list checking
        if agent_model.role == "CEO":
            return {
                "type": "use_tool",
                "tool": "add_task",
                "args": {
                    "agent_name": agent_model.name,
                    "title": "Review team progress and strategic priorities",
                    "description": "Check on team progress, identify bottlenecks, and set strategic direction for next phase",
                    "priority": 2
                }
            }
        elif agent_model.role == "Programmer":
            return {
                "type": "use_tool",
                "tool": "add_task", 
                "args": {
                    "agent_name": agent_model.name,
                    "title": "Code review and optimization",
                    "description": "Review existing code, identify optimization opportunities, and improve system performance",
                    "priority": 3
                }
            }
        elif agent_model.role == "Marketer":
            return {
                "type": "use_tool",
                "tool": "add_task",
                "args": {
                    "agent_name": agent_model.name,
                    "title": "Content creation and brand development",
                    "description": "Create engaging content, develop brand messaging, and plan marketing campaigns",
                    "priority": 2
                }
            }
        elif agent_model.role == "HR":
            return {
                "type": "use_tool",
                "tool": "add_task",
                "args": {
                    "agent_name": agent_model.name,
                    "title": "Team wellness and culture assessment",
                    "description": "Assess team morale, identify culture improvement opportunities, and plan team building initiatives",
                    "priority": 3
                }
            }
    
    # Otherwise, check their todo list (but this should be rare now)
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
                tools_needing_agent_name = [
                    "add_task", "complete_task", "get_my_todo_list", "update_task_status",
                    "write_to_file", "read_file", "list_files", "write_tweet",
                    "share_file_with_agent", "copy_to_project", "web_search",
                    "send_message_to_channel", "send_direct_message", "ask_for_help", "share_update"
                ]
                if tool_name in tools_needing_agent_name:
                    # These tools need the agent name
                    if "agent_name" not in tool_args:
                        tool_args["agent_name"] = agent_model.name
                
                # Check if the tool is async and await it if necessary
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(tool_func):
                    result = await tool_func(**tool_args)
                else:
                    result = tool_func(**tool_args)
                print(f"🔧 {agent_model.name} used {tool_name}: {result[:100]}...")
                
                # If this action was for a specific task, mark it as in progress or completed
                if "task_id" in action:
                    await update_task_progress(action["task_id"], tool_name)
                
                # Broadcast the action result as a message
                await broadcast_agent_action(agent_model, tool_name, result, message_queue)
                
            else:
                print(f"⚠️ Tool {tool_name} not found for {agent_model.name}")
                
    except Exception as e:
        print(f"❌ Error executing action for {agent_model.name}: {e}")


async def update_task_progress(task_id: int, tool_name: str):
    """Update a task's progress and potentially complete it."""
    with Session(engine) as session:
        task = session.exec(select(AgentTask).where(AgentTask.id == task_id)).first()
        if not task:
            return
            
        # Move from pending to in_progress
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            session.add(task)
            session.commit()
            print(f"📋 Task {task_id} marked as IN_PROGRESS")
            
        # After working on a task, there's a chance to complete it
        elif task.status == TaskStatus.IN_PROGRESS:
            # Some tools indicate task completion
            completion_tools = ["write_to_file", "post_to_twitter", "manage_budget", "web_search"]
            
            # 30% chance to complete task after working on it, 80% if using completion tools
            import random
            completion_chance = 0.8 if tool_name in completion_tools else 0.3
            
            if random.random() < completion_chance:
                task.status = TaskStatus.COMPLETED
                session.add(task)
                session.commit()
                print(f"✅ Task {task_id} marked as COMPLETED: {task.title}")
                
                # Broadcast task completion
                try:
                    from api.main import broadcast_task_list_update
                    await broadcast_task_list_update(task.agent_id)
                except ImportError:
                    pass
            
            # Broadcast task list update
            try:
                from api.main import broadcast_task_list_update
                await broadcast_task_list_update(task.agent_id)
            except ImportError:
                pass  # Avoid circular import issues


async def broadcast_agent_action(agent_model: Agent, tool_name: str, result: str, message_queue: asyncio.Queue):
    """Update agent status and broadcast activity to frontend (but not to chat channels)."""
    
    # Create a message about the action for other agents to see
    action_message = {
        "type": "agent_action",
        "agent": agent_model.name,
        "tool": tool_name,
        "result": result[:200] + "..." if len(result) > 200 else result,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Add to message queue for other agents to see (internal communication)
    await message_queue.put(action_message)
    
    # Update agent status based on the tool they're using
    status_map = {
        "web_search": "researching",
        "write_to_file": "coding", 
        "read_file": "reviewing_code",
        "list_files": "organizing",
        "add_task": "planning",
        "complete_task": "completing_work",
        "get_my_todo_list": "planning"
    }
    
    new_status = status_map.get(tool_name, "working")
    
    # Update the agent's status in the database
    try:
        with Session(engine) as session:
            agent = session.get(Agent, agent_model.id)
            if agent:
                agent.status = new_status
                session.add(agent)
                session.commit()
                
                # Broadcast status update to frontend via WebSocket
                try:
                    from api.main import broadcast_agent_status_update
                    await broadcast_agent_status_update(agent.id, new_status)
                except ImportError:
                    pass
                    
    except Exception as e:
        print(f"⚠️ Could not update agent status: {e}")
        
    # Only send a message to chat if it's something worth sharing (like completing a major task)
    # Most tool usage should just update status, not spam chat 