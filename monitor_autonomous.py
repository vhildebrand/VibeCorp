#!/usr/bin/env python3
"""
Monitor autonomous agent activities in real-time
Shows tasks being created, messages being posted, and status changes
"""

import asyncio
import websockets
import json
import requests
from datetime import datetime

API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

def print_timestamp():
    return datetime.now().strftime("%H:%M:%S")

def show_current_status():
    """Show current system status"""
    try:
        # Get agents
        agents_response = requests.get(f"{API_BASE}/agents")
        agents = agents_response.json()
        
        # Get recent tasks
        tasks_response = requests.get(f"{API_BASE}/tasks")
        tasks = tasks_response.json()
        recent_tasks = [t for t in tasks if t['status'] in ['pending', 'in_progress']][:3]
        
        print("\n" + "="*60)
        print(f"🤖 AUTONOMOUS AGENT MONITOR - {print_timestamp()}")
        print("="*60)
        
        print("\n📊 AGENT STATUS:")
        for agent in agents:
            status_emoji = {
                'idle': '😴',
                'coding': '💻', 
                'in_meeting': '🤝',
                'tweeting': '📱',
                'researching': '🔍',
                'debugging': '🐛'
            }.get(agent['status'], '⚡')
            
            print(f"  {status_emoji} {agent['name'].replace('_', ' ')}: {agent['status'].replace('_', ' ')}")
        
        print(f"\n🎯 ACTIVE TASKS ({len(recent_tasks)}):")
        for task in recent_tasks:
            print(f"  • [{task['status'].upper()}] {task['title']}")
        
        print(f"\n🌐 WebSocket URL: {WS_URL}")
        print("Listening for real-time updates...\n")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")

async def monitor_websocket():
    """Monitor WebSocket for real-time updates"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            print(f"✅ [{print_timestamp()}] Connected to WebSocket")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    timestamp = print_timestamp()
                    
                    if data.get('type') == 'connection_established':
                        print(f"🔗 [{timestamp}] {data.get('message', 'Connected')}")
                        
                    elif data.get('type') == 'new_message':
                        msg_data = data.get('data', {})
                        agent_name = msg_data.get('agentName', 'Unknown').replace('_', ' ')
                        content = msg_data.get('content', '')[:80] + ('...' if len(msg_data.get('content', '')) > 80 else '')
                        print(f"💬 [{timestamp}] {agent_name}: {content}")
                        
                    elif data.get('type') == 'agent_status_update':
                        status_data = data.get('data', {})
                        agent_id = status_data.get('agentId')
                        status = status_data.get('status', '').replace('_', ' ')
                        print(f"📊 [{timestamp}] Agent {agent_id} status: {status}")
                        
                    elif data.get('type') == 'task_update':
                        task_data = data.get('data', {})
                        title = task_data.get('title', 'Unknown task')
                        status = task_data.get('status', '').upper()
                        print(f"🎯 [{timestamp}] Task [{status}]: {title}")
                        
                    else:
                        print(f"📡 [{timestamp}] {data.get('type', 'Unknown')}: {data}")
                        
                except json.JSONDecodeError:
                    print(f"⚠️  [{timestamp}] Invalid JSON received: {message}")
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

async def main():
    """Main monitoring function"""
    print("🚀 Starting AutoGen Autonomous Agent Monitor...")
    
    # Show initial status
    show_current_status()
    
    # Monitor WebSocket for updates
    while True:
        try:
            await monitor_websocket()
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 [{print_timestamp()}] Monitor stopped by user")
    except Exception as e:
        print(f"\n💥 [{print_timestamp()}] Fatal error: {e}") 