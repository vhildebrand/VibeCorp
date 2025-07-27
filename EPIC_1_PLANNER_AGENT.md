# Epic 1: The "Planner Agent" - Upgrading Agent Intelligence

**Objective:** Evolve agents from simple task-doers into proactive planners. This involves replacing the flat to-do list with a dynamic task graph that agents can build and traverse, enabling them to handle complex, multi-step goals autonomously.

---

### **Sprint Breakdown**

#### **Task 1.1: Backend - Implement Task Graph Model**

*   **Goal:** Update the database schema to support hierarchical tasks, forming the foundation of the planning system.
*   **Implementation Details:**
    1.  **Modify `AgentTask` Model (`database/models.py`):**
        *   Add a self-referencing foreign key to enable parent-child relationships.
            *   `parent_id: Optional[int] = Field(default=None, foreign_key="agent_tasks.id")`
        *   Define the SQLAlchemy relationships for `parent` and `children`.
            *   `parent: Optional["AgentTask"] = Relationship(back_populates="children", ...)`
            *   `children: List["AgentTask"] = Relationship(back_populates="parent")`
    2.  **Update Database Initialization (`database/init_db.py`):**
        *   Ensure that the `init_database()` script correctly drops and recreates the tables with the new schema. Per development best practices, we will rely on re-initializing the database rather than creating a migration for this change.
*   **Acceptance Criteria:**
    *   The database schema is successfully updated to include the parent-child task relationship.
    *   The application starts without database errors.
    *   It is manually verifiable that a task can be created with a `parent_id` pointing to another task.

---

#### **Task 1.2: Agent Logic - Plan Creation and Execution**

*   **Goal:** Grant agents the intelligence to create their own plans (task sub-trees) and execute them logically.
*   **Implementation Details:**
    1.  **Create New `planning` Tool (`company/tools.py`):**
        *   Implement a `create_sub_tasks` tool. This function will take a `parent_task_id` and a list of dictionaries (each with `title`, `description`) to create new `AgentTask` records linked to the parent.
    2.  **Refactor `decide_next_action` (`agents/agent_manager.py`):**
        *   The agent's decision logic will be updated to prioritize executing "leaf" tasks (i.e., tasks with no pending children).
        *   Introduce a new "planning step" into the agent's loop. If a task is high-level and has no children, the agent should first call `create_sub_tasks` to break it down.
    3.  **Implement "Sense of Done-ness":**
        *   Instead of auto-completing tasks after using a tool, the agent will make a more explicit decision.
        *   After performing an action related to a task, the agent will re-evaluate. It will ask itself, "Based on the task description, is the work complete?"
        *   Only if the agent reasons that the work is complete will it call the `complete_task` tool on itself. This removes rigid, timer-based logic and gives the agent true autonomy over its workflow.
*   **Acceptance Criteria:**
    *   An agent, when assigned a complex task like "Build a feature," first creates a series of sub-tasks (e.g., "design schema," "write API," "create frontend component").
    *   The agent completes the sub-tasks in a logical order.
    *   The parent task is only marked complete after all its children are complete.
    *   The process is observable through logs and agent communications.

---
### **Potential Challenges**

*   **SQLAlchemy Self-Referencing:** The self-referencing relationship in SQLModel/SQLAlchemy can be tricky. Careful attention must be paid to the `sa_relationship_kwargs` to avoid errors.
*   **Recursive Logic:** Both the agent's decision-making and the API's data fetching will involve recursion, which can be complex to debug.
*   **Emergent Dysfunctional Loops:** Granting agents the ability to create their own plans may lead to unforeseen looping behaviors (e.g., planning indefinitely without executing). Initial versions will require careful monitoring. 