import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlmodel import Session, select
from database.init_db import engine
from database.models import Agent, Conversation, Task, TaskStatus
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AutonomousScheduler:
    """Manages autonomous agent activities and conversations"""
    
    def __init__(self):
        self.is_running = False
        self.base_interval = 180  # 3 minutes base interval
        self.conversation_topics = [
            # Product Development
            {
                "title": "Product Roadmap Review",
                "description": "Let's review our product roadmap and prioritize features for the next quarter. What should we focus on to maximize user engagement?",
                "conversation_type": "brainstorming"
            },
            {
                "title": "User Experience Improvements", 
                "description": "We need to discuss the latest user feedback and identify key UX improvements. How can we make our product more intuitive?",
                "conversation_type": "problem_solving"
            },
            {
                "title": "Technical Architecture Decision",
                "description": "It's time to evaluate our current tech stack and consider if we need to refactor any components for better scalability.",
                "conversation_type": "technical"
            },
            
            # Marketing & Growth
            {
                "title": "Social Media Strategy",
                "description": "Our Twitter engagement is down 15% this month. Let's brainstorm some viral content ideas and campaign strategies.",
                "conversation_type": "marketing"
            },
            {
                "title": "Competitor Analysis",
                "description": "I've been researching our competitors. We need to discuss how to differentiate ourselves and capture more market share.",
                "conversation_type": "strategy"
            },
            {
                "title": "Customer Acquisition Campaign",
                "description": "We need a new customer acquisition strategy. What channels should we focus on to reach our target demographic?",
                "conversation_type": "growth"
            },
            
            # Operations & Culture
            {
                "title": "Team Building Initiative",
                "description": "Our team culture survey results are in. Let's discuss ways to improve collaboration and employee satisfaction.",
                "conversation_type": "hr"
            },
            {
                "title": "Budget Allocation Review",
                "description": "Q3 budget review time! We need to reallocate resources based on our current priorities and performance metrics.",
                "conversation_type": "finance"
            },
            {
                "title": "Process Optimization",
                "description": "Our development cycle seems slower lately. Let's identify bottlenecks and streamline our workflow.",
                "conversation_type": "operations"
            },
            
            # Innovation & Research
            {
                "title": "AI Integration Opportunities",
                "description": "Everyone's talking about AI. How can we integrate AI features into our product to stay competitive?",
                "conversation_type": "innovation"
            },
            {
                "title": "Market Research Analysis",
                "description": "I've compiled the latest market research data. Let's analyze trends and identify new opportunities.",
                "conversation_type": "research"
            },
            {
                "title": "Feature Request Prioritization",
                "description": "We have 47 feature requests in our backlog. Time to prioritize based on user impact and development effort.",
                "conversation_type": "planning"
            }
        ]
        
        self.spontaneous_conversations = [
            # Casual workplace chatter
            "Did anyone see that TechCrunch article about the startup that raised $50M with just a PowerPoint? Wild times!",
            "I just spilled coffee all over my keyboard. Anyone know where we keep the spare keyboards?",
            "Our office playlist needs an update. Who's been adding all this smooth jazz?",
            "Just got back from lunch at that new place downtown. Their wifi password is 'startup123' - not very secure!",
            
            # Work-related observations
            "I noticed our app's loading time increased by 200ms since the last deploy. Should we investigate?",
            "The new intern asked me what 'technical debt' means. Made me realize how much we've accumulated!",
            "Our customer support tickets are trending toward mobile-specific issues. Might be worth looking into.",
            "I've been thinking about our onboarding flow. Do we make it too complicated for new users?",
            
            # Industry commentary
            "Did you see that Google released another AI model? The pace of innovation is insane.",
            "Another day, another startup claiming they're 'disrupting' something. What are we disrupting again?",
            "I love how every company is now 'AI-powered'. Even my coffee shop claims to use AI for their loyalty program.",
            "Remember when everyone was pivoting to blockchain? Now it's all about AI agents. What's next?",
            
            # Office culture
            "Who keeps eating lunches from the company fridge? We need a fridge police.",
            "I think we should get a office plant. Studies show they improve productivity by 15%!",
            "Why do all startup offices have ping pong tables? Does anyone actually use them during work hours?",
            "Can we please have a 'no meetings Wednesday'? I need at least one day to actually code."
        ]

    async def start(self):
        """Start the autonomous scheduler"""
        if self.is_running:
            print("Autonomous scheduler is already running")
            return
            
        self.is_running = True
        print("🤖 Starting Autonomous Agent Scheduler...")
        print("🎯 Agents will now generate their own tasks and conversations!")
        
        # Start multiple concurrent tasks
        await asyncio.gather(
            self.task_generation_loop(),
            self.spontaneous_conversation_loop(),
            self.agent_status_update_loop(),
            self.background_activity_loop()
        )

    async def stop(self):
        """Stop the autonomous scheduler"""
        self.is_running = False
        print("🛑 Autonomous scheduler stopped")

    async def task_generation_loop(self):
        """Generate autonomous tasks periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(self.base_interval, self.base_interval * 2))
                await self.generate_autonomous_task()
            except Exception as e:
                print(f"❌ Error in task generation loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def spontaneous_conversation_loop(self):
        """Generate spontaneous conversations"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(60, 300))  # 1-5 minutes
                await self.generate_spontaneous_message()
            except Exception as e:
                print(f"❌ Error in spontaneous conversation loop: {e}")
                await asyncio.sleep(30)

    async def agent_status_update_loop(self):
        """Update agent statuses periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(90, 180))  # 1.5-3 minutes
                await self.update_agent_status()
            except Exception as e:
                print(f"❌ Error in status update loop: {e}")
                await asyncio.sleep(30)

    async def background_activity_loop(self):
        """Generate background activities"""
        while self.is_running:
            try:
                await asyncio.sleep(random.randint(240, 480))  # 4-8 minutes
                await self.generate_background_activity()
            except Exception as e:
                print(f"❌ Error in background activity loop: {e}")
                await asyncio.sleep(30)

    async def generate_autonomous_task(self):
        """Generate a random autonomous task"""
        try:
            # Import here to avoid circular imports
            from api.main import websocket_manager, broadcast_task_update
            
            # Choose a random conversation topic
            topic = random.choice(self.conversation_topics)
            
            # Add some randomness to make each task unique
            timestamp = datetime.now().strftime("%H:%M")
            topic_variations = [
                f"[{timestamp}] {topic['title']}",
                f"Urgent: {topic['title']}",
                f"Weekly {topic['title']}",
                f"Q3 {topic['title']}"
            ]
            
            title = random.choice(topic_variations)
            description = topic['description']
            
            # Add context based on time of day
            hour = datetime.now().hour
            if hour < 10:
                description = f"Good morning team! {description}"
            elif hour > 17:
                description = f"Before we wrap up today: {description}"
            elif hour == 12:
                description = f"Lunchtime discussion: {description}"
            
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
                
                print(f"🎯 Generated autonomous task: {title}")
                
                # Broadcast task creation
                await broadcast_task_update(task)
                
                # Update status to in_progress and trigger conversation
                task.status = TaskStatus.IN_PROGRESS
                session.add(task)
                session.commit()
                
                # Trigger agent conversation
                from main import run_agent_conversation
                asyncio.create_task(run_agent_conversation(
                    task.title,
                    task.description,
                    task.assigned_conversation_id
                ))
                
        except Exception as e:
            print(f"❌ Error generating autonomous task: {e}")

    async def generate_spontaneous_message(self):
        """Generate a spontaneous message from a random agent"""
        try:
            from api.main import websocket_manager
            from main import save_message_to_db
            
            # Get random agent and message
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                if not agents:
                    return
                    
                agent = random.choice(agents)
                message = random.choice(self.spontaneous_conversations)
                
                # Choose a random conversation (favor #random for casual chat)
                conversations = session.exec(select(Conversation)).all()
                if not conversations:
                    return
                    
                # 60% chance for #random, 40% for other channels
                if random.random() < 0.6:
                    conversation = next((c for c in conversations if c.name == "#random"), conversations[0])
                else:
                    conversation = random.choice(conversations)
                
                print(f"💬 {agent.name} posted spontaneous message in {conversation.name}")
                await save_message_to_db(agent.name, message, conversation.id)
                
        except Exception as e:
            print(f"❌ Error generating spontaneous message: {e}")

    async def update_agent_status(self):
        """Randomly update agent statuses"""
        try:
            from api.main import broadcast_agent_status_update
            
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                if not agents:
                    return
                    
                # Update 1-2 agents randomly
                agents_to_update = random.sample(agents, random.randint(1, min(2, len(agents))))
                
                for agent in agents_to_update:
                    # Choose a realistic status based on agent role
                    if agent.role == "CEO":
                        statuses = ["in_meeting", "reviewing_metrics", "strategic_planning"]
                    elif agent.role == "Programmer":
                        statuses = ["coding", "debugging", "code_review", "researching"]
                    elif agent.role == "Marketer":
                        statuses = ["content_creation", "social_media", "campaign_planning"]
                    elif agent.role == "HR":
                        statuses = ["interviewing", "policy_review", "team_building"]
                    else:
                        statuses = ["working", "in_meeting", "researching"]
                    
                    # Add idle status occasionally
                    if random.random() < 0.2:
                        statuses.append("idle")
                    
                    new_status = random.choice(statuses)
                    
                    # Update in database - agents can now set any status they want
                    agent.status = new_status
                    session.add(agent)
                    
                    print(f"📊 {agent.name} status updated to: {new_status}")
                    
                    # Broadcast status update
                    await broadcast_agent_status_update(agent.id, new_status)
                
                session.commit()
                
        except Exception as e:
            print(f"❌ Error updating agent status: {e}")

    async def generate_background_activity(self):
        """Generate background activities like code commits, research findings"""
        try:
            from main import save_message_to_db
            
            activities = [
                # Development activities
                "🔧 Just pushed a hotfix for the authentication bug. All tests passing!",
                "📊 Performance optimization complete: reduced API response time by 40%",
                "🐛 Found and fixed a memory leak in the data processing pipeline",
                "✅ Code review completed for the new user dashboard feature",
                "🚀 Deployed version 2.3.1 to staging environment",
                
                # Research activities
                "📈 Market research update: Our target demographic engagement increased 23% this quarter",
                "🔍 Competitive analysis shows we're ahead in user retention but behind in acquisition",
                "📱 User survey results: 84% satisfaction rate, top request is mobile app",
                "📊 A/B test results: New onboarding flow improved conversion by 15%",
                
                # Business activities
                "💰 Monthly revenue report: We're 12% above target for this quarter!",
                "📞 Just finished a great call with a potential enterprise client",
                "📧 Customer support response time improved to under 2 hours average",
                "🎯 Updated our OKRs based on this month's performance metrics",
                
                # Creative activities
                "🎨 New brand guidelines are ready for review - love the updated color palette!",
                "📝 Blog post about our latest feature is live - already getting great engagement",
                "🎥 Product demo video is complete, ready for the marketing campaign",
                "📱 Social media engagement up 45% since we started the community challenges"
            ]
            
            with Session(engine) as session:
                agents = session.exec(select(Agent)).all()
                conversations = session.exec(select(Conversation)).all()
                
                if not agents or not conversations:
                    return
                
                # Choose random agent and activity
                agent = random.choice(agents)
                activity = random.choice(activities)
                
                # Choose appropriate conversation based on activity type
                if "🔧" in activity or "📊" in activity or "🐛" in activity:
                    # Technical activities go to #brainstorming
                    conversation = next((c for c in conversations if c.name == "#brainstorming"), conversations[0])
                elif "💰" in activity or "📞" in activity:
                    # Business activities go to #general
                    conversation = next((c for c in conversations if c.name == "#general"), conversations[0])
                else:
                    # Other activities can go anywhere
                    conversation = random.choice(conversations)
                
                print(f"⚡ {agent.name} shared background activity in {conversation.name}")
                await save_message_to_db(agent.name, activity, conversation.id)
                
        except Exception as e:
            print(f"❌ Error generating background activity: {e}")

# Global scheduler instance
autonomous_scheduler = AutonomousScheduler()

async def start_autonomous_mode():
    """Start the autonomous scheduler"""
    await autonomous_scheduler.start()

async def stop_autonomous_mode():
    """Stop the autonomous scheduler"""
    await autonomous_scheduler.stop()

if __name__ == "__main__":
    # Run the scheduler directly
    asyncio.run(start_autonomous_mode()) 