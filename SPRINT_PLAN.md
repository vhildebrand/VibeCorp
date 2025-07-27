# Project Sprint Plan: The Autonomous Startup Simulation

This document breaks down the development work outlined in the revised `PRODUCT_REQUIREMENTS.md` and `TECHNICAL_DESIGN.md` into a series of focused sprints. The goal is to build a truly autonomous multi-agent simulation.

---

## Sprint 1: The Asynchronous Core & Agent Autonomy

**Goal:** Refactor the backend to replace the scheduler-based system with an asynchronous, agent-driven architecture. Each agent will run its own independent loop.

### Tasks:
- [x] **Project Cleanup:**
    - [x] Delete `agents/autonomous_scheduler.py` and `agents/contextual_scheduler.py`.
    - [x] Remove all usage of the old schedulers from the codebase.
- [x] **Database Refactor (`database/models.py`):**
    - [x] Add the new `AgentTask` table to track individual agent to-do lists.
    - [x] Remove the `conversation_members` table and simplify `conversations` to only represent channels.
- [x] **New Agent Core (`agents/agent_manager.py`):**
    - [x] Create a new `AgentManager` class responsible for initializing agents.
    - [x] Implement the core `run_agent_loop(agent)` function. This is the asynchronous loop where each agent will check messages, consult its to-do list, and execute tasks.
- [x] **Communication Bus (`api/main.py`):**
    - [x] Create a central `asyncio.Queue` to act as the message bus for all agent communication.
    - [x] Implement the `POST /simulation/start` endpoint to initialize the `AgentManager` and start the `run_agent_loop` for all agents as concurrent `asyncio` tasks.
- [x] **Initial Agent Prompts (`agents/agents.py`):**
    - [x] Write detailed `system_message` prompts for the initial set of agents (CEO, PM, Dev). The prompts must instruct the agents on how to use their to-do list and collaborate to achieve a high-level goal.

**Deliverable:** ✅ A backend that can start and run a set of agents in parallel. We can't see them talk yet, but the core asynchronous loops will be running. We can verify this with logging.

---

## Sprint 2: Task Management & Basic Tooling

**Goal:** Empower agents with the ability to manage their own tasks and perform basic actions like file I/O and web searches.

### Tasks:
- [x] **To-Do List Tools (`company/tools.py`):**
    - [x] Create tools for agents to manage their own tasks: `add_task(title: str, description: str, priority: int)`, `complete_task(task_id: int)`, `get_my_todo_list() -> List[AgentTask]`.
- [x] **Filesystem Tools (`company/tools.py`):**
    - [x] Create tools for reading and writing files: `write_to_file(path: str, content: str)`, `read_file(path: str) -> str`, `list_files(path: str) -> List[str]`.
- [x] **Web Search Tool (`company/tools.py`):**
    - [x] Implement a `web_search(query: str) -> str` tool using an external library like `requests` or a search API.
- [x] **Tool Integration:**
    - [x] Make the tools available to the agents within their `run_agent_loop`.
    - [x] Update the agent prompts to explicitly instruct them on how and when to use these new tools.
- [x] **Agent-to-Agent Communication:**
    - [x] Implement the logic for agents to send messages to the central `asyncio.Queue`.
    - [x] The `run_agent_loop` should now process messages from the queue, allowing agents to react to each other.

**Deliverable:** ✅ Agents can now manage their own to-do lists, read/write files, and search the web. They can also send messages to each other, which we can observe through backend logging.

---

## Sprint 3: Backend API & Frontend Integration

**Goal:** Expose the state of the autonomous simulation via the API and connect the frontend to display agent activities in real-time.

### Tasks:
- [x] **API Endpoints (`api/main.py`):**
    - [x] Implement the new API endpoints defined in the technical design: `GET /agents`, `GET /agents/{agent_id}/tasks`, `GET /conversations/{conv_id}/messages`.
- [x] **Backend WebSocket (`api/main.py`):**
    - [x] Create a listener that reads from the `asyncio.Queue`.
    - [x] When a new message is added to the queue, broadcast it to all connected frontend clients via the `/ws` WebSocket.
    - [x] Broadcast updates when an agent's task list changes.
- [x] **Frontend State Management (`startup-simulator-ui/src/store.ts`):**
    - [x] Add `agentTasks` to the Zustand store.
    - [x] Implement the WebSocket client logic to listen for new messages and task updates and update the store accordingly.
- [x] **UI Implementation (`startup-simulator-ui/src/`):**
    - [x] Create the new `TodoList.tsx` component to display the contents of `agentTasks` for a selected agent.
    - [x] Integrate the `TodoList.tsx` component into the `AgentProfile.tsx` or a similar view.

**Deliverable:** ✅ A fully connected application. The frontend displays conversations and agent to-do lists in real-time as the simulation runs on the backend.

---

## Sprint 4: Advanced Agents & Simulation Polish

**Goal:** Refine agent behavior, expand the agent team, and improve the overall quality and believability of the simulation.

### Tasks:
- [x] **New Agent Roles:**
    - [x] Add more specialized agents: a Frontend Developer, a Backend Developer, a Marketer, and an HR Manager.
    - [x] Write detailed system prompts and define specific toolsets for each new role.
- [x] **Concrete Development Tools & Deliverables:**
    - [x] Implement `create_code_file` tool for agents to write actual Python, HTML, CSS, JavaScript code
    - [x] Add `create_feature_spec` tool for detailed feature documentation with requirements
    - [x] Create `build_database_schema` tool for SQL schema generation
    - [x] Add `create_api_endpoint` tool for API documentation and templates
    - [x] Implement `deploy_mvp_feature` tool for tracking completed deliverables
- [x] **Task System Overhaul:**
    - [x] Replace vague tasks ("research", "brainstorm") with specific deliverable-focused tasks
    - [x] Add duplicate prevention to stop agents from assigning the same tasks repeatedly
    - [x] Modified decision logic to prioritize building concrete outputs over communication
    - [x] Tasks now specify exact deliverables (filenames, code, documentation)
- [x] **Agent Decision Logic Improvements:**
    - [x] Agents now create actual code files based on task requirements
    - [x] Programming tasks result in functional Python authentication systems, HTML dashboards
    - [x] Marketing tasks create complete landing pages with HTML/CSS
    - [x] Documentation tasks produce structured markdown files with processes
    - [x] Tasks automatically complete when deliverables are created
- [x] **Error Handling & Resilience:**
    - [x] Improve the `run_agent_loop` to gracefully handle errors during tool execution or LLM calls, preventing a single agent failure from stopping the entire simulation.

**Deliverable:** ✅ A much more robust and productive simulation. Agents now create concrete deliverables instead of just talking. The CEO assigns specific, actionable tasks with clear outputs. Programmers write actual authentication systems and dashboards. Marketers build real landing pages. The simulation produces tangible results that can be reviewed and deployed.

**Key Improvements Made:**
- **Concrete Deliverables**: Agents now create actual files (`auth_system.py`, `dashboard.html`, `landing_page.html`)
- **Specific Task Assignment**: CEO assigns tasks with exact deliverables specified
- **Automated Completion**: Tasks complete when real work is done, not based on probability
- **Duplicate Prevention**: No more repeated task assignments
- **Building Over Talking**: Decision logic prioritizes creating files over sending messages

---

## Sprint 5: Deployment & Final Touches

**Goal:** Prepare the application for production and deploy it to the cloud.

### Tasks:
- [ ] **Containerization (`Dockerfile`):**
    - [ ] Ensure the `Dockerfile` for the FastAPI backend is up-to-date with all new dependencies.
- [ ] **CI/CD (GitHub Actions):**
    - [ ] Create a workflow to automatically run tests for the agent tools and backend API.
    - [ ] Set up a deployment workflow to build and deploy the frontend and backend when changes are pushed to `main`.
- [ ] **Deployment:**
    - [ ] Deploy the React frontend to Vercel.
    - [ ] Deploy the backend container to a service like Google Cloud Run.
- [ ] **Final Configuration:**
    - [ ] Set up production environment variables.
    - [ ] Configure the production database.
    - [ ] Verify that CORS is correctly configured for the production domains.

**Deliverable:** The live, publicly accessible web application. 