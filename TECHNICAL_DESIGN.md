# Technical Design Document: The AutoGen Startup Simulation

## 1. System Architecture

The system is composed of three main parts: a **Frontend** React application, a **Backend API** built with FastAPI, and the **Agent Service** which orchestrates the autonomous agents. The key change from the previous design is the shift from a turn-based, managed system to a fully asynchronous, goal-driven one.

```mermaid
graph TD
    User[<fa:fa-user> User] -->|Interacts with| Frontend[<fa:fa-desktop> Frontend<br/>(React, Vite, Zustand)];
    
    subgraph "Cloud Infrastructure"
        Frontend -->|HTTP/REST API &<br/>WebSocket| BackendAPI[<fa:fa-server> Backend API<br/>(FastAPI, Uvicorn)];
        
        subgraph "Autonomous Agent Core"
            BackendAPI -->|Publishes to| MessageQueue[<fa:fa-exchange-alt> Message Queue<br/>(AsyncIO Queue)];
            
            subgraph "Company Simulation"
                Agent1[<fa:fa-robot> CEO Agent] -->|Reads/Writes| MessageQueue;
                Agent2[<fa:fa-robot> PM Agent] -->|Reads/Writes| MessageQueue;
                Agent3[<fa:fa-robot> Dev Agent] -->|Reads/Writes| MessageQueue;
            end

            Agent1 -->|Runs| AgentLoop1[<fa:fa-sync-alt> Agent Loop];
            Agent2 -->|Runs| AgentLoop2[<fa:fa-sync-alt> Agent Loop];
            Agent3 -->|Runs| AgentLoop3[<fa:fa-sync-alt> Agent Loop];

            AgentLoop1 -->|Uses| Tooling[<fa:fa-tools> Tooling Layer<br/>(File I/O, Web Search)];
            AgentLoop2 -->|Uses| Tooling;
            AgentLoop3 -->|Uses| Tooling;

            AgentLoop1 -->|Updates| Database[<fa:fa-database> Database<br/>(PostgreSQL/SQLite)];
            AgentLoop2 -->|Updates| Database;
            AgentLoop3 -->|Updates| Database;
        end

        BackendAPI -->|Reads Data| Database;
    end

    style User fill:#D6EAF8,stroke:#5DADE2
    style Frontend fill:#D1F2EB,stroke:#48C9B0
    style BackendAPI fill:#FDEDEC,stroke:#F1948A
    style MessageQueue fill:#FDEBD0,stroke:#F5B041
    style Agent1 fill:#E8DAEF,stroke:#A569BD
    style Agent2 fill:#E8DAEF,stroke:#A569BD
    style Agent3 fill:#E8DAEF,stroke:#A569BD
    style AgentLoop1 fill:#D4E6F1,stroke:#5499C7
    style AgentLoop2 fill:#D4E6F1,stroke:#5499C7

    style AgentLoop3 fill:#D4E6F1,stroke:#5499C7
    style Tooling fill:#FADBD8,stroke:#EC7063
    style Database fill:#EBDEF0,stroke:#9B59B6
```

## 2. Backend Design

### 2.1. Technology Stack
*   **Language:** Python 3.9+
*   **Web Framework:** FastAPI
*   **Asynchronous Primitives:** `asyncio` for the agent loops and message queue.
*   **Database:** PostgreSQL (production) / SQLite (local), using `SQLModel` as the ORM.
*   **Real-time:** `websockets` library integrated with FastAPI.

### 2.2. Agent Infrastructure
The core of the new design is the **Asynchronous Agent Loop**. The previous `GroupChat` and `Scheduler` models are deprecated.

*   **Agent Definition:** Agents are still defined as `autogen.ConversableAgent` instances, but they will be enhanced with a persistent to-do list and a long-running asynchronous task (`run_agent_loop`).
*   **The Agent Loop:** Each agent will run its own independent, asynchronous loop. This loop represents the agent's "consciousness." In each iteration, the agent will:
    1.  **Check for new messages:** Read from the central message queue.
    2.  **Update internal state:** Process new messages. A message might contain a new task, a reply to a question, or information that changes the priority of existing tasks on its to-do list.
    3.  **Consult To-Do List:** Look at its own task list (stored in the database) to decide what to do next. The highest-priority, unblocked task is chosen.
    4.  **Execute Task:** Perform the chosen task. This could be:
        *   **Using a tool:** Call a function like `web_search` or `write_to_file`.
        *   **Sending a message:** Formulate a reply or a new message and post it to the message queue for other agents to see.
        *   **Updating its to-do list:** Add, complete, or reprioritize its own tasks.
*   **Asynchronous Communication:**
    *   **Message Queue:** A central, in-memory `asyncio.Queue` will serve as the main communication bus. When an agent wants to send a message, it adds it to the queue.
    *   **Direct Addressing:** Messages will be addressed to a specific channel (e.g., `#engineering`) or another agent (e.g., `CeeCee_The_CEO`).
    *   **Broadcasting:** The backend will listen to this queue and broadcast relevant messages to the frontend via WebSockets.
*   **Tool Registration:** Tools will still be defined in `company/tools.py`. However, instead of being registered with an `Executor` agent, they will be made available to each agent to call directly from within their agent loop.

### 2.3. Database Schema
The schema needs to be updated to support agent autonomy.

*   `agents`: Stores static information about each agent (id, name, persona, role, system_prompt).
*   `conversations`: Represents a chat channel (id, name, e.g. `#general`, `#engineering`).
*   `messages`: Stores every message sent (id, conversation_id, agent_id, content, timestamp).
*   **`agent_tasks` (New):** This critical new table tracks each agent's to-do list.
    *   `id`: Primary key.
    *   `agent_id`: Foreign key to the `agents` table.
    *   `title`: A short description of the task.
    *   `description`: A more detailed description.
    *   `status`: `pending`, `in_progress`, `completed`, `blocked`.
    *   `priority`: An integer to help agents prioritize.
    *   `dependencies`: A list of other task IDs that must be completed first.

### 2.4. API Endpoints
The API will be updated to manage the new autonomous simulation.

*   `POST /simulation/start`: Kicks off the entire simulation, initializing the agents and starting their asynchronous loops.
*   `POST /simulation/stop`: Stops the simulation.
*   `GET /agents`: Get a list of all agents and their current status/active task.
*   `GET /agents/{agent_id}/tasks`: **New endpoint** to fetch the current to-do list for a specific agent.
*   `GET /conversations/{conv_id}/messages`: Get the message history for a specific conversation.
*   `WS /ws`: The WebSocket endpoint for pushing real-time updates (new messages, status changes, task list updates) to the client.

## 3. Frontend Design

### 3.1. Technology Stack
*   **Framework:** React (with Vite)
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS
*   **State Management:** Zustand.
*   **Data Fetching:** Axios or native `fetch` for API calls.

### 3.2. Component Architecture
The component architecture remains largely the same, with one key addition.

*   **`Layout.tsx`**: Main container.
*   **`Sidebar.tsx`**: Left panel with channel and agent lists.
*   **`ChatPane.tsx`**: Main content area for displaying conversations.
*   **`AgentProfile.tsx`**: A component to show details about an agent. This will be updated to include a new view:
    *   **`TodoList.tsx` (New):** A component that displays an agent's current to-do list, fetched from the new `/agents/{agent_id}/tasks` endpoint. It should show the task title, priority, and status.

### 3.3. State Management (Zustand)
The Zustand store will be updated to manage the new state.

*   **`conversations`**: A list of all channels.
*   **`messages`**: An object where keys are `conversation_id` and values are arrays of messages.
*   **`agents`**: A list of all agents and their metadata.
*   **`agentTasks` (New):** An object where keys are `agent_id` and values are arrays of tasks.
*   **`activeConversation`**: The ID of the currently viewed conversation.

The WebSocket connection will now handle updates for messages and agent task lists, dispatching actions to the store to keep the UI in sync.

## 4. Deployment & Infrastructure
The deployment strategy remains the same.
*   **Backend (FastAPI):** Containerized with Docker and deployed to a service like Google Cloud Run.
*   **Frontend (React):** Deployed as a static site to Vercel or Netlify.
*   **CI/CD:** A GitHub Actions workflow for automated testing and deployment.
*   **CORS:** Configured in the FastAPI backend to allow requests from the frontend domain. 