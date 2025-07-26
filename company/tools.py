import os
import json
from datetime import datetime
from typing import Optional
from agents.status_tool import set_agent_status

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


def write_code_to_file(filename: str, code: str) -> str:
    """
    Write code to a file in the workspace directory.
    
    Args:
        filename (str): The name of the file to create/write
        code (str): The code content to write to the file
        
    Returns:
        str: Confirmation message about the file creation
    """
    try:
        # Ensure workspace directory exists
        workspace_dir = "workspace"
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(workspace_dir, filename)
        
        # Write code to file
        with open(file_path, 'w') as f:
            f.write(code)
        
        # Get file size for confirmation
        file_size = os.path.getsize(file_path)
        
        return f"✅ Successfully wrote code to {file_path} ({file_size} bytes)"
        
    except Exception as e:
        return f"❌ Error writing code to file: {str(e)}"


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


# Dictionary of all available tools for easy registration
AVAILABLE_TOOLS = {
    "post_to_twitter": post_to_twitter,
    "write_code_to_file": write_code_to_file,
    "web_search": web_search,
    "manage_budget": manage_budget,
    "set_agent_status": set_agent_status
}
