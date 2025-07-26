import os
import json
from datetime import datetime
from typing import Optional, List
from sqlmodel import Session, select
from agents.status_tool import set_agent_status
from agents.communication_tools import send_message_to_channel, send_direct_message, ask_for_help, share_update
from database.init_db import engine
from database.models import AgentTask, TaskStatus, Agent


# ==============================================================================
# Task Management Tools
# ==============================================================================

def add_task(agent_name: str, title: str, description: str, priority: int = 10) -> str:
    """
    Add a new task to an agent's to-do list.
    
    Args:
        agent_name (str): The name of the agent adding the task
        title (str): Short title for the task
        description (str): Detailed description of the task
        priority (int): Priority level (1-20, lower numbers = higher priority)
        
    Returns:
        str: Confirmation message
    """
    try:
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent '{agent_name}' not found"
            
            # Create new task
            task = AgentTask(
                agent_id=agent.id,
                title=title,
                description=description,
                priority=priority,
                status=TaskStatus.PENDING
            )
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            return f"✅ Task added to {agent_name}'s to-do list: '{title}' (Priority: {priority}, ID: {task.id})"
            
    except Exception as e:
        return f"❌ Error adding task: {str(e)}"


def complete_task(agent_name: str, task_id: int) -> str:
    """
    Mark a task as completed.
    
    Args:
        agent_name (str): The name of the agent completing the task
        task_id (int): ID of the task to complete
        
    Returns:
        str: Confirmation message
    """
    try:
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent '{agent_name}' not found"
            
            # Find the task
            task = session.exec(
                select(AgentTask)
                .where(AgentTask.id == task_id)
                .where(AgentTask.agent_id == agent.id)
            ).first()
            
            if not task:
                return f"❌ Task {task_id} not found for {agent_name}"
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            session.add(task)
            session.commit()
            
            return f"✅ Task completed: '{task.title}' (ID: {task_id})"
            
    except Exception as e:
        return f"❌ Error completing task: {str(e)}"


def get_my_todo_list(agent_name: str) -> str:
    """
    Get the current to-do list for an agent.
    
    Args:
        agent_name (str): The name of the agent
        
    Returns:
        str: Formatted to-do list
    """
    try:
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent '{agent_name}' not found"
            
            # Get all pending and in-progress tasks, ordered by priority
            tasks = session.exec(
                select(AgentTask)
                .where(AgentTask.agent_id == agent.id)
                .where(AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
                .order_by(AgentTask.priority)
            ).all()
            
            if not tasks:
                return f"📋 {agent_name}'s to-do list is empty! 🎉"
            
            todo_list = f"📋 {agent_name}'s To-Do List ({len(tasks)} tasks):\n\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = "⏳" if task.status == TaskStatus.IN_PROGRESS else "📌"
                todo_list += f"{i}. {status_emoji} [{task.priority}] {task.title} (ID: {task.id})\n"
                todo_list += f"   📝 {task.description}\n\n"
            
            return todo_list
            
    except Exception as e:
        return f"❌ Error getting to-do list: {str(e)}"


def update_task_status(agent_name: str, task_id: int, status: str) -> str:
    """
    Update the status of a task.
    
    Args:
        agent_name (str): The name of the agent
        task_id (int): ID of the task to update
        status (str): New status ('pending', 'in_progress', 'completed', 'blocked')
        
    Returns:
        str: Confirmation message
    """
    try:
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if status.lower() not in valid_statuses:
            return f"❌ Invalid status. Valid options: {', '.join(valid_statuses)}"
        
        with Session(engine) as session:
            # Find the agent
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if not agent:
                return f"❌ Agent '{agent_name}' not found"
            
            # Find the task
            task = session.exec(
                select(AgentTask)
                .where(AgentTask.id == task_id)
                .where(AgentTask.agent_id == agent.id)
            ).first()
            
            if not task:
                return f"❌ Task {task_id} not found for {agent_name}"
            
            # Update status
            task.status = TaskStatus(status.upper())
            session.add(task)
            session.commit()
            
            return f"✅ Task '{task.title}' status updated to: {status}"
            
    except Exception as e:
        return f"❌ Error updating task status: {str(e)}"


def assign_task_to_agent(assigner_name: str, assignee_name: str, title: str, description: str, priority: int = 10) -> str:
    """
    Assign a task to another agent.
    
    Args:
        assigner_name (str): The agent assigning the task
        assignee_name (str): The agent receiving the task
        title (str): Task title
        description (str): Task description
        priority (int): Task priority
        
    Returns:
        str: Confirmation message
    """
    try:
        with Session(engine) as session:
            # Find both agents
            assigner = session.exec(select(Agent).where(Agent.name == assigner_name)).first()
            assignee = session.exec(select(Agent).where(Agent.name == assignee_name)).first()
            
            if not assigner:
                return f"❌ Assigner '{assigner_name}' not found"
            if not assignee:
                return f"❌ Assignee '{assignee_name}' not found"
            
            # Create task for the assignee
            task = AgentTask(
                agent_id=assignee.id,
                title=title,
                description=f"[Assigned by {assigner_name}] {description}",
                priority=priority,
                status=TaskStatus.PENDING
            )
            
            session.add(task)
            session.commit()
            session.refresh(task)
            
            return f"✅ Task assigned to {assignee_name}: '{title}' (ID: {task.id})"
            
    except Exception as e:
        return f"❌ Error assigning task: {str(e)}"


# ==============================================================================
# Enhanced Filesystem Tools
# ==============================================================================

def write_to_file(path: str, content: str) -> str:
    """
    Write content to a file in the workspace directory.
    
    Args:
        path (str): The file path (relative to workspace)
        content (str): The content to write
        
    Returns:
        str: Confirmation message
    """
    try:
        # Ensure workspace directory exists
        workspace_dir = "workspace"
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(workspace_dir, path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size for confirmation
        file_size = os.path.getsize(file_path)
        
        return f"✅ Successfully wrote to {file_path} ({file_size} bytes)"
        
    except Exception as e:
        return f"❌ Error writing to file: {str(e)}"


def read_file(path: str) -> str:
    """
    Read content from a file in the workspace directory.
    
    Args:
        path (str): The file path (relative to workspace)
        
    Returns:
        str: File content or error message
    """
    try:
        # Create full file path
        file_path = os.path.join("workspace", path)
        
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = os.path.getsize(file_path)
        
        return f"📄 Content of {path} ({file_size} bytes):\n\n{content}"
        
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


def list_files(path: str = ".") -> str:
    """
    List files in a directory within the workspace.
    
    Args:
        path (str): Directory path (relative to workspace)
        
    Returns:
        str: List of files and directories
    """
    try:
        # Create full directory path
        dir_path = os.path.join("workspace", path)
        
        if not os.path.exists(dir_path):
            return f"❌ Directory not found: {dir_path}"
        
        items = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                items.append(f"📄 {item} ({size} bytes)")
        
        if not items:
            return f"📂 Directory {path} is empty"
        
        return f"📂 Contents of {path}:\n" + "\n".join(sorted(items))
        
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"


# ==============================================================================
# Existing Tools (keeping the ones that work well)
# ==============================================================================

def post_to_twitter(message: str) -> str:
    """
    Post a message to Twitter (simulated for now).
    
    Args:
        message (str): The message to post to Twitter
        
    Returns:
        str: Confirmation message about the Twitter post
    """
    # For now, we'll simulate posting to Twitter by saving to a file
    # In a real implementation, this would use the Twitter API
    
    try:
        # Create a simulated tweet
        tweet_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "engagement": {
                "likes": 0,
                "retweets": 0,
                "replies": 0
            },
            "status": "posted"
        }
        
        # Save to a simulated Twitter feed file
        tweets_file = "workspace/twitter_feed.json"
        
        # Load existing tweets or create new list
        if os.path.exists(tweets_file):
            with open(tweets_file, 'r') as f:
                tweets = json.load(f)
        else:
            tweets = []
        
        # Add new tweet
        tweets.append(tweet_data)
        
        # Save back to file
        os.makedirs("workspace", exist_ok=True)
        with open(tweets_file, 'w') as f:
            json.dump(tweets, f, indent=2)
        
        return f"✅ Successfully posted to Twitter: '{message[:50]}...' | Tweet saved to {tweets_file}"
        
    except Exception as e:
        return f"❌ Error posting to Twitter: {str(e)}"


def web_search(query: str, max_results: int = 5) -> str:
    """
    Perform a web search (simulated for now).
    
    Args:
        query (str): The search query
        max_results (int): Maximum number of results to return
        
    Returns:
        str: Search results summary
    """
    # For now, simulate web search results
    # In a real implementation, this would use a web search API like Google, Bing, or DuckDuckGo
    
    try:
        search_results = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "results": [
                {
                    "title": f"Result 1 for '{query}'",
                    "url": f"https://example.com/search-result-1",
                    "snippet": f"This is a simulated search result about {query}. It contains relevant information that would help with research."
                },
                {
                    "title": f"Advanced Guide to {query}",
                    "url": f"https://example.com/advanced-guide",
                    "snippet": f"Comprehensive guide covering all aspects of {query} with practical examples and best practices."
                },
                {
                    "title": f"{query} - Latest News and Updates",
                    "url": f"https://news-example.com/latest-news",
                    "snippet": f"Stay up to date with the latest developments and trends in {query} from industry experts."
                }
            ][:max_results]
        }
        
        # Save search results to file
        search_file = f"workspace/search_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("workspace", exist_ok=True)
        
        with open(search_file, 'w') as f:
            json.dump(search_results, f, indent=2)
        
        # Format results for return
        results_summary = f"🔍 Search Results for '{query}':\n"
        for i, result in enumerate(search_results["results"], 1):
            results_summary += f"{i}. {result['title']}\n   {result['snippet']}\n   URL: {result['url']}\n\n"
        
        results_summary += f"📁 Detailed results saved to: {search_file}"
        
        return results_summary
        
    except Exception as e:
        return f"❌ Error performing web search: {str(e)}"


def manage_budget(action: str, amount: Optional[float] = None, description: Optional[str] = None) -> str:
    """
    Manage the company budget (simulated).
    
    Args:
        action (str): Action to perform ('view', 'spend', 'add_revenue')
        amount (float, optional): Amount for spend/revenue actions
        description (str, optional): Description of the transaction
        
    Returns:
        str: Budget status or transaction confirmation
    """
    try:
        budget_file = "workspace/company_budget.json"
        
        # Load existing budget or create default
        if os.path.exists(budget_file):
            with open(budget_file, 'r') as f:
                budget_data = json.load(f)
        else:
            budget_data = {
                "current_balance": 100000.0,  # Starting budget of $100k
                "transactions": [],
                "monthly_burn_rate": 15000.0
            }
        
        if action == "view":
            return f"💰 Current Company Budget: ${budget_data['current_balance']:,.2f}\n📊 Monthly Burn Rate: ${budget_data['monthly_burn_rate']:,.2f}\n📈 Total Transactions: {len(budget_data['transactions'])}"
        
        elif action == "spend" and amount is not None:
            if amount > budget_data['current_balance']:
                return f"❌ Insufficient funds! Available: ${budget_data['current_balance']:,.2f}, Requested: ${amount:,.2f}"
            
            # Record transaction
            transaction = {
                "type": "expense",
                "amount": -amount,
                "description": description or "Unspecified expense",
                "timestamp": datetime.utcnow().isoformat(),
                "balance_after": budget_data['current_balance'] - amount
            }
            
            budget_data['current_balance'] -= amount
            budget_data['transactions'].append(transaction)
            
            # Save updated budget
            os.makedirs("workspace", exist_ok=True)
            with open(budget_file, 'w') as f:
                json.dump(budget_data, f, indent=2)
            
            return f"💸 Expense recorded: ${amount:,.2f} for '{description}'\n💰 New balance: ${budget_data['current_balance']:,.2f}"
        
        elif action == "add_revenue" and amount is not None:
            # Record revenue
            transaction = {
                "type": "revenue",
                "amount": amount,
                "description": description or "Unspecified revenue",
                "timestamp": datetime.utcnow().isoformat(),
                "balance_after": budget_data['current_balance'] + amount
            }
            
            budget_data['current_balance'] += amount
            budget_data['transactions'].append(transaction)
            
            # Save updated budget
            os.makedirs("workspace", exist_ok=True)
            with open(budget_file, 'w') as f:
                json.dump(budget_data, f, indent=2)
            
            return f"💰 Revenue added: ${amount:,.2f} for '{description}'\n💰 New balance: ${budget_data['current_balance']:,.2f}"
        
        else:
            return f"❌ Invalid action '{action}' or missing required parameters"
            
    except Exception as e:
        return f"❌ Error managing budget: {str(e)}"


# ==============================================================================
# Tool Registry
# ==============================================================================

# Dictionary of all available tools for easy registration
AVAILABLE_TOOLS = {
    # Task Management Tools
    "add_task": add_task,
    "complete_task": complete_task,
    "get_my_todo_list": get_my_todo_list,
    "update_task_status": update_task_status,
    "assign_task_to_agent": assign_task_to_agent,
    
    # Filesystem Tools
    "write_to_file": write_to_file,
    "read_file": read_file,
    "list_files": list_files,
    
    # Communication & Research Tools
    "post_to_twitter": post_to_twitter,
    "web_search": web_search,
    "send_message_to_channel": send_message_to_channel,
    "send_direct_message": send_direct_message,
    "ask_for_help": ask_for_help,
    "share_update": share_update,
    
    # Business Tools
    "manage_budget": manage_budget,
    
    # Status Tools
    "set_agent_status": set_agent_status
}
