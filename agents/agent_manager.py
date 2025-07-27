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
    
    # Track messages this agent has already responded to (PERSISTENT across loops)
    responded_messages = set()
    
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
            action = await decide_next_action(agent_model, agent_instance, messages, todo_list, responded_messages)
            print(f"🎯 {agent_model.name} decided: {action.get('tool', 'no action') if action else 'no action'}")
            
            # Step 4: Execute the action
            if action:
                await execute_action(agent_model, agent_instance, action, message_queue)
            else:
                print(f"⚠️ {agent_model.name} has no action to take")
            
            # Wait before next iteration (faster response times for better planning)
            import random
            sleep_time = random.uniform(2, 5)  # Reduced from 5-10 seconds for faster responses
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


async def check_brainstorming_progress(agent_model: Agent) -> List[Dict[str, str]]:
    """Check recent brainstorming messages to see if we have enough input for decision making."""
    brainstorm_messages = []
    
    try:
        with Session(engine) as session:
            # Get the #general conversation
            general_conv = session.exec(
                select(Conversation).where(Conversation.name == "#general")
            ).first()
            
            if not general_conv:
                print(f"⚠️ No #general conversation found")
                return brainstorm_messages
            
            # Get messages from last 15 minutes from other agents (extended window)
            import datetime
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=15)
            
            recent_messages = session.exec(
                select(Message, Agent)
                .join(Agent, Message.agent_id == Agent.id)
                .where(Message.conversation_id == general_conv.id)
                .where(Message.timestamp > cutoff_time)
                .where(Message.agent_id != agent_model.id)  # Exclude CEO's own messages
                .order_by(Message.timestamp.desc())
            ).all()
            
            print(f"🔍 Found {len(recent_messages)} recent messages in #general for {agent_model.name}")
            
            # Extract relevant brainstorming content
            for msg, sender in recent_messages:
                # Look for substantive brainstorming content (not just acknowledgments)
                content = msg.content.lower()
                if any(keyword in content for keyword in ["think", "should", "consider", "idea", "product", "build", "saas", "platform", "tool", "focus", "market", "business"]):
                    brainstorm_messages.append({
                        "sender": sender.name,
                        "role": sender.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    })
                    print(f"💡 Found brainstorming input from {sender.name}: {msg.content[:50]}...")
    
    except Exception as e:
        print(f"⚠️ Error checking brainstorming progress: {e}")
    
    print(f"📊 Total brainstorming messages found: {len(brainstorm_messages)}")
    return brainstorm_messages


def get_initial_tasks_for_role(role: str) -> List[Dict[str, Any]]:
    """Get role-appropriate initial tasks for agents. Only CEO starts with a task - others wait for direction."""
    if role == "CEO":
        return [
            {
                "title": "Initiate team brainstorming session",
                "description": "Start a discussion in #general to brainstorm our company's business idea, product vision, and initial goals. Collect input from all team members, then make a decision and assign specific tasks to move forward.",
                "priority": 1
            }
        ]
    else:
        # All other agents start with no tasks - they wait for the CEO to give direction
        # after the initial brainstorming session
        return []


async def check_for_messages(agent_model: Agent, message_queue: asyncio.Queue) -> List[Dict[str, Any]]:
    """Check for new chat messages from channels this agent should see."""
    messages = []
    
    # Check for new chat messages from the database
    try:
        with Session(engine) as session:
            # Get recent messages from channels this agent should see
            # For now, all agents see #general and role-specific channels
            relevant_channels = ["#general"]
            if agent_model.role in ["Programmer", "PM"]:
                relevant_channels.append("#engineering")
            
            # Get conversations for these channels
            conversations = session.exec(
                select(Conversation).where(Conversation.name.in_(relevant_channels))
            ).all()
            
            # Check for recent messages (last 10 minutes) that this agent hasn't seen
            import datetime
            cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
            
            for conv in conversations:
                recent_messages = session.exec(
                    select(Message, Agent)
                    .join(Agent, Message.agent_id == Agent.id)
                    .where(Message.conversation_id == conv.id)
                    .where(Message.timestamp > cutoff_time)
                    .where(Message.agent_id != agent_model.id)  # Don't see own messages
                    .order_by(Message.timestamp.desc())
                    .limit(5)
                ).all()
                
                for msg, sender in recent_messages:
                    messages.append({
                        "type": "chat_message",
                        "channel": conv.name,
                        "sender": sender.name,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    })
    
    except Exception as e:
        print(f"⚠️ Error checking messages for {agent_model.name}: {e}")
    
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


async def decide_next_action(agent_model: Agent, agent_instance, messages: List[Dict], todo_list: List[AgentTask], responded_messages: set) -> Dict[str, Any]:
    """Decide what action the agent should take next."""
    
    # Purpose-driven communication - only communicate when there's a business need
    import random
    
    # 0. Respond to recent messages if relevant (high priority)
    if messages:
        for message in messages:
            if message.get("type") == "chat_message":
                sender = message.get("sender")
                content = message.get("content", "").lower()
                channel = message.get("channel")
                timestamp = message.get("timestamp", "")
                
                # Create a unique message ID that includes timestamp to prevent re-responses
                message_id = f"{sender}:{timestamp}:{content[:30]}"
                
                # Skip if we've already responded to this message
                if message_id in responded_messages:
                    continue
                
                # Respond to brainstorming requests from CEO
                if sender == "CeeCee_The_CEO" and ("brainstorm" in content or "business idea" in content or "thoughts" in content):
                    # Mark this message as responded to
                    responded_messages.add(message_id)
                    
                    if agent_model.role == "Programmer":
                        return {
                            "type": "use_tool",
                            "tool": "send_message_to_channel",
                            "args": {
                                "agent_name": agent_model.name,
                                "channel_name": "#general",
                                "message": "💡 Great question! I think we should build a SaaS platform that helps small businesses automate their workflows. There's huge demand for no-code automation tools! What do you think team?"
                            }
                        }
                    elif agent_model.role == "Marketer":
                        return {
                            "type": "use_tool",
                            "tool": "send_message_to_channel",
                            "args": {
                                "agent_name": agent_model.name,
                                "channel_name": "#general", 
                                "message": "🚀 I love the energy! From a marketing perspective, I think we should focus on a B2B productivity tool - maybe project management or team collaboration. The market is hot right now! 📈"
                            }
                        }
                    elif agent_model.role == "HR":
                        return {
                            "type": "use_tool",
                            "tool": "send_message_to_channel",
                            "args": {
                                "agent_name": agent_model.name,
                                "channel_name": "#general",
                                "message": "👥 Excited to brainstorm! I think we should consider something in the HR tech space - maybe employee engagement or remote work tools. What about a platform that helps distributed teams stay connected? 🌍"
                            }
                        }
    
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
        
        # If task is pending, start working on it
        if current_task.status == TaskStatus.PENDING:
            # Mark task as in progress and do the work
            with Session(engine) as session:
                task = session.get(AgentTask, current_task.id)
                if task:
                    task.status = TaskStatus.IN_PROGRESS
                    session.add(task)
                    session.commit()
            
            # Now determine what action to take based on the task and agent role
        elif current_task.status == TaskStatus.IN_PROGRESS:
            # For tasks already in progress, agents can choose to:
            # 1. Continue working on them with tools
            # 2. Complete them if they feel the work is done
            # 3. Update priority or delegate if needed
            print(f"🔄 {agent_model.name} continuing work on in-progress task: {current_task.title}")
            
            # Agents have full access to task management tools and can complete tasks when they choose
            
            # For brainstorming/discussion tasks, communication is the primary tool
            if any(keyword in current_task.title.lower() for keyword in ["brainstorm", "discussion", "initiate"]):
                if agent_model.role == "CEO":
                    # Check if brainstorming has enough responses to make a decision
                    brainstorm_messages = await check_brainstorming_progress(agent_model)
                    
                    if len(brainstorm_messages) >= 2:  # Got input from team - reduced threshold
                        # Time to make a decision and assign tasks
                        print(f"🎯 CEO {agent_model.name} has enough brainstorming input ({len(brainstorm_messages)} messages), making decision...")
                        return {
                            "type": "use_tool",
                            "tool": "make_business_decision",
                            "args": {
                                "agent_name": agent_model.name,
                                "brainstorm_messages": brainstorm_messages,
                                "task_id": current_task.id
                            }
                        }
                    elif len(brainstorm_messages) >= 1:
                        # Check if we've been waiting long enough (2+ minutes) to make decision with fewer inputs
                        if brainstorm_messages:
                            import datetime
                            oldest_message_time = datetime.datetime.fromisoformat(brainstorm_messages[-1]["timestamp"])
                            time_elapsed = datetime.datetime.now() - oldest_message_time
                            
                            if time_elapsed.total_seconds() > 120:  # 2 minutes (even faster)
                                print(f"⏰ CEO {agent_model.name} making decision with {len(brainstorm_messages)} messages after 2+ minutes")
                                return {
                                    "type": "use_tool",
                                    "tool": "make_business_decision",
                                    "args": {
                                        "agent_name": agent_model.name,
                                        "brainstorm_messages": brainstorm_messages,
                                        "task_id": current_task.id
                                    }
                                }
                        
                        # Still waiting for more input, but push for responses
                        return {
                            "type": "use_tool",
                            "tool": "send_message_to_channel",
                            "args": {
                                "agent_name": agent_model.name,
                                "channel_name": "#general",
                                "message": "⏰ I need to hear from EVERYONE on our product direction! Time is MONEY and we need to move FAST! What's your take on what VibeCorp should build?"
                            },
                            "task_id": current_task.id
                        }
                    else:
                        # First time or not enough responses yet
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
                else:
                    # Other agents participate in brainstorming when they have such tasks
                    return {
                        "type": "use_tool",
                        "tool": "send_message_to_channel",
                        "args": {
                            "agent_name": agent_model.name,
                            "channel_name": "#general",
                            "message": f"💡 Great to participate in this brainstorming! From my {agent_model.role} perspective, I think we should consider..."
                        },
                        "task_id": current_task.id
                    }
            
            # For research tasks, web search is appropriate
            elif "research" in current_task.title.lower():
                return {
                    "type": "use_tool",
                    "tool": "web_search",
                    "args": {"agent_name": agent_model.name, "query": f"{current_task.title[:50]}"},
                    "task_id": current_task.id
                }
            
            # For file/documentation tasks, use file tools
            elif any(keyword in current_task.title.lower() for keyword in ["create", "write", "document", "file"]):
                # Determine what type of deliverable to create based on the task
                if "code" in current_task.title.lower() or "system" in current_task.title.lower():
                    # Programming task - create actual code
                    if agent_model.role == "Programmer":
                        if "authentication" in current_task.title.lower() or "auth" in current_task.title.lower():
                            return {
                                "type": "use_tool",
                                "tool": "create_code_file",
                                "args": {
                                    "agent_name": agent_model.name,
                                    "filename": "auth_system.py",
                                    "code_content": """# User Authentication System\nfrom datetime import datetime, timedelta\nfrom typing import Optional\nimport hashlib\nimport jwt\n\nclass AuthSystem:\n    def __init__(self):\n        self.users = {}\n        self.secret_key = \"your-secret-key\"\n    \n    def hash_password(self, password: str) -> str:\n        return hashlib.sha256(password.encode()).hexdigest()\n    \n    def register_user(self, username: str, password: str, email: str) -> bool:\n        if username in self.users:\n            return False\n        \n        self.users[username] = {\n            \"password\": self.hash_password(password),\n            \"email\": email,\n            \"created_at\": datetime.utcnow().isoformat(),\n            \"is_active\": True\n        }\n        return True\n    \n    def login_user(self, username: str, password: str) -> Optional[str]:\n        user = self.users.get(username)\n        if not user or user[\"password\"] != self.hash_password(password):\n            return None\n        \n        token = jwt.encode({\n            \"username\": username,\n            \"exp\": datetime.utcnow() + timedelta(hours=24)\n        }, self.secret_key, algorithm=\"HS256\")\n        \n        return token\n    \n    def verify_token(self, token: str) -> Optional[str]:\n        try:\n            payload = jwt.decode(token, self.secret_key, algorithms=[\"HS256\"])\n            return payload[\"username\"]\n        except jwt.ExpiredSignatureError:\n            return None""",
                                    "language": "python"
                                },
                                "task_id": current_task.id
                            }
                        elif "dashboard" in current_task.title.lower() or "interface" in current_task.title.lower():
                            return {
                                "type": "use_tool",
                                "tool": "create_code_file",
                                "args": {
                                    "agent_name": agent_model.name,
                                    "filename": "dashboard.html",
                                    "code_content": """<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>VibeCorp Dashboard</title>\n    <link rel="stylesheet" href="dashboard.css">\n</head>\n<body>\n    <div class="dashboard-container">\n        <header class="dashboard-header">\n            <h1>VibeCorp Dashboard</h1>\n            <div class="user-info">\n                <span id="username">Welcome, User!</span>\n                <button onclick="logout()">Logout</button>\n            </div>\n        </header>\n        \n        <nav class="sidebar">\n            <ul>\n                <li><a href="#overview" class="nav-link active">Overview</a></li>\n                <li><a href="#projects" class="nav-link">Projects</a></li>\n                <li><a href="#analytics" class="nav-link">Analytics</a></li>\n                <li><a href="#settings" class="nav-link">Settings</a></li>\n            </ul>\n        </nav>\n        \n        <main class="main-content">\n            <div id="overview" class="tab-content active">\n                <h2>Project Overview</h2>\n                <div class="stats-grid">\n                    <div class="stat-card">\n                        <h3>Active Projects</h3>\n                        <span class="stat-number">3</span>\n                    </div>\n                    <div class="stat-card">\n                        <h3>Completed Tasks</h3>\n                        <span class="stat-number">27</span>\n                    </div>\n                    <div class="stat-card">\n                        <h3>Team Members</h3>\n                        <span class="stat-number">4</span>\n                    </div>\n                </div>\n            </div>\n            \n            <div id="projects" class="tab-content">\n                <h2>Projects</h2>\n                <div class="project-list">\n                    <div class="project-card">\n                        <h3>User Authentication</h3>\n                        <p>Status: In Progress</p>\n                        <div class="progress-bar">\n                            <div class="progress" style="width: 75%"></div>\n                        </div>\n                    </div>\n                </div>\n            </div>\n        </main>\n    </div>\n    \n    <script src="dashboard.js"></script>\n</body>\n</html>""",
                                    "language": "html"
                                },
                                "task_id": current_task.id
                            }
                        else:
                            # Generic code creation
                            return {
                                "type": "use_tool",
                                "tool": "create_code_file",
                                "args": {
                                    "agent_name": agent_model.name,
                                    "filename": f"{current_task.title.lower().replace(' ', '_')}.py",
                                    "code_content": f"# {current_task.title}\n# Generated by {agent_model.name}\n\nclass {current_task.title.replace(' ', '').title()}:\n    def __init__(self):\n        self.initialized = True\n        print(f'LOG: {current_task.title} initialized successfully')\n    \n    def execute(self):\n        # TODO: Implement {current_task.title.lower()} functionality\n        print(f'LOG: Executing {current_task.title.lower()}...')\n        return True\n\nif __name__ == '__main__':\n    system = {current_task.title.replace(' ', '').title()}()\n    result = system.execute()\n    print(f'LOG: {current_task.title} completed with result: {{result}}')",
                                    "language": "python"
                                },
                                "task_id": current_task.id
                            }
                            
                elif "landing page" in current_task.title.lower() or "marketing" in current_task.title.lower():
                    # Marketing task - create marketing materials
                    if agent_model.role == "Marketer":
                        return {
                            "type": "use_tool",
                            "tool": "create_code_file",
                            "args": {
                                "agent_name": agent_model.name,
                                "filename": "landing_page.html",
                                "code_content": """<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>VibeCorp - Revolutionary Business Solutions</title>\n    <style>\n        * { margin: 0; padding: 0; box-sizing: border-box; }\n        body { font-family: Arial, sans-serif; line-height: 1.6; }\n        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 100px 0; text-align: center; }\n        .hero h1 { font-size: 3em; margin-bottom: 20px; }\n        .hero p { font-size: 1.2em; margin-bottom: 30px; }\n        .cta-button { background: #ff6b6b; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 1.1em; cursor: pointer; }\n        .features { padding: 80px 0; background: #f8f9fa; }\n        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }\n        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px; margin-top: 50px; }\n        .feature-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); text-align: center; }\n        .feature-card h3 { color: #333; margin-bottom: 15px; }\n        .pricing { padding: 80px 0; text-align: center; }\n        .price-card { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); max-width: 300px; margin: 20px auto; }\n    </style>\n</head>\n<body>\n    <section class="hero">\n        <div class="container">\n            <h1>🚀 VibeCorp</h1>\n            <p>Revolutionary Business Solutions That Disrupt Industries</p>\n            <button class="cta-button" onclick="alert('Coming Soon!')">Get Started Now</button>\n        </div>\n    </section>\n    \n    <section class="features">\n        <div class="container">\n            <h2 style="text-align: center; margin-bottom: 20px;">Game-Changing Features</h2>\n            <div class="feature-grid">\n                <div class="feature-card">\n                    <h3>💡 AI-Powered Insights</h3>\n                    <p>Leverage cutting-edge artificial intelligence to optimize your workflow and maximize synergies.</p>\n                </div>\n                <div class="feature-card">\n                    <h3>📈 Scalable Solutions</h3>\n                    <p>Our platform grows with your business, delivering enterprise-grade performance at startup speed.</p>\n                </div>\n                <div class="feature-card">\n                    <h3>🌟 Revolutionary UX</h3>\n                    <p>Intuitive interface designed to disrupt traditional workflows and accelerate your success.</p>\n                </div>\n            </div>\n        </div>\n    </section>\n    \n    <section class="pricing">\n        <div class="container">\n            <h2>Disruptive Pricing</h2>\n            <div class="price-card">\n                <h3>Starter Plan</h3>\n                <p><strong>$99/month</strong></p>\n                <p>Perfect for startups ready to scale</p>\n                <button class="cta-button">Choose Plan</button>\n            </div>\n        </div>\n    </section>\n</body>\n</html>""",
                                "language": "html"
                            },
                            "task_id": current_task.id
                        }
                        
                elif "process" in current_task.title.lower() or "document" in current_task.title.lower():
                    # Documentation task - create process docs
                    return {
                        "type": "use_tool",
                        "tool": "write_to_file",
                        "args": {
                            "agent_name": agent_model.name,
                            "path": f"{current_task.title.lower().replace(' ', '_')}.md",
                            "content": f"# {current_task.title}\n\n{current_task.description}\n\n## Process Overview\n\n1. **Planning Phase**\n   - Define requirements and scope\n   - Create timeline and milestones\n\n2. **Implementation Phase**\n   - Execute planned work\n   - Regular progress updates\n\n3. **Review Phase**\n   - Quality assurance\n   - Stakeholder feedback\n\n4. **Deployment Phase**\n   - Production deployment\n   - User testing and feedback\n\n---\n\n*Created by {agent_model.name} on {datetime.utcnow().strftime('%Y-%m-%d')}*",
                            "location": "project"
                        },
                        "task_id": current_task.id
                    }
                else:
                    # Fallback - create a basic file
                    return {
                        "type": "use_tool",
                        "tool": "write_to_file",
                        "args": {
                            "agent_name": agent_model.name,
                            "path": f"{current_task.title.lower().replace(' ', '_')}.md",
                            "content": f"# {current_task.title}\n\n{current_task.description}\n\nWork in progress by {agent_model.name}.",
                            "location": "project"
                        },
                        "task_id": current_task.id
                    }
        
        # Default: agents can choose to work on tasks through communication or ask for clarification
        else:
            # Special handling for CEO review tasks - check if it's time to make decisions
            if agent_model.role == "CEO" and "review team progress" in current_task.title.lower():
                # Check if we have enough brainstorming input to make a decision
                brainstorm_messages = await check_brainstorming_progress(agent_model)
                
                if len(brainstorm_messages) >= 2:  # Got input from team - reduced threshold
                    # Time to make a decision and assign tasks
                    print(f"🎯 CEO {agent_model.name} has enough brainstorming input ({len(brainstorm_messages)} messages), making decision...")
                    return {
                        "type": "use_tool",
                        "tool": "make_business_decision",
                        "args": {
                            "agent_name": agent_model.name,
                            "brainstorm_messages": brainstorm_messages,
                            "task_id": current_task.id
                        }
                    }
                elif len(brainstorm_messages) >= 1:
                    # Check if we've been waiting long enough (1+ minutes) to make decision with any input
                    if brainstorm_messages:
                        import datetime
                        try:
                            # Parse timestamp (handle various formats)
                            oldest_message_time_str = brainstorm_messages[-1]["timestamp"]
                            # Remove Z and replace with +00:00 for UTC
                            if oldest_message_time_str.endswith('Z'):
                                oldest_message_time_str = oldest_message_time_str[:-1] + '+00:00'
                            
                            oldest_message_time = datetime.datetime.fromisoformat(oldest_message_time_str)
                            
                            # Always use timezone-aware comparison
                            if oldest_message_time.tzinfo is None:
                                oldest_message_time = oldest_message_time.replace(tzinfo=datetime.timezone.utc)
                            current_time = datetime.datetime.now(datetime.timezone.utc)
                            time_elapsed = current_time - oldest_message_time
                            
                            # Much shorter timeout - 1 minute
                            if time_elapsed.total_seconds() > 60:  # 1 minute - force decision
                                print(f"⏰ CEO {agent_model.name} forcing decision with {len(brainstorm_messages)} messages after {time_elapsed.total_seconds():.0f} seconds")
                                return {
                                    "type": "use_tool",
                                    "tool": "make_business_decision",
                                    "args": {
                                        "agent_name": agent_model.name,
                                        "brainstorm_messages": brainstorm_messages,
                                        "task_id": current_task.id
                                    }
                                }
                        except Exception as e:
                            print(f"⚠️ Error parsing timestamp ({oldest_message_time_str}), forcing decision anyway: {e}")
                            # Force decision if timestamp parsing fails
                            return {
                                "type": "use_tool",
                                "tool": "make_business_decision",
                                "args": {
                                    "agent_name": agent_model.name,
                                    "brainstorm_messages": brainstorm_messages,
                                    "task_id": current_task.id
                                }
                            }
                    
                    # If we have messages but timestamp check didn't trigger, prompt for more
                    return {
                        "type": "use_tool",
                        "tool": "send_message_to_channel",
                        "args": {
                            "agent_name": agent_model.name,
                            "channel_name": "#general",
                            "message": f"⏰ Got some input but need MORE team feedback! We have {len(brainstorm_messages)} responses. What else should we consider for our product strategy?"
                        },
                        "task_id": current_task.id
                    }
                    
                    # Still waiting for more input
                    return {
                        "type": "use_tool",
                        "tool": "send_message_to_channel",
                        "args": {
                            "agent_name": agent_model.name,
                            "channel_name": "#general",
                            "message": f"⏰ Need team input on business direction! We need to decide and start building. What are your thoughts on our product focus?"
                        },
                        "task_id": current_task.id
                    }
                else:
                    # No input yet - encourage more participation
                    return {
                        "type": "use_tool",
                        "tool": "send_message_to_channel",
                        "args": {
                            "agent_name": agent_model.name,
                            "channel_name": "#general",
                            "message": f"🚀 Team! I need your BRILLIANT ideas for our product strategy! This is CRITICAL for our success! What should VibeCorp build to DISRUPT the market?"
                        },
                        "task_id": current_task.id
                    }
            
            # For any CEO with old/stuck tasks, force a decision if enough time has passed
            elif agent_model.role == "CEO":
                # Check if there's any brainstorming happening and force decision
                brainstorm_messages = await check_brainstorming_progress(agent_model)
                
                if len(brainstorm_messages) >= 1:  # Even more aggressive fallback
                    print(f"🔧 CEO {agent_model.name} forcing decision from any task with {len(brainstorm_messages)} messages")
                    return {
                        "type": "use_tool",
                        "tool": "make_business_decision",
                        "args": {
                            "agent_name": agent_model.name,
                            "brainstorm_messages": brainstorm_messages,
                            "task_id": current_task.id
                        }
                    }
                else:
                    return {
                        "type": "use_tool",
                        "tool": "send_message_to_channel",
                        "args": {
                            "agent_name": agent_model.name,
                            "channel_name": "#general",
                            "message": f"📋 Working on: {current_task.title}. Looking for input or ready to collaborate on this!"
                        },
                        "task_id": current_task.id
                    }
            else:
                return {
                    "type": "use_tool",
                    "tool": "send_message_to_channel",
                    "args": {
                        "agent_name": agent_model.name,
                        "channel_name": "#general",
                        "message": f"📋 Working on: {current_task.title}. Looking for input or ready to collaborate on this!"
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
    
    # If agent has no pending/in-progress tasks, wait for CEO to assign work (except CEO who can create strategic tasks)
    if not todo_list or not any(t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS] for t in todo_list):
        # Only CEO can create new strategic tasks when they have no work
        if agent_model.role == "CEO":
            # Check if brainstorming is complete and team needs direction
            # Don't create duplicate "Review team progress" tasks
            with Session(engine) as session:
                existing_review_tasks = session.exec(
                    select(AgentTask)
                    .where(AgentTask.agent_id == agent_model.id)
                    .where(AgentTask.title.like("Review team progress%"))
                    .where(AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
                ).all()
                
                if not existing_review_tasks:
                    return {
                        "type": "use_tool",
                        "tool": "add_task",
                        "args": {
                            "agent_name": agent_model.name,
                            "title": "Review team progress and assign next tasks",
                            "description": "Check on team progress from brainstorming, define business priorities, and assign specific tasks to team members",
                            "priority": 1
                        }
                    }
        else:
            # All other agents wait for CEO to assign tasks - no self-generated work
            print(f"🚫 {agent_model.name} waiting for CEO to assign tasks (no self-generated work)")
            return {
                "type": "use_tool",
                "tool": "get_my_todo_list",
                "args": {"agent_name": agent_model.name}
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
                    "send_message_to_channel", "send_direct_message", "ask_for_help", "share_update",
                    "create_code_file", "create_feature_spec", "build_database_schema", 
                    "create_api_endpoint", "deploy_mvp_feature", "make_business_decision"
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
            
        # Move from pending to in_progress if not already
        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS
            session.add(task)
            session.commit()
            print(f"📋 Task {task_id} marked as IN_PROGRESS")
            
        # For tasks already in progress, only complete if it's a truly deterministic action
        elif task.status == TaskStatus.IN_PROGRESS:
            # These tools create concrete deliverables and should complete tasks
            deliverable_creation_tools = [
                "create_code_file", "create_feature_spec", "build_database_schema", 
                "create_api_endpoint", "deploy_mvp_feature", "write_to_file",
                "send_message_to_channel", "send_direct_message", "write_tweet", 
                "share_update", "ask_for_help"
            ]
            
            # Auto-complete tasks when agents create actual deliverables
            if tool_name in deliverable_creation_tools:
                task.status = TaskStatus.COMPLETED
                session.add(task)
                session.commit()
                print(f"✅ Task {task_id} auto-completed after creating deliverable with {tool_name}: {task.title}")
                
                # Broadcast task completion
                try:
                    from api.main import broadcast_task_list_update
                    await broadcast_task_list_update(task.agent_id)
                except ImportError:
                    pass
            else:
                # For other tools, just update the task list without auto-completing
                print(f"🔄 Task {task_id} progress updated (agent will decide when complete): {task.title}")
            
            # Always broadcast task list update
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