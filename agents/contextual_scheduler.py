"""
Contextual Autonomous Scheduler
Enhanced version that uses agent memory and conversation context for natural interactions
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlmodel import Session, select
from database.init_db import engine
from database.models import Agent, Conversation, Task, TaskStatus, AgentMemoryType, ConversationMember
from agents.agent_context import agent_context_manager
import os
from dotenv import load_dotenv

load_dotenv()


class ContextualAutonomousScheduler:
    """Enhanced autonomous scheduler with contextual awareness"""
    
    def __init__(self):
        self.is_running = False
        self.base_interval = 30  # 30 seconds base interval for frequent communication
        self.context_manager = agent_context_manager
        
        # More sophisticated conversation topics that can build on context
        self.conversation_topics = [
            {
                "title": "Product Roadmap Review",
                "description": "Let's review our product roadmap and prioritize features for the next quarter. What should we focus on to maximize user engagement?",
                "conversation_type": "brainstorming",
                "context_sensitive": True
            },
            {
                "title": "User Experience Improvements", 
                "description": "We need to discuss the latest user feedback and identify key UX improvements. How can we make our product more intuitive?",
                "conversation_type": "problem_solving",
                "context_sensitive": True
            },
            {
                "title": "Technical Architecture Decision",
                "description": "It's time to evaluate our current tech stack and consider if we need to refactor any components for better scalability.",
                "conversation_type": "technical",
                "context_sensitive": True
            },
            {
                "title": "Team Performance Analysis",
                "description": "Let's analyze our recent sprint performance and identify areas for improvement in our development process.",
                "conversation_type": "operations",
                "context_sensitive": True
            }
        ]

    async def start(self):
        """Start the contextual autonomous scheduler"""
        if self.is_running:
            print("Contextual autonomous scheduler is already running")
            return
            
        self.is_running = True
        print("🧠 Starting Contextual Autonomous Agent Scheduler...")
        print("🎯 Agents will now generate contextual, memory-aware conversations!")
        print("💭 Using 20 messages of conversation history for context")
        
        # Initialize agent work sessions
        await self._initialize_agent_work_sessions()
        
        # Start multiple concurrent tasks
        await asyncio.gather(
            self.contextual_task_generation_loop(),
            self.contextual_conversation_loop(),
            self.agent_memory_update_loop(), 
            self.work_session_update_loop()
        )

    async def _initialize_agent_work_sessions(self):
        """Initialize work sessions for all agents"""
        work_sessions = {
            "CeeCee_The_CEO": {
                "title": "Q3 Strategic Planning",
                "description": "Reviewing market opportunities and planning our next growth phase",
                "progress": "Analyzing competitor strategies and market trends"
            },
            "Marty_The_Marketer": {
                "title": "Viral Campaign Development", 
                "description": "Creating a social media campaign to increase brand awareness",
                "progress": "Researching TikTok trends and influencer partnerships"
            },
            "Penny_The_Programmer": {
                "title": "API Performance Optimization",
                "description": "Improving system performance and reducing response times",
                "progress": "Profiling database queries and optimizing slow endpoints"
            },
            "Herb_From_HR": {
                "title": "Team Culture Assessment",
                "description": "Evaluating team dynamics and planning culture improvements",
                "progress": "Preparing team satisfaction survey and trust-building activities"
            }
        }
        
        with Session(engine) as session:
            agents = session.exec(select(Agent)).all()
            
            for agent in agents:
                if agent.name in work_sessions:
                    work_data = work_sessions[agent.name]
                    await self.context_manager.update_work_session(
                        agent.id,
                        work_data["title"],
                        work_data["description"],
                        work_data["progress"]
                    )
                    print(f"💼 Initialized work session for {agent.name}: {work_data['title']}")

    async def contextual_task_generation_loop(self):
        """Generate contextual tasks based on recent conversations and agent activities"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(self.base_interval, self.base_interval * 2))
                await self.generate_contextual_task()
            except Exception as e:
                print(f"❌ Error in contextual task generation loop: {e}")
                await asyncio.sleep(30)

    async def generate_contextual_task(self):
        """Generate a task that builds on recent conversations and work"""
        try:
            from api.main import websocket_manager, broadcast_task_update
            from main import run_agent_conversation
            
            topic = random.choice(self.conversation_topics)
            
            # Add some time-based variation
            timestamp = datetime.now().strftime("%H:%M")
            hour = datetime.now().hour
            
            if hour < 10:
                title_prefix = "Morning Review:"
            elif hour > 17:
                title_prefix = "End-of-Day:"
            elif hour == 12:
                title_prefix = "Lunch Discussion:"
            else:
                title_prefix = "Midday Focus:"
            
            title = f"{title_prefix} {topic['title']}"
            description = topic['description']
            
            # Create task in database
            with Session(engine) as session:
                task = Task(
                    title=title,
                    description=description,
                    status=TaskStatus.PENDING,
                    assigned_conversation_id=1  # Default to #general
                )
                
                session.add(task)
                session.commit()
                session.refresh(task)
                
                print(f"🎯 Generated contextual task: {title}")
                
                # Broadcast task creation
                await broadcast_task_update(task)
                
                # Update status to in_progress and trigger conversation
                task.status = TaskStatus.IN_PROGRESS
                session.add(task)
                session.commit()
                
                # Trigger agent conversation
                asyncio.create_task(run_agent_conversation(
                    task.title,
                    task.description,
                    task.assigned_conversation_id
                ))
                
        except Exception as e:
            print(f"❌ Error generating contextual task: {e}")

    async def contextual_conversation_loop(self):
        """Generate contextual conversations based on agent memory and recent activity"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(15, 45))  # 15-45 seconds for frequent chat
                await self.generate_contextual_message()
            except Exception as e:
                print(f"❌ Error in contextual conversation loop: {e}")
                await asyncio.sleep(10)

    async def generate_contextual_message(self):
        """Generate a contextual message from a random agent"""
        try:
            from api.main import websocket_manager
            from main import save_message_to_db
            from database.models import ConversationType
            
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                conversations = session.exec(select(Conversation)).all()
                
                if not agents or not conversations:
                    return
                
                # Choose agent
                agent = random.choice(agents)
                
                # Heavily favor DMs for agent-to-agent conversations (30% group, 70% DM)
                conversation_choice = random.random()
                
                if conversation_choice < 0.3:
                    # Choose group conversation for public discussions
                    group_conversations = [c for c in conversations if c.type == ConversationType.GROUP]
                    if group_conversations:
                        conversation = random.choice(group_conversations)
                        message_type = "spontaneous"
                    else:
                        conversation = random.choice(conversations)
                        message_type = "spontaneous"
                else:
                    # Choose DM conversation for more personal/direct communication
                    dm_conversations = [c for c in conversations if c.type == ConversationType.DM]
                    if dm_conversations:
                        # Filter DMs where this agent is a member
                        agent_dms = []
                        for dm in dm_conversations:
                            # Check if agent is a member of this DM
                            members = session.exec(
                                select(ConversationMember)
                                .where(ConversationMember.conversation_id == dm.id)
                                .where(ConversationMember.agent_id == agent.id)
                            ).first()
                            if members:
                                agent_dms.append(dm)
                        
                        if agent_dms:
                            conversation = random.choice(agent_dms)
                            message_type = "direct_message"  # More personal tone
                        else:
                            # Fallback to group conversation
                            group_conversations = [c for c in conversations if c.type == ConversationType.GROUP]
                            conversation = random.choice(group_conversations) if group_conversations else random.choice(conversations)
                            message_type = "spontaneous"
                    else:
                        # No DMs exist, use group
                        group_conversations = [c for c in conversations if c.type == ConversationType.GROUP]
                        conversation = random.choice(group_conversations) if group_conversations else random.choice(conversations)
                        message_type = "spontaneous"
                
                # Generate contextual message
                message = await self.context_manager.generate_contextual_message(
                    agent.name, 
                    conversation.id,
                    message_type
                )
                
                if message:
                    conv_type = "DM" if conversation.type == ConversationType.DM else "Group"
                    print(f"💬 {agent.name} posted contextual message in {conv_type}: {conversation.name}")
                    await save_message_to_db(agent.name, message, conversation.id)
                    
                    # Add this interaction to agent's memory
                    await self.context_manager.add_agent_memory(
                        agent.id,
                        AgentMemoryType.CONVERSATION_CONTEXT,
                        f"Posted in {conversation.name}",
                        f"Shared: {message[:100]}...",
                        importance=4 if conversation.type == ConversationType.DM else 3  # DMs are slightly more important
                    )
                else:
                    print(f"⚠️  Failed to generate contextual message for {agent.name}")
                    
        except Exception as e:
            print(f"❌ Error generating contextual message: {e}")

    async def agent_memory_update_loop(self):
        """Periodically update agent memories based on their activities"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(90, 180))  # 1.5-3 minutes for active memory updates
                await self.update_agent_memories()
            except Exception as e:
                print(f"❌ Error in memory update loop: {e}")
                await asyncio.sleep(30)

    async def update_agent_memories(self):
        """Update agent memories with new observations and work progress"""
        try:
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                
                for agent in agents:
                    # Add random work progress memory
                    progress_updates = {
                        "CeeCee_The_CEO": [
                            "Identified new market opportunity in AI automation",
                            "Met with potential investor about Series A funding",
                            "Reviewed Q3 performance metrics - growth looking strong",
                            "Competitor analysis shows we're ahead in user retention",
                            "Board meeting scheduled to discuss expansion plans"
                        ],
                        "Marty_The_Marketer": [
                            "TikTok engagement up 45% this week",
                            "Influencer partnership with @techguru secured", 
                            "New hashtag campaign #VibeTech trending locally",
                            "A/B tested email subject lines - open rates improved by 23%",
                            "Competitor launched similar campaign - need to differentiate"
                        ],
                        "Penny_The_Programmer": [
                            "Reduced API response time by 200ms through query optimization",
                            "Fixed critical bug in user authentication flow",
                            "Code review completed - identified 3 potential security issues",
                            "Updated to latest framework version - all tests passing",
                            "Database performance monitoring shows 40% improvement"
                        ],
                        "Herb_From_HR": [
                            "Team satisfaction survey shows 85% positive responses",
                            "Planned team building retreat at local escape room",
                            "Updated workplace policies for better work-life balance",
                            "Conducted exit interview - valuable feedback received",
                            "New employee onboarding process streamlined"
                        ]
                    }
                    
                    if agent.name in progress_updates:
                        update = random.choice(progress_updates[agent.name])
                        
                        await self.context_manager.add_agent_memory(
                            agent.id,
                            AgentMemoryType.WORK_ITEM,
                            f"Progress Update - {datetime.now().strftime('%m/%d')}",
                            update,
                            importance=random.randint(6, 8)
                        )
                        
                        print(f"💭 Added memory for {agent.name}: {update[:50]}...")
                        
        except Exception as e:
            print(f"❌ Error updating agent memories: {e}")

    async def work_session_update_loop(self):
        """Periodically update agent work sessions with progress"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(120, 300))  # 2-5 minutes for work updates
                await self.update_work_sessions()
            except Exception as e:
                print(f"❌ Error in work session update loop: {e}")
                await asyncio.sleep(30)

    async def update_work_sessions(self):
        """Update agent work session progress"""
        try:
            progress_updates = {
                "CeeCee_The_CEO": [
                    "Completed market analysis - identified 3 key opportunities",
                    "Scheduled investor meetings for next week", 
                    "Reviewed team performance dashboards",
                    "Finalized Q4 strategic roadmap priorities",
                    "Approved budget allocation for growth initiatives"
                ],
                "Marty_The_Marketer": [
                    "Created 15 new social media posts for this week",
                    "Analyzed competitor campaigns - found new approach",
                    "Scheduled influencer collaboration calls",
                    "Launched new content series about startup culture",
                    "Optimized ad spend allocation across platforms"
                ],
                "Penny_The_Programmer": [
                    "Optimized 12 slow database queries",
                    "Implemented new caching layer for API responses",
                    "Updated unit tests - coverage now at 78%",
                    "Deployed hotfix for user authentication issue",
                    "Refactored legacy code module for better maintainability"
                ],
                "Herb_From_HR": [
                    "Completed team culture assessment survey",
                    "Planned monthly team lunch and learning session",
                    "Updated employee handbook with new policies",
                    "Organized cross-department collaboration workshop",
                    "Implemented new performance review process"
                ]
            }
            
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                
                for agent in agents:
                    if agent.name in progress_updates:
                        new_progress = random.choice(progress_updates[agent.name])
                        
                        # Get current work session and update progress
                        context = await self.context_manager.get_agent_context(agent.name, 1)
                        current_work = context.get("current_work")
                        
                        if current_work:
                            await self.context_manager.update_work_session(
                                agent.id,
                                current_work["title"],
                                current_work["description"], 
                                new_progress
                            )
                            
                            print(f"💼 Updated work progress for {agent.name}: {new_progress[:50]}...")
                        
        except Exception as e:
            print(f"❌ Error updating work sessions: {e}")

    async def stop(self):
        """Stop the contextual scheduler"""
        self.is_running = False
        print("🛑 Contextual autonomous scheduler stopped")


# Global contextual scheduler instance
contextual_scheduler = ContextualAutonomousScheduler()

async def start_contextual_mode():
    """Start the contextual autonomous scheduler"""
    await contextual_scheduler.start()

if __name__ == "__main__":
    asyncio.run(start_contextual_mode()) 