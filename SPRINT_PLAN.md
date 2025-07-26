# Project Sprint Plan: The AutoGen Startup Simulation

This document breaks down the development work outlined in the `PRODUCT_REQUIREMENTS.md` and `TECHNICAL_DESIGN.md` into a series of two-week sprints. Each sprint has a clear goal and a set of deliverables.

---

## Sprint 1: Backend Foundation & Core Agent Setup

**Goal:** Establish the core Python backend, define the AI agents, and enable basic conversations. This sprint focuses on getting the "brains" of the operation running in a local environment.

### Tasks:
- [ ] **Project Setup:**
    - [ ] Initialize Python virtual environment and install dependencies: `autogen-agentchat`, `fastapi`, `uvicorn`, `sqlalchemy`, `sqlmodel`, `websockets`.
    - [ ] Set up the `.env` file for API keys.
- [ ] **Agent Definition (`agents/agents.py`):**
    - [ ] Create `ConversableAgent` instances for the CEO, Marketer, Programmer, and HR agents.
    - [ ] Write detailed `system_message` prompts to define each agent's personality, role, and communication style.
- [ ] **Database Models (`database/models.py`):**
    - [ ] Define `SQLModel` tables for `Agent`, `Conversation`, `Message`, and `Task`.
    - [ ] Create a database initialization script.
- [ ] **Core Conversation Logic (`main.py`):**
    - [ ] Implement a script to instantiate the agents.
    - [ ] Create a `GroupChat` and a `GroupChatManager`.
    - [ ] Implement a test function to trigger a conversation and verify that messages are being generated and saved to the database.

**Deliverable:** A set of Python scripts that can be run from the terminal to demonstrate agents conversing and their interactions being persisted in a local SQLite database.

---

## Sprint 2: API Layer & Agent Tooling

**Goal:** Expose the agent simulation via a web API and empower agents with their first set of tools.

### Tasks:
- [ ] **FastAPI Setup (`api/main.py`):**
    - [ ] Create the main FastAPI application.
    - [ ] Implement CORS middleware to allow frontend access.
- [ ] **API Endpoints:**
    - [ ] `GET /agents`: Returns a list of all defined agents from the database.
    - [ ] `GET /conversations`: Returns a list of all conversations (e.g., `#general`).
    - [ ] `GET /conversations/{conv_id}/messages`: Fetches the history for a specific conversation.
    - [ ] `POST /tasks`: A stub endpoint that will eventually trigger a new agent task.
- [ ] **Tool Definition (`company/tools.py`):**
    - [ ] Define initial Python functions for tools: `post_to_twitter(message: str)` and `write_code_to_file(filename: str, code: str)`.
- [ ] **Executor Agent:**
    - [ ] Create a `UserProxyAgent` named `Executor`.
    - [ ] Use `register_function` to link the tools to the `Executor` and the agents who can propose them.
    - [ ] Modify the group chat to include the `Executor` to handle function calls.

**Deliverable:** A runnable FastAPI server. We can use `curl` or a tool like Postman to hit the API endpoints and retrieve data from the backend.

---

## Sprint 3: Frontend Scaffolding & UI Mockups

**Goal:** Build the static structure of the React frontend, creating a visually appealing and intuitive Slack/Teams clone with mock data.

### Tasks:
- [ ] **Component Architecture (`startup-simulator-ui/src/components/`):**
    - [ ] Create the file structure for all components outlined in the TDD (`Layout`, `Sidebar`, `ChatPane`, `ChannelList`, `MessageList`, `AgentMessage`, etc.).
- [ ] **State Management (Zustand):**
    - [ ] Set up a Zustand store (`src/store.ts`) with slices for `agents`, `conversations`, and `messages`.
- [ ] **UI Implementation:**
    - [ ] Build out the static components using Tailwind CSS and mock data from the Zustand store.
    - [ ] `Layout.tsx`: Implement the main two-column layout.
    - [ ] `Sidebar.tsx`: Display lists of channels and DMs.
    - [ ] `ChatPane.tsx`: Display a conversation from the mock data.
    - [ ] `AgentMessage.tsx`: Style message bubbles differently based on the agent.

**Deliverable:** A fully styled, responsive React application that displays a mock conversation. It should look and feel like the final product, but with static data.

---

## Sprint 4: Full-Stack Integration & Real-Time Updates

**Goal:** Connect the frontend and backend, replacing mock data with live data and enabling real-time communication via WebSockets.

### Tasks:
- [ ] **API Integration:**
    - [ ] In the React app, replace mock data by fetching from the FastAPI endpoints (`/agents`, `/conversations`, etc.) on initial load.
- [ ] **Backend WebSocket (`api/main.py`):**
    - [ ] Create a `/ws` WebSocket endpoint in FastAPI.
    - [ ] Implement logic to broadcast new messages and agent status updates to all connected clients.
- [ ] **Frontend WebSocket:**
    - [ ] Implement a WebSocket client service in React to connect to the backend.
    - [ ] When a message is received via WebSocket, update the Zustand store. This will cause the UI to re-render automatically.
- [ ] **Task Initiation:**
    - [ ] Fully implement the `POST /tasks` endpoint to kick off a new `GroupChat` session in the background.
    - [ ] As the agents in that session converse, their messages should be broadcast over the WebSocket.

**Deliverable:** A fully functional web application. The frontend loads initial data via REST and then receives real-time updates for new messages via WebSockets.

---

## Sprint 5: Advanced Features & Polish

**Goal:** Enhance the simulation's depth by adding features that allow for more complex agent interactions and better user observability.

### Tasks:
- [ ] **Advanced Communication:**
    - [ ] Implement the backend routing logic to support multiple channels and 1-on-1 DMs.
    - [ ] Update the UI to allow switching between these different conversations.
- [ ] **Agent Status Updates:**
    - [ ] When an agent decides to use a tool, update its status (e.g., "Penny is `Coding`"). Push this status change over the WebSocket.
    - [ ] Display the agent's status in the UI (e.g., in the sidebar).
- [ ] **"Company Files" Viewer:**
    - [ ] Create a new API endpoint to list files created by agents.
    - [ ] Create a new UI component that displays the contents of these files.
- [ ] **Refine Agent Prompts:**
    - [ ] Based on observed conversations, tweak the `system_message` prompts to improve narrative quality and agent behavior.

**Deliverable:** A more dynamic application where users can follow multiple conversation threads and have better insight into what the agents are actively doing.

---

## Sprint 6: Deployment & Final Touches

**Goal:** Prepare the application for production and deploy it to the cloud.

### Tasks:
- [ ] **Containerization:**
    - [ ] Create a `Dockerfile` for the FastAPI backend.
- [ ] **CI/CD (GitHub Actions):**
    - [ ] Create a workflow to automatically run tests and linting.
    - [ ] Create a second workflow to build and deploy the frontend and backend when changes are pushed to `main`.
- [ ] **Deployment:**
    - [ ] Deploy the React frontend to Netlify or Vercel.
    - [ ] Deploy the backend container to a service like Google Cloud Run or AWS Fargate.
- [ ] **Final Configuration:**
    - [ ] Set up production environment variables.
    - [ ] Ensure the production database is configured and migrated.
    - [ ] Verify that CORS is correctly configured for the production domains.

**Deliverable:** The live, publicly accessible web application. 