### **Sprint Plan: Autonomous Agent Overhaul**

**Goal:** Transform the agent system into a proactive, planning-based framework where agents demonstrate greater autonomy, intelligence, and collaborative behavior.

---

### **Epic 1: The "Planner Agent" - Upgrading Agent Intelligence**

*   **Objective:** Give agents the ability to create, manage, and execute complex, multi-step plans represented as task graphs.

*   **Tasks:**
    1.  **Backend: Implement Task Graph Model**
        *   **Why:** The current flat list of tasks with priorities is insufficient for complex plans. A graph structure allows for true dependencies and sub-tasks.
        *   **How:** We'll update the `AgentTask` model in `database/models.py` to support parent-child relationships, effectively creating a tree/graph structure for tasks. This will likely involve adding a `parent_id` and a `children` relationship.

    2.  **Agent Logic: Plan Execution and "Done-ness"**
        *   **Why:** Agents need the intelligence to navigate this new task graph and determine when a task is genuinely complete.
        *   **How:** We will refactor the agent's core decision-making loop (`decide_next_action`). Agents will learn to work on the "leaf nodes" of their task graph. We will also implement an internal "is this done?" check, where an agent evaluates its own work against the task description before marking it `COMPLETED`.

---

### **Epic 2: Enhanced Team Collaboration & Communication**

*   **Objective:** Make the agents more communicative and structured in their collaboration, ensuring the team runs efficiently.

*   **Tasks:**
    1.  **Agent Logic: Proactive Status Reporting**
        *   **Why:** A silent agent is an unhelpful one. Agents need to report their progress and blockers to the right team members.
        *   **How:** We'll enhance `decide_next_action` so that upon completing a task, an agent automatically sends a direct message to its superior. If an agent gets stuck, it will ask for help in the appropriate channel or from a specific teammate.

    2.  **Configuration: Reconfigure Agent Team & Roles**
        *   **Why:** The current team structure is limiting, and roles are not well-defined. The marketer shouldn't be writing code.
        *   **How:** We will:
            *   Add a second programmer to the team in `database/init_db.py`.
            *   Strictly define which tools each agent role can use within `agents/agents.py`. This will prevent the marketer from accessing coding tools and ensure programmers handle the development work.

---

### **Epic 3: UI & Observability Enhancements**

*   **Objective:** Provide you with a better window into the agents' minds and their work environment.

*   **Tasks:**
    1.  **Frontend: Task Graph Visualization**
        *   **Why:** A flat to-do list doesn't represent the complexity of the agents' plans.
        *   **How:** We'll update the API to serve the new task graph structure. The `TodoList.tsx` component will be overhauled to render this graph visually, showing parent tasks and their nested sub-tasks.

    2.  **Full Stack: Workspace File Browser**
        *   **Why:** You currently have no way to see the files the agents are creating in their workspace.
        *   **How:** We'll create a new, secure API endpoint to list directories and read files within the `workspace/` directory. On the client, a new `FileBrowser.tsx` component will be added, allowing you to navigate the agents' file system in real-time. 