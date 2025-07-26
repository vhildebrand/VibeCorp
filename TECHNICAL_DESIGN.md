# Technical Design Document: The AutoGen Startup Simulation

## 1. System Architecture

The system is composed of three main parts: a **Frontend** React application, a **Backend API** built with FastAPI, and the **Agent Service** powered by Microsoft AutoGen. Communication between the frontend and backend will happen via REST API calls and WebSockets for real-time updates.

```mermaid
graph TD
    User[<fa:fa-user> User] -->|Interacts with| Frontend[<fa:fa-desktop> Frontend<br/>(React, Vite, TailwindCSS)];
    
    subgraph "Cloud Infrastructure"
        Frontend -->|HTTP/REST API &<br/>WebSocket| BackendAPI[<fa:fa-server> Backend API<br/>(FastAPI, Uvicorn)];
        
        subgraph "Agent Core"
            BackendAPI -->|Initiates Tasks| AgentService[<fa:fa-robot> Agent Service<br/>(AutoGen)];
            AgentService -->|Executes Actions| Tooling[<fa:fa-tools> Tooling Layer<br/>(Python Functions)];
            Tooling -->|Interacts with| ExternalAPIs[<fa:fa-globe> External APIs<br/>(Web Search, etc.)];
            AgentService -->|Saves State| Database[<fa:fa-database> Database<br/>(PostgreSQL/SQLite)];
        end

        BackendAPI -->|Reads/Writes Data| Database;
    end

    style User fill:#D6EAF8,stroke:#5DADE2
    style Frontend fill:#D1F2EB,stroke:#48C9B0
    style BackendAPI fill:#FDEDEC,stroke:#F1948A
    style AgentService fill:#E8DAEF,stroke:#A569BD
    style Tooling fill:#FDEBD0,stroke:#F5B041
    style ExternalAPIs fill:#D4E6F1,stroke:#5499C7
    style Database fill:#FADBD8,stroke:#EC7063
```

## 2. Backend Design

### 2.1. Technology Stack
*   **Language:** Python 3.9+
*   **Web Framework:** FastAPI
*   **Agent Framework:** Microsoft AutoGen
*   **Database:** PostgreSQL (for production robustness) / SQLite (for easy local development). We will use an ORM like `SQLModel` or `SQLAlchemy` for data access.
*   **Real-time:** `websockets` library integrated with FastAPI.

### 2.2. Agent Infrastructure
*   **Agent Definition:** Agents will be defined as `autogen.ConversableAgent` instances in a dedicated module (e.g., `agents/agents.py`). Each agent will have a carefully crafted `system_message` to define its persona and capabilities.
*   **Executor Agent:** A `autogen.UserProxyAgent` named `Executor` will be responsible for executing tool calls and code blocks. It will not have a "personality" and will act as a neutral execution environment.
*   **Communication Model:**
    *   **Group Chats:** Core task collaboration will use `autogen.GroupChat`. A new `GroupChat` will be instantiated for each major task. The chat manager will handle the speaker selection transition.
    *   **1-on-1 & Channels:** To simulate Slack/Teams channels, we will build a layer on top of AutoGen. We'll manage multiple `GroupChat` instances: one for `#general`, one for each project, etc. 1-on-1 chats can be simulated by creating a `GroupChat` with only two agents. A routing function will direct agent messages to the correct "chat" based on the message content or context.
*   **Tool Registration:** Tools (Python functions) will be defined in `company/tools.py`. We will use AutoGen's `register_function` utility to map these functions to the agents. The `Executor` agent will be configured to execute these functions when proposed by other agents.

### 2.3. Database Schema
We will need several tables to persist the state of the simulation.

*   `agents`: Stores static information about each agent (id, name, persona, role).
*   `conversations` (Channels/DMs): Represents a chat channel or DM (id, name, type: `group` or `dm`).
*   `conversation_members`: Maps agents to the conversations they are part of.
*   `messages`: Stores every message sent (id, conversation_id, agent_id, content, timestamp, type: `message` or `action`).
*   `tasks`: High-level tasks assigned to the agent group (id, description, status: `pending`, `in_progress`, `completed`).

### 2.4. API Endpoints
The FastAPI application (`api/main.py`) will expose the following endpoints:

*   `POST /tasks`: Create a new high-level task for the agents to work on.
*   `GET /tasks`: List all current and past tasks.
*   `GET /conversations`: Get a list of all channels and DMs the user can view.
*   `GET /conversations/{conv_id}/messages`: Get the message history for a specific conversation.
*   `GET /agents`: Get a list of all agents and their current status.
*   `GET /agents/{agent_id}`: Get detailed information for a specific agent.
*   `WS /ws`: The WebSocket endpoint for pushing real-time updates (new messages, status changes) to the client.

## 3. Frontend Design

### 3.1. Technology Stack
*   **Framework:** React (with Vite)
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS
*   **State Management:** Zustand. It's a simple, unopinionated state management solution that is well-suited for handling real-time data from WebSockets without the boilerplate of Redux.
*   **Data Fetching:** Axios or native `fetch` for API calls.

### 3.2. Component Architecture
The UI will be broken down into the following key components in the `startup-simulator-ui/src/components/` directory:

*   **`Layout.tsx`**: The main container, establishing the Slack-like two-column layout.
*   **`Sidebar.tsx`**: The left panel, containing:
    *   `ChannelList.tsx`: Lists all public channels (`#general`, `#random`).
    *   `ProjectList.tsx`: Lists all active project group chats.
    *   `DirectMessageList.tsx`: Lists all 1-on-1 conversations between agents.
*   **`ChatPane.tsx`**: The main content area, which displays the selected conversation. It will contain:
    *   `ChatHeader.tsx`: Displays the name of the current channel/DM.
    *   `MessageList.tsx`: Renders the list of messages. It will be virtualized to handle very long conversations efficiently.
    *   `AgentMessage.tsx`: Renders a single message bubble with the agent's name, avatar, and the message content.
*   **`AgentProfile.tsx`**: A component to show details about an agent, perhaps in the right sidebar or a modal.
*   **`StatusBar.tsx`**: A global component to show the agent's current statuses.

### 3.3. State Management (Zustand)
We will create a central store to manage the application's state:

*   **`conversations`**: A list of all channels and DMs.
*   **`messages`**: An object where keys are `conversation_id` and values are arrays of messages.
*   **`agents`**: A list of all agents and their metadata (name, role, status).
*   **`activeConversation`**: The ID of the currently viewed conversation.

The WebSocket connection will dispatch actions to this store to update the state in real-time.

## 4. Deployment & Infrastructure
*   **Backend (FastAPI):**
    *   **Containerization:** The application will be containerized using Docker.
    *   **Deployment:** Deployed as a container to a service like Google Cloud Run or AWS Fargate for easy scaling.
*   **Frontend (React):**
    *   **Deployment:** The static site will be built and deployed to a service like Vercel or Netlify.
*   **CI/CD:** A GitHub Actions workflow will be set up to:
    *   Run tests and linting on every push.
    *   Automatically build and deploy the frontend and backend when changes are pushed to the `main` branch.

*   **CORS:** The FastAPI backend will be configured with CORS (Cross-Origin Resource Sharing) middleware to allow requests from the deployed frontend's domain. 