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

def write_to_file(agent_name: str, path: str, content: str, location: str = "personal") -> str:
    """
    Write content to a file in the organized workspace structure.
    
    Args:
        agent_name (str): The name of the agent writing the file
        path (str): The file path (relative to the chosen location)
        content (str): The content to write
        location (str): Where to write - "personal", "project", or "shared"
        
    Returns:
        str: Confirmation message
    """
    try:
        # Determine the base directory based on location
        if location == "project":
            base_dir = "workspace/project"
        elif location == "shared":
            base_dir = "workspace/shared"
        elif location == "personal":
            base_dir = f"workspace/agents/{agent_name}"
        else:
            return f"❌ Invalid location '{location}'. Use 'personal', 'project', or 'shared'"
        
        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(base_dir, path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size for confirmation
        file_size = os.path.getsize(file_path)
        
        location_desc = {
            "personal": f"{agent_name}'s personal folder",
            "project": "project folder (shared with team)",
            "shared": "shared team folder"
        }
        
        return f"✅ Successfully wrote to {file_path} ({file_size} bytes) in {location_desc[location]}"
        
    except Exception as e:
        return f"❌ Error writing to file: {str(e)}"


def read_file(agent_name: str, path: str, location: str = "personal") -> str:
    """
    Read content from a file in the organized workspace structure.
    
    Args:
        agent_name (str): The name of the agent reading the file
        path (str): The file path (relative to the chosen location)
        location (str): Where to read from - "personal", "project", or "shared"
        
    Returns:
        str: File content or error message
    """
    try:
        # Determine the base directory based on location
        if location == "project":
            base_dir = "workspace/project"
        elif location == "shared":
            base_dir = "workspace/shared"
        elif location == "personal":
            base_dir = f"workspace/agents/{agent_name}"
        else:
            return f"❌ Invalid location '{location}'. Use 'personal', 'project', or 'shared'"
        
        # Create full file path
        file_path = os.path.join(base_dir, path)
        
        if not os.path.exists(file_path):
            return f"❌ File not found: {file_path}"
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = os.path.getsize(file_path)
        
        location_desc = {
            "personal": f"{agent_name}'s personal folder",
            "project": "project folder",
            "shared": "shared team folder"
        }
        
        return f"📄 Content of {path} from {location_desc[location]} ({file_size} bytes):\n\n{content}"
        
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


def list_files(agent_name: str, path: str = ".", location: str = "personal") -> str:
    """
    List files in a directory within the organized workspace structure.
    
    Args:
        agent_name (str): The name of the agent listing files
        path (str): Directory path (relative to the chosen location)
        location (str): Where to list from - "personal", "project", or "shared"
        
    Returns:
        str: List of files and directories
    """
    try:
        # Determine the base directory based on location
        if location == "project":
            base_dir = "workspace/project"
        elif location == "shared":
            base_dir = "workspace/shared"
        elif location == "personal":
            base_dir = f"workspace/agents/{agent_name}"
        else:
            return f"❌ Invalid location '{location}'. Use 'personal', 'project', or 'shared'"
        
        # Create full directory path
        dir_path = os.path.join(base_dir, path)
        
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
        
        location_desc = {
            "personal": f"{agent_name}'s personal folder",
            "project": "project folder",
            "shared": "shared team folder"
        }
        
        if not items:
            return f"📂 {location_desc[location]} at {path} is empty"
        
        return f"📂 Contents of {location_desc[location]} at {path}:\n" + "\n".join(sorted(items))
        
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"


# ==============================================================================
# Existing Tools (keeping the ones that work well)
# ==============================================================================

def write_tweet(agent_name: str, message: str) -> str:
    """
    Write a tweet to the agent's personal file for later posting.
    
    Args:
        agent_name (str): The name of the agent writing the tweet
        message (str): The message to tweet
        
    Returns:
        str: Confirmation message about the tweet file
    """
    try:
        # Validate message length (Twitter limit is 280 characters)
        if len(message) > 280:
            return f"❌ Tweet too long! Twitter limit is 280 characters. Your message is {len(message)} characters."
        
        # Create agent's personal folder
        agent_dir = f"workspace/agents/{agent_name}"
        os.makedirs(agent_dir, exist_ok=True)
        
        # Create tweet data
        tweet_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "author": agent_name,
            "message": message,
            "character_count": len(message),
            "hashtags": message.count('#'),
            "mentions": message.count('@'),
            "status": "draft"
        }
        
        # Load existing tweets or create new list
        tweets_file = os.path.join(agent_dir, "tweets.json")
        if os.path.exists(tweets_file):
            with open(tweets_file, 'r') as f:
                tweets = json.load(f)
        else:
            tweets = []
        
        # Add new tweet to the beginning (most recent first)
        tweets.insert(0, tweet_data)
        
        # Save to agent's personal tweet file
        with open(tweets_file, 'w') as f:
            json.dump(tweets, f, indent=2)
        
        return f"📝 Tweet draft saved to {agent_name}'s personal folder!\n🐦 Message: '{message}'\n📊 Characters: {len(message)}/280\n📁 Saved to {tweets_file}"
        
    except Exception as e:
        return f"❌ Error saving tweet: {str(e)}"


def web_search(agent_name: str, query: str, max_results: int = 5) -> str:
    """
    Perform a real web search using DuckDuckGo and save to agent's folder.
    
    Args:
        agent_name (str): The name of the agent performing the search
        query (str): The search query
        max_results (int): Maximum number of results to return
        
    Returns:
        str: Search results summary
    """
    try:
        import requests
        from urllib.parse import quote_plus
        import re
        
        # Simplify query for better results - take key terms only
        query_words = query.split()
        if len(query_words) > 5:
            # Take first 3-4 most important words, skip common words
            important_words = [w for w in query_words[:6] if w.lower() not in ['best', 'practices', 'how', 'to', 'the', 'and', 'or', 'for', 'with']]
            simplified_query = ' '.join(important_words[:4])
        else:
            simplified_query = query
        
        print(f"🔍 {agent_name} searching for: '{simplified_query}' (simplified from: '{query}')")
        
        # Use DuckDuckGo Instant Answer API (free, no API key required)
        search_url = f"https://api.duckduckgo.com/?q={quote_plus(simplified_query)}&format=json&no_html=1&skip_disambig=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract results
        results = []
        
        # Add abstract (main result) if available
        if data.get('Abstract'):
            results.append({
                "title": data.get('Heading', query),
                "url": data.get('AbstractURL', ''),
                "snippet": data.get('Abstract', '')
            })
        
        # Add related topics
        for topic in data.get('RelatedTopics', [])[:max_results-1]:
            if isinstance(topic, dict) and 'Text' in topic:
                # Extract URL from FirstURL
                url = topic.get('FirstURL', '')
                title = topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', '')
                snippet = topic.get('Text', '')
                
                results.append({
                    "title": title[:100],
                    "url": url,
                    "snippet": snippet[:200]
                })
        
        # If no results from DuckDuckGo API, try HTML scraping (backup)
        if not results:
            try:
                html_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                html_response = requests.get(html_url, headers=headers, timeout=10)
                html_content = html_response.text
                
                # Simple regex to extract basic results (backup method)
                title_pattern = r'<a.*?class="result__a".*?>(.*?)</a>'
                snippet_pattern = r'<a.*?class="result__snippet".*?>(.*?)</a>'
                
                titles = re.findall(title_pattern, html_content, re.DOTALL)[:max_results]
                snippets = re.findall(snippet_pattern, html_content, re.DOTALL)[:max_results]
                
                for i, title in enumerate(titles):
                    snippet = snippets[i] if i < len(snippets) else "No description available"
                    # Clean HTML tags
                    title = re.sub(r'<.*?>', '', title).strip()
                    snippet = re.sub(r'<.*?>', '', snippet).strip()
                    
                    results.append({
                        "title": title[:100],
                        "url": f"https://duckduckgo.com/?q={quote_plus(query)}",
                        "snippet": snippet[:200]
                    })
            except:
                pass  # Fallback failed, use what we have
        
        # Create search results structure
        search_results = {
            "query": query,
            "simplified_query": simplified_query,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "DuckDuckGo API" if results else "No results found",
            "results": results[:max_results] if results else [
                {
                    "title": f"No specific results found for '{simplified_query}'",
                    "url": f"https://duckduckgo.com/?q={quote_plus(simplified_query)}",
                    "snippet": f"Search performed but no structured results returned. Try searching manually for more detailed information about '{simplified_query}'."
                }
            ]
        }
        
        # Save search results to agent's personal folder
        agent_dir = f"workspace/agents/{agent_name}"
        os.makedirs(agent_dir, exist_ok=True)
        search_file = os.path.join(agent_dir, f"search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(search_file, 'w') as f:
            json.dump(search_results, f, indent=2)
        
        # Format results for return
        results_summary = f"🔍 Real Web Search Results for '{query}':\n\n"
        for i, result in enumerate(search_results["results"], 1):
            title = result['title'] or f"Result {i}"
            snippet = result['snippet'] or "No description available"
            url = result['url'] or "URL not available"
            
            results_summary += f"{i}. {title}\n"
            results_summary += f"   📝 {snippet}\n"
            if url and url != "URL not available":
                results_summary += f"   🔗 {url}\n"
            results_summary += "\n"
        
        results_summary += f"📁 Detailed results saved to: {search_file}"
        
        return results_summary
        
    except Exception as e:
        # Save error info to agent's folder for debugging
        agent_dir = f"workspace/agents/{agent_name}"
        os.makedirs(agent_dir, exist_ok=True)
        
        error_info = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "status": "search_failed"
        }
        
        error_file = os.path.join(agent_dir, f"search_error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        with open(error_file, 'w') as f:
            json.dump(error_info, f, indent=2)
        
        # Return honest failure message
        fallback_result = f"❌ Web search failed for '{query}': {str(e)}\n\n"
        fallback_result += f"💡 This was a real search attempt that failed. Try simplifying the search terms.\n"
        fallback_result += f"📁 Error details saved to: {error_file}"
        
        return fallback_result


def share_file_with_agent(sender_name: str, recipient_name: str, file_path: str, message: str = "") -> str:
    """
    Share a file from one agent's personal folder to another agent's folder.
    
    Args:
        sender_name (str): The agent sharing the file
        recipient_name (str): The agent receiving the file
        file_path (str): Path to the file in sender's personal folder
        message (str): Optional message to include with the shared file
        
    Returns:
        str: Confirmation message
    """
    try:
        import shutil
        
        # Source file path
        source_path = os.path.join(f"workspace/agents/{sender_name}", file_path)
        
        if not os.path.exists(source_path):
            return f"❌ File not found in {sender_name}'s folder: {file_path}"
        
        # Create recipient's folder if it doesn't exist
        recipient_dir = f"workspace/agents/{recipient_name}"
        os.makedirs(recipient_dir, exist_ok=True)
        
        # Create shared_files subdirectory
        shared_dir = os.path.join(recipient_dir, "shared_files")
        os.makedirs(shared_dir, exist_ok=True)
        
        # Destination file path with sender prefix
        filename = os.path.basename(file_path)
        dest_filename = f"from_{sender_name}_{filename}"
        dest_path = os.path.join(shared_dir, dest_filename)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        # Create a sharing note
        note_content = f"File shared by {sender_name} on {datetime.utcnow().isoformat()}\n"
        note_content += f"Original file: {file_path}\n"
        if message:
            note_content += f"Message: {message}\n"
        
        note_path = os.path.join(shared_dir, f"from_{sender_name}_{filename}.note")
        with open(note_path, 'w') as f:
            f.write(note_content)
        
        return f"✅ File shared successfully!\n📁 {file_path} copied to {recipient_name}'s shared_files folder\n📝 Note: {message if message else 'No message'}"
        
    except Exception as e:
        return f"❌ Error sharing file: {str(e)}"


def copy_to_project(agent_name: str, file_path: str, project_path: str = None) -> str:
    """
    Copy a file from agent's personal folder to the project folder.
    
    Args:
        agent_name (str): The agent copying the file
        file_path (str): Path to the file in agent's personal folder
        project_path (str): Optional path in project folder (defaults to same as file_path)
        
    Returns:
        str: Confirmation message
    """
    try:
        import shutil
        
        # Source file path
        source_path = os.path.join(f"workspace/agents/{agent_name}", file_path)
        
        if not os.path.exists(source_path):
            return f"❌ File not found in {agent_name}'s folder: {file_path}"
        
        # Destination path
        if project_path is None:
            project_path = file_path
        
        dest_path = os.path.join("workspace/project", project_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        return f"✅ File copied to project folder!\n📁 {file_path} → project/{project_path}\n🚀 Now available to the entire team"
        
    except Exception as e:
        return f"❌ Error copying to project: {str(e)}"


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
    
    # Organized Filesystem Tools
    "write_to_file": write_to_file,
    "read_file": read_file,
    "list_files": list_files,
    "share_file_with_agent": share_file_with_agent,
    "copy_to_project": copy_to_project,
    
    # Communication & Research Tools
    "write_tweet": write_tweet,
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
