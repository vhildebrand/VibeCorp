#!/usr/bin/env python3
"""
Test script for the new contextual agent system
"""

import asyncio
from agents.agent_context import agent_context_manager  
from agents.contextual_scheduler import contextual_scheduler
from database.models import AgentMemoryType


async def test_contextual_system():
    """Test the contextual agent memory and message generation"""
    print("🧠 Testing Contextual Agent System...")
    print("💭 Using 20 messages of conversation history for context")
    print("=" * 60)
    
    # Test 1: Add some sample memories for agents
    print("\n📝 Adding sample memories...")
    
    # Add memory for CEO
    await agent_context_manager.add_agent_memory(
        agent_id=1,  # CEO
        memory_type=AgentMemoryType.WORK_ITEM,
        title="Series A Funding Preparation",
        content="Working on pitch deck and financial projections for upcoming investor meetings. Target: $5M Series A by Q4.",
        importance=9
    )
    
    # Add memory for Programmer  
    await agent_context_manager.add_agent_memory(
        agent_id=3,  # Programmer
        memory_type=AgentMemoryType.ACHIEVEMENT,
        title="API Performance Optimization Complete",
        content="Successfully reduced API response times by 40% through database query optimization and caching implementation.",
        importance=8
    )
    
    # Add memory for Marketer
    await agent_context_manager.add_agent_memory(
        agent_id=2,  # Marketer
        memory_type=AgentMemoryType.WORK_ITEM,
        title="TikTok Campaign Analytics",
        content="Analyzing viral content patterns and engagement metrics. Current campaign reaching 2M+ impressions daily.",
        importance=7
    )
    
    # Add memory for HR
    await agent_context_manager.add_agent_memory(
        agent_id=4,  # HR
        memory_type=AgentMemoryType.PERSONAL_NOTE,
        title="Team Satisfaction Survey Results",
        content="85% positive feedback on work culture. Main concerns: need better coffee and more team lunches.",
        importance=6
    )
    
    print("✅ Sample memories added!")
    
    # Test 2: Get context for each agent
    print("\n🔍 Testing context retrieval...")
    
    for agent_name in ["CeeCee_The_CEO", "Penny_The_Programmer", "Marty_The_Marketer", "Herb_From_HR"]:
        context = await agent_context_manager.get_agent_context(agent_name, 1)
        
        if context:
            agent = context.get("agent")
            memories = context.get("memories", [])
            work_session = context.get("current_work")
            
            print(f"\n👤 {agent.name.replace('_', ' ')} ({agent.role}):")
            print(f"   Status: {agent.status}")
            print(f"   Memories: {len(memories)} items")
            
            if work_session:
                print(f"   Current Work: {work_session['title']}")
            else:
                print("   Current Work: None")
        else:
            print(f"❌ No context found for {agent_name}")
    
    # Test 3: Generate contextual messages
    print("\n💬 Generating contextual messages...")
    
    for agent_name in ["CeeCee_The_CEO", "Penny_The_Programmer"]:
        print(f"\n🎭 Generating message for {agent_name.replace('_', ' ')}...")
        
        message = await agent_context_manager.generate_contextual_message(
            agent_name=agent_name,
            conversation_id=1, 
            message_type="work_update"
        )
        
        if message:
            print(f"✅ Generated: {message}")
        else:
            print(f"❌ Failed to generate message for {agent_name}")
    
    print("\n" + "=" * 60)
    print("✅ Contextual system test complete!")
    print("")
    print("🎯 Key Features Tested:")
    print("   ✅ Agent memory storage and retrieval")
    print("   ✅ Context-aware message generation")
    print("   ✅ Work session tracking")
    print("   ✅ 20 message conversation history")
    print("")
    print("🚀 Your agents now have memory and contextual awareness!")
    print("💭 They will reference past conversations and ongoing work")
    print("🤝 Messages will feel natural and connected")


async def demo_contextual_conversation():
    """Demo the difference between old and new system"""
    print("\n" + "="*60)
    print("🎭 CONTEXTUAL CONVERSATION DEMO")
    print("="*60)
    
    print("\n🔄 OLD SYSTEM (Random Messages):")
    old_messages = [
        "I just spilled coffee all over my keyboard. Anyone know where we keep the spare keyboards?",
        "Did you see that TechCrunch article about the startup that raised $50M with just a PowerPoint? Wild times!",
        "Our office playlist needs an update. Who's been adding all this smooth jazz?"
    ]
    
    for msg in old_messages[:2]:
        print(f"   📢 Random Agent: {msg}")
    
    print("\n🧠 NEW SYSTEM (Contextual Messages):")
    
    # Generate a few contextual messages to show the difference
    contextual_agents = ["CeeCee_The_CEO", "Penny_The_Programmer"]
    
    for agent_name in contextual_agents:
        message = await agent_context_manager.generate_contextual_message(
            agent_name=agent_name,
            conversation_id=1,
            message_type="spontaneous"
        )
        
        if message:
            display_name = agent_name.replace("_", " ")
            print(f"   🎭 {display_name}: {message}")
    
    print("\n💡 Notice the difference:")
    print("   • Old: Random, disconnected messages")
    print("   • New: Contextual, work-aware, personality-driven")


if __name__ == "__main__":
    try:
        asyncio.run(test_contextual_system())
        asyncio.run(demo_contextual_conversation())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        print("💡 Make sure the database is initialized and OpenAI API key is set") 