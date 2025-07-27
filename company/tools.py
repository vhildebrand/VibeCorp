import os
import json
from datetime import datetime
from typing import Optional, List, Dict
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
            
            # Check for duplicate tasks - look for similar titles and descriptions
            existing_tasks = session.exec(
                select(AgentTask)
                .where(AgentTask.agent_id == assignee.id)
                .where(AgentTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]))
            ).all()
            
            # Check for exact title matches or very similar tasks
            for existing_task in existing_tasks:
                # Exact title match
                if existing_task.title.lower().strip() == title.lower().strip():
                    return f"⚠️ Similar task already exists for {assignee_name}: '{existing_task.title}' (ID: {existing_task.id}). Not creating duplicate."
                
                # Check for similar content in title/description (keyword overlap)
                title_words = set(title.lower().split())
                existing_title_words = set(existing_task.title.lower().split())
                
                # If there's significant overlap in keywords (>60% common words)
                if len(title_words) > 2 and len(existing_title_words) > 2:
                    common_words = title_words.intersection(existing_title_words)
                    overlap_ratio = len(common_words) / max(len(title_words), len(existing_title_words))
                    
                    if overlap_ratio > 0.6:
                        return f"⚠️ Very similar task already exists for {assignee_name}: '{existing_task.title}' vs '{title}'. Not creating potential duplicate."
            
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


def make_business_decision(agent_name: str, brainstorm_messages: List[Dict], task_id: int) -> str:
    """
    Allow the CEO to analyze brainstorming input and make business decisions.
    
    Args:
        agent_name (str): The name of the decision-making agent (should be CEO)
        brainstorm_messages (List[Dict]): Recent brainstorming messages from team
        task_id (int): ID of the current review task to complete
        
    Returns:
        str: Decision summary and next steps
    """
    try:
        # Analyze the brainstorming input
        ideas = []
        for msg in brainstorm_messages:
            role = msg.get("role", "Unknown")
            content = msg.get("content", "")
            
            # Extract key ideas from each message
            if "saas" in content.lower() or "platform" in content.lower():
                ideas.append(f"{role}: SaaS/Platform solution")
            elif "productivity" in content.lower() or "workflow" in content.lower():
                ideas.append(f"{role}: Productivity/Workflow tools")
            elif "hr" in content.lower() or "employee" in content.lower():
                ideas.append(f"{role}: HR/Employee engagement")
            elif "collaboration" in content.lower() or "team" in content.lower():
                ideas.append(f"{role}: Team collaboration tools")
            else:
                ideas.append(f"{role}: {content[:50]}...")
        
        # Make the business decision (CEO chooses based on input)
        # Analyze team input to pick the most mentioned/supported idea
        idea_counts = {}
        for msg in brainstorm_messages:
            content = msg.get("content", "").lower()
            if "saas" in content or "platform" in content:
                idea_counts["SaaS Platform"] = idea_counts.get("SaaS Platform", 0) + 1
            if "productivity" in content or "workflow" in content:
                idea_counts["Productivity Tools"] = idea_counts.get("Productivity Tools", 0) + 1
            if "collaboration" in content or "team" in content:
                idea_counts["Team Collaboration"] = idea_counts.get("Team Collaboration", 0) + 1
            if "hr" in content or "employee" in content:
                idea_counts["HR Tech"] = idea_counts.get("HR Tech", 0) + 1
        
        # Pick the most mentioned concept, with fallback
        if idea_counts:
            chosen_concept = max(idea_counts.keys(), key=lambda x: idea_counts[x])
            decision = f"{chosen_concept} for Small Businesses"
            rationale = f"Based on team input, '{chosen_concept}' was the most discussed concept ({idea_counts[chosen_concept]} mentions). We'll build a SaaS solution focused on this area."
        else:
            # Fallback if no clear pattern
            decision = "Team Productivity SaaS Platform"
            rationale = "Based on general team input, we'll build a SaaS platform for small business workflow automation with team collaboration features."
        
        # Create decision summary
        decision_summary = f"""# VibeCorp Business Decision

## Chosen Direction: {decision}

## Rationale: 
{rationale}

## Team Input Considered:
"""
        for idea in ideas:
            decision_summary += f"- {idea}\n"
        
        decision_summary += f"""
## Next Steps:
- Programmer: Set up initial project repository and technical architecture
- Marketer: Draft initial marketing strategy and target audience analysis  
- HR: Plan team structure and hiring needs for development phase
- CEO: Oversee execution and remove blockers

Decision made on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        # Save decision to project folder
        os.makedirs("workspace/project", exist_ok=True)
        with open("workspace/project/business_decision.md", "w") as f:
            f.write(decision_summary)
        
        # Complete the current review task
        with Session(engine) as session:
            agent = session.exec(select(Agent).where(Agent.name == agent_name)).first()
            if agent:
                task = session.exec(
                    select(AgentTask)
                    .where(AgentTask.id == task_id)
                    .where(AgentTask.agent_id == agent.id)
                ).first()
                
                if task:
                    task.status = TaskStatus.COMPLETED
                    session.add(task)
                    session.commit()
        
        # Assign specific tasks to team members
        task_assignments = [
            {
                "assignee": "Penny_The_Programmer",
                "title": "Create user authentication system",
                "description": "Build login/signup functionality with database schema, API endpoints, and security measures. Deliverables: auth.py, user_schema.sql, /api/auth endpoints",
                "priority": 1
            },
            {
                "assignee": "Penny_The_Programmer",
                "title": "Build core product dashboard",
                "description": "Create main application interface with user dashboard, navigation, and core features. Deliverables: dashboard.html, app.js, main.css",
                "priority": 2
            },
            {
                "assignee": "Marty_The_Marketer", 
                "title": "Create landing page and marketing site",
                "description": "Design and build marketing website with clear value proposition, pricing, and conversion funnel. Deliverables: index.html, marketing.css, conversion tracking",
                "priority": 1
            },
            {
                "assignee": "Marty_The_Marketer",
                "title": "Launch initial marketing campaign",
                "description": "Create social media presence, initial content, and user acquisition strategy. Deliverables: social accounts, 10 posts, email campaign",
                "priority": 2
            },
            {
                "assignee": "Hannah_The_HR",
                "title": "Document development processes",
                "description": "Create development workflow, code review process, and team collaboration guidelines. Deliverables: dev_process.md, code_review_checklist.md",
                "priority": 3
            }
        ]
        
        # Create the tasks
        assigned_count = 0
        for assignment in task_assignments:
            # Check if agent already has a similar task to avoid duplicates
            result = assign_task_to_agent(
                assigner_name=agent_name,
                assignee_name=assignment["assignee"],
                title=assignment["title"],
                description=assignment["description"],
                priority=assignment["priority"]
            )
            if "✅" in result:
                assigned_count += 1
            elif "⚠️" in result:
                print(f"Skipped duplicate task: {result}")
                # Don't count as failure, just skip
        
        return f"""✅ Business Decision Made: {decision}

📄 Decision document saved to workspace/project/business_decision.md

🎯 Assigned {assigned_count} specific tasks to team members:
- Programmer: Technical architecture setup
- Marketer: Market analysis and strategy  
- HR: Team planning and hiring

🚀 Moving from brainstorming to execution phase! Team now has clear direction and actionable tasks."""
        
    except Exception as e:
        return f"❌ Error making business decision: {str(e)}"


# ==============================================================================
# Development & Building Tools
# ==============================================================================

def create_code_file(agent_name: str, filename: str, code_content: str, language: str = "python") -> str:
    """
    Create a specific code file with actual implementation.
    
    Args:
        agent_name (str): The agent creating the code
        filename (str): Name of the file to create
        code_content (str): The actual code content
        language (str): Programming language (python, javascript, html, css, etc.)
        
    Returns:
        str: Confirmation with file details
    """
    try:
        # Determine file extension based on language
        extensions = {
            "python": ".py",
            "javascript": ".js", 
            "html": ".html",
            "css": ".css",
            "sql": ".sql",
            "markdown": ".md",
            "json": ".json"
        }
        
        if not filename.endswith(extensions.get(language, "")):
            filename += extensions.get(language, ".txt")
        
        # Save to project folder
        project_path = os.path.join("workspace/project", filename)
        os.makedirs(os.path.dirname(project_path), exist_ok=True)
        
        with open(project_path, 'w') as f:
            f.write(code_content)
        
        # Also save to agent's personal folder for tracking
        agent_path = os.path.join(f"workspace/agents/{agent_name}", filename)
        os.makedirs(os.path.dirname(agent_path), exist_ok=True)
        
        with open(agent_path, 'w') as f:
            f.write(code_content)
        
        return f"✅ Created {language} file: {filename} ({len(code_content)} characters)\n📁 Saved to: {project_path}\n🔧 Language: {language}\n💻 Ready for team review and testing!"
        
    except Exception as e:
        return f"❌ Error creating code file: {str(e)}"


def create_feature_spec(agent_name: str, feature_name: str, description: str, requirements: List[str]) -> str:
    """
    Create a detailed feature specification document.
    
    Args:
        agent_name (str): The agent creating the spec
        feature_name (str): Name of the feature
        description (str): Feature description
        requirements (List[str]): List of specific requirements
        
    Returns:
        str: Confirmation with spec details
    """
    try:
        spec_content = f"""# {feature_name} Feature Specification

## Overview
{description}

## Requirements
"""
        for i, req in enumerate(requirements, 1):
            spec_content += f"{i}. {req}\n"
        
        spec_content += f"""
## Technical Notes
- Created by: {agent_name}
- Created on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- Status: Draft

## Implementation Checklist
- [ ] Database schema design
- [ ] API endpoint implementation  
- [ ] Frontend component creation
- [ ] Testing and validation
- [ ] Documentation updates
"""
        
        filename = f"{feature_name.lower().replace(' ', '_')}_spec.md"
        spec_path = os.path.join("workspace/project/specs", filename)
        os.makedirs(os.path.dirname(spec_path), exist_ok=True)
        
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        
        return f"✅ Created feature spec: {feature_name}\n📋 Requirements: {len(requirements)} items\n📁 Saved to: {spec_path}\n🎯 Ready for development team to implement!"
        
    except Exception as e:
        return f"❌ Error creating feature spec: {str(e)}"


def build_database_schema(agent_name: str, schema_name: str, tables: Dict[str, List[str]]) -> str:
    """
    Create a database schema file with table definitions.
    
    Args:
        agent_name (str): The agent creating the schema
        schema_name (str): Name of the schema/database
        tables (Dict[str, List[str]]): Table names and their columns
        
    Returns:
        str: Confirmation with schema details
    """
    try:
        sql_content = f"-- {schema_name} Database Schema\n"
        sql_content += f"-- Created by: {agent_name}\n"
        sql_content += f"-- Created on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        
        for table_name, columns in tables.items():
            sql_content += f"CREATE TABLE {table_name} (\n"
            for i, column in enumerate(columns):
                sql_content += f"    {column}"
                if i < len(columns) - 1:
                    sql_content += ","
                sql_content += "\n"
            sql_content += ");\n\n"
        
        filename = f"{schema_name.lower()}_schema.sql"
        schema_path = os.path.join("workspace/project/database", filename)
        os.makedirs(os.path.dirname(schema_path), exist_ok=True)
        
        with open(schema_path, 'w') as f:
            f.write(sql_content)
        
        return f"✅ Created database schema: {schema_name}\n🗄️ Tables: {len(tables)} defined\n📁 Saved to: {schema_path}\n💾 Ready for database implementation!"
        
    except Exception as e:
        return f"❌ Error creating database schema: {str(e)}"


def create_api_endpoint(agent_name: str, endpoint_name: str, method: str, description: str, parameters: List[str]) -> str:
    """
    Create a documented API endpoint specification.
    
    Args:
        agent_name (str): The agent creating the endpoint
        endpoint_name (str): API endpoint path (e.g., "/api/users")
        method (str): HTTP method (GET, POST, PUT, DELETE)
        description (str): What the endpoint does
        parameters (List[str]): Required parameters
        
    Returns:
        str: Confirmation with endpoint details
    """
    try:
        api_content = f"""# API Endpoint: {endpoint_name}

**Method:** {method}
**Description:** {description}

## Parameters
"""
        for param in parameters:
            api_content += f"- {param}\n"
        
        api_content += f"""
## Implementation Notes
- Created by: {agent_name}
- Created on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- Status: Specification complete, ready for implementation

## Example Code Template
```python
@app.{method.lower()}('{endpoint_name}')
async def {endpoint_name.replace('/', '_').replace('-', '_')}():
    # TODO: Implement {description}
    pass
```
"""
        
        filename = f"{endpoint_name.replace('/', '_').replace('-', '_')}_api.md"
        api_path = os.path.join("workspace/project/api_docs", filename)
        os.makedirs(os.path.dirname(api_path), exist_ok=True)
        
        with open(api_path, 'w') as f:
            f.write(api_content)
        
        return f"✅ Created API endpoint spec: {method} {endpoint_name}\n📝 Parameters: {len(parameters)} defined\n📁 Saved to: {api_path}\n🚀 Ready for backend implementation!"
        
    except Exception as e:
        return f"❌ Error creating API endpoint: {str(e)}"


def deploy_mvp_feature(agent_name: str, feature_name: str, files_created: List[str]) -> str:
    """
    Mark a feature as deployed to MVP and track deliverables.
    
    Args:
        agent_name (str): The agent deploying the feature
        feature_name (str): Name of the feature being deployed
        files_created (List[str]): List of files that make up this feature
        
    Returns:
        str: Deployment confirmation
    """
    try:
        deployment_info = {
            "feature_name": feature_name,
            "deployed_by": agent_name,
            "deployment_time": datetime.utcnow().isoformat(),
            "files_included": files_created,
            "status": "deployed_to_mvp",
            "version": "0.1.0"
        }
        
        # Create deployment record
        deployments_file = "workspace/project/deployments.json"
        os.makedirs("workspace/project", exist_ok=True)
        
        if os.path.exists(deployments_file):
            with open(deployments_file, 'r') as f:
                deployments = json.load(f)
        else:
            deployments = {"mvp_features": []}
        
        deployments["mvp_features"].append(deployment_info)
        
        with open(deployments_file, 'w') as f:
            json.dump(deployments, f, indent=2)
        
        return f"🚀 DEPLOYED: {feature_name} to MVP!\n📦 Files: {len(files_created)} included\n⏰ Deployed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}\n🎯 Feature now live and ready for user testing!"
        
    except Exception as e:
        return f"❌ Error deploying feature: {str(e)}"


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
    
    # Development & Building Tools
    "create_code_file": create_code_file,
    "create_feature_spec": create_feature_spec,
    "build_database_schema": build_database_schema,
    "create_api_endpoint": create_api_endpoint,
    "deploy_mvp_feature": deploy_mvp_feature,
    
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
    "make_business_decision": make_business_decision,
    
    # Status Tools
    "set_agent_status": set_agent_status
}
