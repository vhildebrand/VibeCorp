import { create } from 'zustand';
import { apiService, WebSocketService } from './services/api';

// Types
export interface Agent {
  id: number;
  name: string;
  role: string;
  persona: string;
  status: 'idle' | 'thinking' | 'coding' | 'researching' | 'tweeting' | 'in_meeting';
  avatar: string;
  color: string;
  lastStatusUpdate?: string; // Timestamp of last status change
}

export interface Conversation {
  id: number;
  name: string;
  type: 'group' | 'dm';
  description?: string;
  members: number[];
  lastMessageTime: string;
  unreadCount: number;
}

export interface Message {
  id: number;
  conversationId: number;
  agentId: number;
  agentName: string;
  content: string;
  timestamp: string;
  type: 'message' | 'action';
}

export interface Task {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  assignedTo: number[];
  createdAt: string;
}

export interface AgentTask {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: number;
}

export interface AgentTaskList {
  agent_id: number;
  agent_name: string;
  tasks: AgentTask[];
}

interface AppState {
  // State
  agents: Agent[];
  conversations: Conversation[];
  messages: Message[];
  tasks: Task[];
  agentTasks: Record<number, AgentTask[]>; // agentId -> tasks
  activeConversationId: number | null;
  selectedAgentId: number | null; // For agent profile panel
  sidebarCollapsed: boolean;
  
  // Loading states
  loading: {
    agents: boolean;
    conversations: boolean;
    messages: boolean;
    tasks: boolean;
    agentTasks: boolean;
  };
  
  // Error states
  error: string | null;
  
  // WebSocket connection
  websocket: WebSocketService | null;
  connected: boolean;
  
  // Actions
  setActiveConversation: (id: number) => void;
  setSelectedAgent: (id: number | null) => void;
  toggleSidebar: () => void;
  markConversationAsRead: (id: number) => void;
  addMessage: (message: Omit<Message, 'id'>) => void;
  updateAgentStatus: (agentId: number, status: Agent['status']) => void;
  updateAgentTasks: (agentId: number, tasks: AgentTask[]) => void;
  
  // API actions
  loadInitialData: () => Promise<void>;
  loadConversationMessages: (conversationId: number) => Promise<void>;
  loadAgentTasks: (agentId: number) => Promise<void>;
  
  // WebSocket actions
  connectWebSocket: () => Promise<void>;
  disconnectWebSocket: () => void;
}

// Mock data for development - commented out to avoid TS warnings
/*
const mockAgents: Agent[] = [
  {
    id: 1,
    name: 'CeeCee_The_CEO',
    role: 'CEO',
    persona: 'A visionary leader who thinks big and makes bold decisions. Always pushing for innovation and growth.',
    status: 'idle',
    avatar: '👩‍💼',
    color: '#3B82F6'
  },
  {
    id: 2,
    name: 'Marty_The_Marketer',
    role: 'Marketer',
    persona: 'A creative and energetic marketer who loves crafting compelling campaigns and engaging with audiences.',
    status: 'tweeting',
    avatar: '📱',
    color: '#10B981'
  },
  {
    id: 3,
    name: 'Penny_The_Programmer',
    role: 'Programmer',
    persona: 'A skilled developer who loves solving complex problems and building elegant solutions.',
    status: 'coding',
    avatar: '💻',
    color: '#EF4444'
  },
  {
    id: 4,
    name: 'Herb_From_HR',
    role: 'HR',
    persona: 'An overly friendly HR representative who turns everything into a team-building exercise.',
    status: 'in_meeting',
    avatar: '🤝',
    color: '#F59E0B'
  }
];

const mockConversations: Conversation[] = [
  {
    id: 1,
    name: '#general',
    description: 'Main company-wide discussion channel',
    type: 'group',
    members: [1, 2, 3, 4]
  },
  {
    id: 2,
    name: '#random', 
    description: 'Off-topic discussions and fun conversations',
    type: 'group',
    members: [1, 2, 3, 4]
  },
  {
    id: 3,
    name: '#engineering',
    description: 'Technical discussions and code-related collaboration',
    type: 'group',
    members: [1, 3]
  }
];

const mockMessages: Message[] = [
  {
    id: 1,
    conversationId: 1,
    senderId: 1,
    senderName: 'CeeCee_The_CEO',
    content: 'Team, let\'s brainstorm some innovative product ideas for our startup!',
    timestamp: new Date('2024-01-15T09:00:00Z'),
    type: 'text'
  },
  {
    id: 2,
    conversationId: 1,
    senderId: 2,
    senderName: 'Marty_The_Marketer',
    content: 'I\'m thinking we could create a social media management platform with AI-powered content suggestions!',
    timestamp: new Date('2024-01-15T09:05:00Z'),
    type: 'text'
  },
  {
    id: 3,
    conversationId: 1,
    senderId: 3,
    senderName: 'Penny_The_Programmer',
    content: 'That sounds interesting! We could use machine learning to analyze engagement patterns and optimize posting times.',
    timestamp: new Date('2024-01-15T09:10:00Z'),
    type: 'text'
  },
  {
    id: 4,
    conversationId: 1,
    senderId: 4,
    senderName: 'Herb_From_HR',
    content: 'Great collaboration, team! This kind of synergy is exactly what we need. Maybe we should have a team-building retreat to further develop these ideas?',
    timestamp: new Date('2024-01-15T09:15:00Z'),
    type: 'text'
  },
  {
    id: 5,
    conversationId: 2,
    senderId: 2,
    senderName: 'Marty_The_Marketer',
    content: 'Just posted our latest tweet about innovation in the startup space! 🚀',
    timestamp: new Date('2024-01-15T10:30:00Z'),
    type: 'text'
  },
  {
    id: 6,
    conversationId: 3,
    senderId: 3,
    senderName: 'Penny_The_Programmer',
    content: 'I\'ve been working on the authentication system. Should have the MVP ready by end of week.',
    timestamp: new Date('2024-01-15T11:00:00Z'),
    type: 'text'
  },
  {
    id: 7,
    conversationId: 3,
    senderId: 1,  
    senderName: 'CeeCee_The_CEO',
    content: 'Excellent progress, Penny! Make sure to prioritize security best practices.',
    timestamp: new Date('2024-01-15T11:05:00Z'),
    type: 'text'
  }
];

const mockTasks: Task[] = [
  {
    id: 1,
    agentId: 1,
    title: 'Define company vision and strategy',
    description: 'Create a comprehensive business plan and define our core mission',
    status: 'in_progress',
    priority: 1,
    dueDate: new Date('2024-01-20T17:00:00Z'),
    assignedBy: 'System'
  },
  {
    id: 2,
    agentId: 2,
    title: 'Launch social media campaign',
    description: 'Create and execute a marketing campaign to build brand awareness',
    status: 'pending',
    priority: 2,
    dueDate: new Date('2024-01-18T12:00:00Z'),
    assignedBy: 'CeeCee_The_CEO'
  },
  {
    id: 3,
    agentId: 3,
    title: 'Build user authentication system',
    description: 'Implement secure login/logout functionality with proper session management',
    status: 'in_progress',
    priority: 1,
    dueDate: new Date('2024-01-17T18:00:00Z'),
    assignedBy: 'CeeCee_The_CEO'
  },
  {
    id: 4,
    agentId: 4,
    title: 'Organize team building event',
    description: 'Plan and coordinate a team building activity to improve collaboration',
    status: 'pending',
    priority: 3,
    dueDate: new Date('2024-01-25T15:00:00Z'),
    assignedBy: 'CeeCee_The_CEO'
  }
];
*/

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state - start with empty arrays, will be populated from API
  agents: [],
  conversations: [],
  messages: [],
  tasks: [],
  agentTasks: {}, // Initialize agentTasks as an empty object
  activeConversationId: null, // Will be set after conversations load
  selectedAgentId: null, // No agent profile shown initially
  sidebarCollapsed: false,
  
  // Loading states
  loading: {
    agents: false,
    conversations: false,
    messages: false,
    tasks: false,
    agentTasks: false,
  },
  
  // Error state
  error: null,
  
  // WebSocket connection
  websocket: null,
  connected: false,
  
  // Actions
  setActiveConversation: (id: number) => {
    set({ activeConversationId: id });
    // Mark conversation as read when opened
    get().markConversationAsRead(id);
    // Load messages for this conversation
    get().loadConversationMessages(id);
  },
  
  setSelectedAgent: (id: number | null) => {
    set({ selectedAgentId: id });
    // Load agent tasks when selecting an agent
    if (id) {
      get().loadAgentTasks(id);
    }
  },
  
  toggleSidebar: () => set((state) => ({ 
    sidebarCollapsed: !state.sidebarCollapsed 
  })),
  
  markConversationAsRead: (id: number) => set((state) => ({
    conversations: state.conversations.map(conv =>
      conv.id === id ? { ...conv, unreadCount: 0 } : conv
    )
  })),
  
  addMessage: (message: Omit<Message, 'id'>) => set((state) => {
    const existingIds = state.messages.map(m => m.id);
    const maxId = existingIds.length > 0 ? Math.max(...existingIds) : 0;
    const newMessage: Message = {
      ...message,
      id: maxId + 1
    };
    
    return {
      messages: [...state.messages, newMessage],
      conversations: state.conversations.map(conv =>
        conv.id === message.conversationId
          ? { 
              ...conv, 
              lastMessageTime: message.timestamp,
              unreadCount: conv.id === state.activeConversationId ? 0 : conv.unreadCount + 1
            }
          : conv
      )
    };
  }),
  
  updateAgentStatus: (agentId: number, status: Agent['status']) => set((state) => ({
    agents: state.agents.map(agent =>
      agent.id === agentId ? { 
        ...agent, 
        status, 
        lastStatusUpdate: new Date().toISOString() 
      } : agent
    )
  })),

  updateAgentTasks: (agentId: number, tasks: AgentTask[]) => set((state) => ({
    agentTasks: {
      ...state.agentTasks,
      [agentId]: tasks
    }
  })),
  
  // API actions
  loadInitialData: async () => {
    const state = get();
    
    set({ loading: { ...state.loading, agents: true, conversations: true, tasks: true, agentTasks: false }, error: null });
    
    try {
      // Load agents and conversations in parallel
      const [agents, conversations] = await Promise.all([
        apiService.getAgents(),
        apiService.getConversations(),
      ]);
      
      // Update conversations with member information
      const updatedConversations = conversations.map((conv: any) => ({
        ...conv,
        members: agents.map((agent: any) => agent.id), // For now, all agents are in all conversations
      }));
      
      set({
        agents,
        conversations: updatedConversations,
        loading: { agents: false, conversations: false, messages: false, tasks: false, agentTasks: false },
        error: null,
      });
      
      // If we have conversations and no active one is set, set the first one
      if (updatedConversations.length > 0 && state.activeConversationId === null) {
        get().setActiveConversation(updatedConversations[0].id);
      }
      
    } catch (error) {
      console.error('Error loading initial data:', error);
      set({
        loading: { agents: false, conversations: false, messages: false, tasks: false, agentTasks: false },
        error: error instanceof Error ? error.message : 'Failed to load data',
      });
    }
  },
  
  loadConversationMessages: async (conversationId: number) => {
    const state = get();
    
    set({ loading: { ...state.loading, messages: true, agentTasks: false }, error: null });
    
    try {
      const messages = await apiService.getConversationMessages(conversationId);
      
      // Update messages, replacing existing messages for this conversation
      const otherMessages = state.messages.filter(msg => msg.conversationId !== conversationId);
      const allMessages = [...otherMessages, ...messages];
      
      // Update conversation's last message time and unread count
      const updatedConversations = state.conversations.map(conv => {
        if (conv.id === conversationId) {
          const conversationMessages = messages.filter(msg => msg.conversationId === conversationId);
          const lastMessage = conversationMessages[conversationMessages.length - 1];
          return {
            ...conv,
            lastMessageTime: lastMessage ? lastMessage.timestamp : conv.lastMessageTime,
            unreadCount: 0, // Mark as read since user is viewing this conversation
          };
        }
        return conv;
      });
      
      set({
        messages: allMessages,
        conversations: updatedConversations,
        loading: { ...state.loading, messages: false, agentTasks: false },
        error: null,
      });
      
    } catch (error) {
      console.error('Error loading conversation messages:', error);
      set({
        loading: { ...state.loading, messages: false, agentTasks: false },
        error: error instanceof Error ? error.message : 'Failed to load messages',
      });
    }
  },

  loadAgentTasks: async (agentId: number) => {
    const state = get();
    set({ loading: { ...state.loading, agentTasks: true }, error: null });
    try {
      const data = await apiService.getAgentTasks(agentId);
      const tasks: AgentTask[] = (data.tasks || []).map(task => ({
        id: task.id,
        title: task.title,
        description: task.description,
        status: task.status as AgentTask['status'],
        priority: task.priority
      }));
      
      set({
        agentTasks: {
          ...state.agentTasks,
          [agentId]: tasks
        },
        loading: { ...state.loading, agentTasks: false },
        error: null
      });
    } catch (error) {
      console.error('Error loading agent tasks:', error);
      set({
        loading: { ...state.loading, agentTasks: false },
        error: error instanceof Error ? error.message : 'Failed to load agent tasks'
      });
    }
  },
  

  
  // WebSocket actions
  connectWebSocket: async () => {
    const state = get();
    
    if (state.websocket) {
      return; // Already connected
    }
    
    try {
      const ws = new WebSocketService();
      
      // Set up message handler
      ws.onMessage((message) => {
        const currentState = get();
        
        switch (message.type) {
          case 'new_message':
            // Add new message to store with proper ID from backend
            const messageData = message.data;
            const newMessage: Message = {
              id: messageData.id || Date.now(), // Use backend ID or fallback to timestamp
              conversationId: messageData.conversationId,
              agentId: messageData.agentId,
              agentName: messageData.agentName,
              content: messageData.content,
              timestamp: messageData.timestamp,
              type: messageData.type || 'message',
            };
            
            // Check if message already exists to prevent duplicates
            const existingMessage = currentState.messages.find(msg => msg.id === newMessage.id);
            if (existingMessage) {
              console.log('Duplicate message ignored:', newMessage.id);
              break;
            }
            
            // Additional check for content-based duplicates (in case IDs differ)
            const contentDuplicate = currentState.messages.find(msg => 
              msg.conversationId === newMessage.conversationId &&
              msg.agentId === newMessage.agentId &&
              msg.content === newMessage.content &&
              Math.abs(new Date(msg.timestamp).getTime() - new Date(newMessage.timestamp).getTime()) < 5000 // Within 5 seconds
            );
            if (contentDuplicate) {
              console.log('Content-based duplicate message ignored:', newMessage.content.substring(0, 50));
              break;
            }
            
            // Add directly to messages array and update conversation
            set((state) => ({
              messages: [...state.messages, newMessage],
              conversations: state.conversations.map(conv =>
                conv.id === newMessage.conversationId
                  ? { 
                      ...conv, 
                      lastMessageTime: newMessage.timestamp,
                      unreadCount: conv.id === state.activeConversationId ? 0 : conv.unreadCount + 1
                    }
                  : conv
              )
            }));
            break;
            
          case 'agent_status_update':
            // Update agent status
            currentState.updateAgentStatus(message.data.agentId, message.data.status);
            break;

          case 'agent_tasks_updated':
            // Update agent tasks
            const taskData = message.data;
            currentState.updateAgentTasks(taskData.agent_id, taskData.tasks);
            break;
            
          case 'agent_activity':
            // Handle agent activity updates (tool usage, etc.)
            console.log('Agent activity:', message.data);
            break;
            
          case 'task_update':
            // Reload tasks when there's an update
            currentState.loadInitialData();
            break;
            
          default:
            console.log('Unknown WebSocket message type:', message.type);
        }
      });
      
      await ws.connect();
      
      set({
        websocket: ws,
        connected: true,
      });
      
    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to connect to real-time updates',
      });
    }
  },
  
  disconnectWebSocket: () => {
    const state = get();
    
    if (state.websocket) {
      state.websocket.disconnect();
      set({
        websocket: null,
        connected: false,
      });
    }
  },
})); 