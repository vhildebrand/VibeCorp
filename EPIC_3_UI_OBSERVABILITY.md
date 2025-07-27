# Epic 3: UI & Observability Enhancements

**Objective:** Provide a clear, intuitive window into the agents' activities and work environment. This involves visualizing the new task graph structure and enabling direct browsing of the agent workspace.

---

### **Sprint Breakdown**

#### **Task 3.1: Full Stack - Workspace File Browser**

*   **Goal:** Allow users to browse the `workspace/` directory directly from the web client, providing transparency into the files agents are creating.
*   **Implementation Details:**
    1.  **Backend - Create File System API (`api/main.py`):**
        *   Add a new FastAPI router for file system operations.
        *   Implement a `GET /files/browse` endpoint that takes a `path` query parameter.
        *   This endpoint will securely list the contents of the requested directory within the `workspace/` root. It must prevent path traversal attacks (e.g., using `..`).
        *   Implement a `GET /files/read` endpoint that takes a `file_path` query parameter and returns the content of the specified file.
    2.  **Frontend - Build `FileBrowser` Component (`startup-simulator-ui/src/components/`):**
        *   Create a new React component, `FileBrowser.tsx`.
        *   This component will make API calls to the new `/files/` endpoints.
        *   It will render a list of files and folders, allowing for navigation through the directory tree.
        *   Clicking a folder will re-call the browse endpoint with the new path.
        *   Clicking a file will fetch its content and display it in a modal or a separate pane.
    3.  **Integrate Component into Layout (`startup-simulator-ui/src/components/Layout.tsx`):**
        *   Add the new `FileBrowser` component to the main application layout, likely as a new tab or a collapsible sidebar panel.
*   **Acceptance Criteria:**
    *   The UI displays a file browser that shows the contents of the `workspace/` directory.
    *   Users can click through folders to navigate the file system.
    *   Users can click on a file to view its contents.
    *   The API endpoints correctly prevent access to files outside the `workspace/` directory.

---

#### **Task 3.2: Full Stack - Task Graph Visualization**

*   **Goal:** Replace the flat to-do list in the UI with a hierarchical view that accurately represents the agents' task graphs.
*   **Implementation Details:**
    1.  **Backend - Update `get_tasks` API (`api/main.py`):**
        *   The existing endpoint for fetching tasks will be modified to return a nested JSON structure that reflects the parent-child relationships.
        *   This will likely involve a recursive function that builds the task tree starting from root tasks (those with no `parent_id`).
    2.  **Frontend - Refactor `TodoList.tsx` (`startup-simulator-ui/src/components/`):**
        *   The component will be updated to handle the new nested data structure.
        *   It will use a recursive rendering function to display tasks and their children in an indented, tree-like format.
        *   Each task item will still display its title, status, and description, but its position in the hierarchy will be clear.
        *   CSS will be updated to support the visual nesting of sub-tasks.
*   **Acceptance Criteria:**
    *   The to-do list in the client UI now renders as a tree.
    *   Sub-tasks are visually nested under their parent tasks.
    *   The status of each task is still visible.
    *   The UI correctly updates in real-time as agents create and complete tasks in the graph.

---
### **Potential Challenges**

*   **API Security:** The file browsing endpoint must be hardened against security vulnerabilities, particularly path traversal. All file paths must be validated to ensure they resolve to a location within the intended `workspace/` directory.
*   **Frontend Performance:** Rendering a very deep or wide task graph could lead to performance issues in the browser. The recursive rendering component must be optimized, potentially with virtualization for very large graphs.
*   **Real-time Synchronization:** Ensuring the client-side task graph and file browser update correctly and efficiently in real-time as agents make changes will require careful WebSocket event handling. 