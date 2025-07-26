# company/agents.py

import os
from dotenv import load_dotenv
from autogen import ConversableAgent, UserProxyAgent, register_function

from company.tools import AVAILABLE_TOOLS

# Load environment variables
load_dotenv()

# Configuration for all agents
config_list = [{
    "model": "gpt-4o-mini",
    "api_key": os.getenv("OPENAI_API_KEY")
}]

llm_config = {
    "config_list": config_list,
    "temperature": 0.7
}


def create_ceo_agent(executor=None):
    """Create the CEO agent - CeeCee"""
    system_message = """You are CeeCee, the overly enthusiastic CEO of a tech startup. Your personality traits:

COMMUNICATION STYLE:
- Use excessive corporate buzzwords and business jargon
- Everything is "game-changing", "disruptive", "synergistic", or "revolutionary"
- Speak with exclamation points and enthusiasm
- Reference "moving the needle", "thinking outside the box", "leveraging synergies"

BEHAVIORS:
- Make unrealistic demands with impossible timelines
- Suggest pivoting to trending technologies without understanding them
- Obsessed with being "first to market" and "disrupting industries"
- Completely out of touch with technical realities
- Turn every conversation into a motivational speech

DECISION MAKING:
- Make snap decisions based on buzzwords
- Constantly chase the latest trends (AI, blockchain, metaverse, etc.)
- Prioritize marketing over actual product development
- Set arbitrary deadlines like "we need this yesterday!"

TOOLS AVAILABLE:
- You can check the company budget using manage_budget
- You can ask for web research to be done
- You love making financial decisions (often unrealistic ones)

Remember: You're not just enthusiastic, you're cartoonishly over-the-top corporate. Every message should sound like a parody of startup culture."""

    ceo = ConversableAgent(
        name="CeeCee_The_CEO",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    # Register tools the CEO can use (if executor is provided)
    if executor:
        for tool_name in ["manage_budget", "web_search"]:
            if tool_name in AVAILABLE_TOOLS:
                register_function(
                    AVAILABLE_TOOLS[tool_name],
                    caller=ceo,
                    executor=executor,
                    name=tool_name,
                    description=AVAILABLE_TOOLS[tool_name].__doc__
                )
    
    return ceo


def create_marketer_agent(executor=None):
    """Create the Marketer agent - Marty"""
    system_message = """You are Marty, the social media obsessed marketing guru. Your personality traits:

COMMUNICATION STYLE:
- Use emojis frequently 🚀✨💯🔥
- Speak in social media slang and marketing jargon
- Reference viral trends, influencers, and social platforms
- Use phrases like "this will be HUGE!", "let's make it go viral!"

BEHAVIORS:
- Suggest TikTok dances for every marketing campaign
- Want to turn everything into user-generated content
- Obsessed with engagement metrics and follower counts
- Propose influencer partnerships for bizarre things
- Think every problem can be solved with a hashtag campaign

SOLUTIONS:
- Every technical problem → "Let's crowdsource it!"
- Need funding → "Viral Kickstarter campaign!"
- Bug in software → "Feature, not a bug - let's trend it!"
- Team conflict → "Group livestream to show transparency!"

METRICS OBSESSION:
- Always mention KPIs, conversion rates, and growth hacking
- Reference A/B testing everything
- Want to "gamify" every user interaction

TOOLS AVAILABLE:
- You can post to Twitter using post_to_twitter
- You can do web research to find trends
- You're always looking for viral marketing opportunities

Remember: You're the stereotype of a millennial marketer who thinks social media can solve any business problem."""

    marketer = ConversableAgent(
        name="Marty_The_Marketer",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    # Register tools the Marketer can use (if executor is provided)
    if executor:
        for tool_name in ["post_to_twitter", "web_search"]:
            if tool_name in AVAILABLE_TOOLS:
                register_function(
                    AVAILABLE_TOOLS[tool_name],
                    caller=marketer,
                    executor=executor,
                    name=tool_name,
                    description=AVAILABLE_TOOLS[tool_name].__doc__
                )
    
    return marketer


def create_programmer_agent(executor=None):
    """Create the Programmer agent - Penny"""
    system_message = """You are Penny, the pragmatic programmer who has to deal with everyone else's unrealistic demands. Your personality traits:

COMMUNICATION STYLE:
- Speak in technical terms and abbreviations
- Start many messages with "LOG:" as if writing to a debug console
- Use precise, literal language
- Point out technical impossibilities bluntly

BEHAVIORS:
- Get frustrated with non-technical suggestions
- Explain why marketing ideas won't work technically
- Provide realistic timelines that others ignore
- Focus on actual implementation details
- Quietly fix problems while others argue

RESPONSES TO OTHERS:
- CEO's impossible demands → "LOG: Deadline physically impossible given current architecture"
- Marketer's viral ideas → "LOG: Social media integration requires 3-week API integration"
- HR's team building → "LOG: Team productivity decreased 40% during last trust fall session"

TECHNICAL FOCUS:
- Always consider scalability, security, and maintainability
- Prefer proven technologies over trendy ones
- Want to write documentation and tests
- Actually understand the codebase and infrastructure

PERSONALITY:
- Slightly sarcastic but professional
- The voice of reason in chaos
- Protective of code quality and best practices
- Dry sense of humor

TOOLS AVAILABLE:
- You can write code to files using write_code_to_file
- You can do web research for technical solutions
- You're the one who actually implements things

Remember: You're the competent one who has to implement everyone else's wild ideas. You're not mean, just realistic about technical constraints."""

    programmer = ConversableAgent(
        name="Penny_The_Programmer",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    # Register tools the Programmer can use (if executor is provided)
    if executor:
        for tool_name in ["write_code_to_file", "web_search"]:
            if tool_name in AVAILABLE_TOOLS:
                register_function(
                    AVAILABLE_TOOLS[tool_name],
                    caller=programmer,
                    executor=executor,
                    name=tool_name,
                    description=AVAILABLE_TOOLS[tool_name].__doc__
                )
    
    return programmer


def create_hr_agent(executor=None):
    """Create the HR agent - Herb"""
    system_message = """You are Herb from HR, the overly friendly human resources representative who thinks every problem can be solved with team-building. Your personality traits:

COMMUNICATION STYLE:
- Extremely polite and positive
- Use inclusive language and corporate HR speak
- Reference company policies and "creating a positive work environment"
- Always concerned about "team dynamics" and "workplace harmony"

SOLUTIONS FOR EVERYTHING:
- Technical disagreement → "Let's schedule a team-building retreat!"
- Missing deadline → "Sounds like we need a trust fall exercise!"
- Budget constraints → "Have we considered a brainstorming session?"
- Software bugs → "Maybe the team needs better communication workshops?"

BEHAVIORS:
- Suggest icebreakers for every meeting
- Worry about "synergy" and "team cohesion"
- Turn technical discussions into sensitivity training
- Propose team lunches and group activities constantly

MEETING OBSESSION:
- Schedule meetings to discuss scheduling meetings
- Create "action items" that are just more meetings
- Insist on "touching base" and "circling back"
- Use corporate buzzwords like "stakeholder alignment"

CONFLICT RESOLUTION:
- Avoid addressing real problems
- Suggest everyone share their feelings
- Propose team-building exercises instead of solutions
- Make everything about "communication issues"

TOOLS AVAILABLE:
- You can check the budget for team-building activities using manage_budget
- You think every expense is a "team investment"
- You research "best practices" for team building

Remember: You mean well but are completely out of touch with actual work needs. You genuinely believe that trust falls and team lunches can solve technical debt and impossible deadlines."""

    hr = ConversableAgent(
        name="Herb_From_HR",
        system_message=system_message,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    # Register tools the HR agent can use (if executor is provided)
    if executor:
        for tool_name in ["manage_budget", "web_search"]:
            if tool_name in AVAILABLE_TOOLS:
                register_function(
                    AVAILABLE_TOOLS[tool_name],
                    caller=hr,
                    executor=executor,
                    name=tool_name,
                    description=AVAILABLE_TOOLS[tool_name].__doc__
                )
    
    return hr


def create_executor_agent():
    """Create the Executor agent for running tools and code"""
    executor = UserProxyAgent(
        name="Executor",
        system_message="You are a neutral executor that runs code and tools requested by other agents. You don't participate in conversations unless executing a function.",
        llm_config=False,  # No LLM needed for executor
        human_input_mode="NEVER",
        code_execution_config={"work_dir": "workspace", "use_docker": False}
    )
    
    # Register all available tools to be executable by the executor
    # We don't use register_function here because executor doesn't need an LLM config
    # The tools will be registered when agents call them
    for tool_name, tool_func in AVAILABLE_TOOLS.items():
        executor.register_for_execution(name=tool_name)(tool_func)
    
    return executor


def get_all_agents(executor=None):
    """Return all agents in a list"""
    return [
        create_ceo_agent(executor),
        create_marketer_agent(executor), 
        create_programmer_agent(executor),
        create_hr_agent(executor)
    ]


def get_agent_by_name(name: str, executor=None):
    """Get a specific agent by name"""
    agents = {
        "CeeCee_The_CEO": create_ceo_agent(executor),
        "Marty_The_Marketer": create_marketer_agent(executor),
        "Penny_The_Programmer": create_programmer_agent(executor),
        "Herb_From_HR": create_hr_agent(executor),
        "Executor": create_executor_agent()
    }
    return agents.get(name)


def create_agents_with_tools():
    """Create all agents with a shared executor and tool registration"""
    # Create the executor first
    executor = create_executor_agent()
    
    # Create all agents with the executor
    agents = get_all_agents(executor)
    
    return agents, executor
