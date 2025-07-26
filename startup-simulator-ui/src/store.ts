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

interface AppState {
  // State
  agents: Agent[];
  conversations: Conversation[];
  messages: Message[];
  tasks: Task[];
  activeConversationId: number | null;
  sidebarCollapsed: boolean;
  
  // Loading states
  loading: {
    agents: boolean;
    conversations: boolean;
    messages: boolean;
    tasks: boolean;
  };
  
  // Error states
  error: string | null;
  
  // WebSocket connection
  websocket: WebSocketService | null;
  connected: boolean;
  
  // Actions
  setActiveConversation: (id: number) => void;
  toggleSidebar: () => void;
  markConversationAsRead: (id: number) => void;
  addMessage: (message: Omit<Message, 'id'>) => void;
  updateAgentStatus: (agentId: number, status: Agent['status']) => void;
  
  // API actions
  loadInitialData: () => Promise<void>;
  loadConversationMessages: (conversationId: number) => Promise<void>;
  createTask: (title: string, description: string, conversationId?: number) => Promise<void>;
  
  // WebSocket actions
  connectWebSocket: () => Promise<void>;
  disconnectWebSocket: () => void;
}

// Mock data
const mockAgents: Agent[] = [
  {
    id: 1,
    name: 'CeeCee_The_CEO',
    role: 'CEO',
    persona: 'Overly enthusiastic, buzzword-loving CEO',
    status: 'in_meeting',
    avatar: '👩‍💼',
    color: 'text-blue-400'
  },
  {
    id: 2,
    name: 'Marty_The_Marketer',
    role: 'Marketer', 
    persona: 'Social media obsessed marketer',
    status: 'tweeting',
    avatar: '📱',
    color: 'text-green-400'
  },
  {
    id: 3,
    name: 'Penny_The_Programmer',
    role: 'Programmer',
    persona: 'Pragmatic, slightly sarcastic programmer',
    status: 'coding',
    avatar: '💻',
    color: 'text-red-400'
  },
  {
    id: 4,
    name: 'Herb_From_HR',
    role: 'HR',
    persona: 'Team-building obsessed HR representative',
    status: 'idle',
    avatar: '🤝',
    color: 'text-yellow-400'
  }
];

const mockConversations: Conversation[] = [
  {
    id: 1,
    name: '#general',
    type: 'group',
    description: 'Main company-wide discussion channel',
    members: [1, 2, 3, 4],
    lastMessageTime: '2025-01-26T16:45:00Z',
    unreadCount: 3
  },
  {
    id: 2,
    name: '#random',
    type: 'group',
    description: 'Off-topic discussions and water cooler chat',
    members: [1, 2, 3, 4],
    lastMessageTime: '2025-01-26T14:30:00Z',
    unreadCount: 0
  },
  {
    id: 3,
    name: '#brainstorming',
    type: 'group',
    description: 'Ideas and project planning',
    members: [1, 2, 3, 4],
    lastMessageTime: '2025-01-26T12:15:00Z',
    unreadCount: 1
  },
  {
    id: 4,
    name: 'CeeCee + Penny',
    type: 'dm',
    members: [1, 3],
    lastMessageTime: '2025-01-26T11:00:00Z',
    unreadCount: 0
  },
  {
    id: 5,
    name: 'Marty + Herb',
    type: 'dm',
    members: [2, 4],
    lastMessageTime: '2025-01-26T10:30:00Z',
    unreadCount: 2
  }
];

const mockMessages: Message[] = [
  // #general conversation
  {
    id: 1,
    conversationId: 1,
    agentId: 1,
    agentName: 'CeeCee_The_CEO',
    content: 'Good morning team! 🌟 We need to DISRUPT the market this quarter with some GAME-CHANGING, synergistic ideas that will leverage our core competencies and move the needle! Let\'s brainstorm something REVOLUTIONARY that will make us first to market! We need this yesterday! 🚀',
    timestamp: '2025-01-26T16:42:00Z',
    type: 'message'
  },
  {
    id: 2,
    conversationId: 1,
    agentId: 2,
    agentName: 'Marty_The_Marketer',
    content: 'OMG CeeCee! 🚀✨💯 YES! I\'m thinking viral TikTok campaign meets blockchain meets influencer partnerships! We could create a hashtag challenge that gamifies our user acquisition funnel! #DisruptiveVibes #InfluencerSynergy 🔥💥',
    timestamp: '2025-01-26T16:43:00Z',
    type: 'message'
  },
  {
    id: 3,
    conversationId: 1,
    agentId: 3,
    agentName: 'Penny_The_Programmer',
    content: 'LOG: Marketing proposals lack technical feasibility assessment. TikTok API integration requires 3-week development cycle. Blockchain implementation adds 8-week overhead to project timeline. Recommend focusing on deliverable features within current sprint capacity.',
    timestamp: '2025-01-26T16:44:00Z',
    type: 'message'
  },
  {
    id: 4,
    conversationId: 1,
    agentId: 4,
    agentName: 'Herb_From_HR',
    content: 'Team! 🌈 I love seeing this collaborative energy! Perhaps we should schedule a brainstorming retreat where we can do some trust-building exercises while ideating? I know a great place that does team lunches AND has a ropes course! Let\'s align our chakras and our KPIs! ✨🤝',
    timestamp: '2025-01-26T16:45:00Z',
    type: 'message'
  },
  
  // #random conversation
  {
    id: 5,
    conversationId: 2,
    agentId: 2,
    agentName: 'Marty_The_Marketer',
    content: 'Anyone else obsessed with this new productivity app? It\'s like Notion but for social media scheduling! 📱💻 #ProductivityHack',
    timestamp: '2025-01-26T14:30:00Z',
    type: 'message'
  },
  
  // DM between CeeCee and Penny
  {
    id: 6,
    conversationId: 4,
    agentId: 1,
    agentName: 'CeeCee_The_CEO',
    content: 'Penny, I need you to be real with me for a sec. Can we actually build what Marty is proposing? I know I get excited, but I trust your technical judgment.',
    timestamp: '2025-01-26T10:58:00Z',
    type: 'message'
  },
  {
    id: 7,
    conversationId: 4,
    agentId: 3,
    agentName: 'Penny_The_Programmer',
    content: 'LOG: Appreciate direct communication approach. Marty\'s viral TikTok blockchain proposal is technically ambitious but would require significant resource allocation. Recommend MVP approach focusing on core functionality first.',
    timestamp: '2025-01-26T11:00:00Z',
    type: 'message'
  }
];

const mockTasks: Task[] = [
  {
    id: 1,
    title: 'Implement viral TikTok integration',
    description: 'Create API integration for TikTok content sharing and engagement tracking',
    status: 'pending',
    assignedTo: [3],
    createdAt: '2025-01-26T16:45:00Z'
  },
  {
    id: 2,
    title: 'Plan team building retreat',
    description: 'Organize collaborative brainstorming session with trust-building activities',
    status: 'in_progress',
    assignedTo: [4],
    createdAt: '2025-01-26T16:46:00Z'
  }
];

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  agents: mockAgents,
  conversations: mockConversations,
  messages: mockMessages,
  tasks: mockTasks,
  activeConversationId: 1, // Start with #general selected
  sidebarCollapsed: false,
  
  // Loading states
  loading: {
    agents: false,
    conversations: false,
    messages: false,
    tasks: false,
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
  
  toggleSidebar: () => set((state) => ({ 
    sidebarCollapsed: !state.sidebarCollapsed 
  })),
  
  markConversationAsRead: (id: number) => set((state) => ({
    conversations: state.conversations.map(conv =>
      conv.id === id ? { ...conv, unreadCount: 0 } : conv
    )
  })),
  
  addMessage: (message: Omit<Message, 'id'>) => set((state) => {
    const newMessage: Message = {
      ...message,
      id: Math.max(...state.messages.map(m => m.id)) + 1
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
      agent.id === agentId ? { ...agent, status } : agent
    )
  })),
  
  // API actions
  loadInitialData: async () => {
    const state = get();
    
    set({ loading: { ...state.loading, agents: true, conversations: true, tasks: true }, error: null });
    
    try {
      // Load agents, conversations, and tasks in parallel
      const [agents, conversations, tasks] = await Promise.all([
        apiService.getAgents(),
        apiService.getConversations(),
        apiService.getTasks(),
      ]);
      
      // Update conversations with member information
      const updatedConversations = conversations.map(conv => ({
        ...conv,
        members: agents.map(agent => agent.id), // For now, all agents are in all conversations
      }));
      
      set({
        agents,
        conversations: updatedConversations,
        tasks,
        loading: { agents: false, conversations: false, messages: false, tasks: false },
        error: null,
      });
      
      // If we have conversations and no active one is set, set the first one
      if (updatedConversations.length > 0 && !state.activeConversationId) {
        get().setActiveConversation(updatedConversations[0].id);
      }
      
    } catch (error) {
      console.error('Error loading initial data:', error);
      set({
        loading: { agents: false, conversations: false, messages: false, tasks: false },
        error: error instanceof Error ? error.message : 'Failed to load data',
      });
    }
  },
  
  loadConversationMessages: async (conversationId: number) => {
    const state = get();
    
    set({ loading: { ...state.loading, messages: true }, error: null });
    
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
        loading: { ...state.loading, messages: false },
        error: null,
      });
      
    } catch (error) {
      console.error('Error loading conversation messages:', error);
      set({
        loading: { ...state.loading, messages: false },
        error: error instanceof Error ? error.message : 'Failed to load messages',
      });
    }
  },
  
  createTask: async (title: string, description: string, conversationId?: number) => {
    const state = get();
    
    set({ loading: { ...state.loading, tasks: true }, error: null });
    
    try {
      const newTask = await apiService.createTask(title, description, conversationId);
      
      set({
        tasks: [...state.tasks, newTask],
        loading: { ...state.loading, tasks: false },
        error: null,
      });
      
    } catch (error) {
      console.error('Error creating task:', error);
      set({
        loading: { ...state.loading, tasks: false },
        error: error instanceof Error ? error.message : 'Failed to create task',
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
            // Add new message to store
            currentState.addMessage({
              conversationId: message.data.conversationId,
              agentId: message.data.agentId,
              agentName: message.data.agentName,
              content: message.data.content,
              timestamp: message.data.timestamp,
              type: message.data.type || 'message',
            });
            break;
            
          case 'agent_status_update':
            // Update agent status
            currentState.updateAgentStatus(message.data.agentId, message.data.status);
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