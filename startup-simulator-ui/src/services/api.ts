import axios from 'axios';
import type { Agent, Conversation, Message } from '../store';

// API base URL - use environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// API response types
interface ApiAgent {
  id: number;
  name: string;
  role: string;
  persona: string;
  status: string;
}

interface ApiConversation {
  id: number;
  name: string;
  description?: string;
}

interface ApiMessage {
  id: number;
  conversation_id: number;
  agent_id: number;
  agent_name: string;
  content: string;
  timestamp: string;
}

interface ApiAgentTask {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: number;
}

interface ApiAgentTasksResponse {
  agent_id: number;
  agent_name: string;
  tasks: ApiAgentTask[];
}

// Helper function to transform API agent to frontend agent
const transformAgent = (apiAgent: ApiAgent): Agent => ({
  id: apiAgent.id,
  name: apiAgent.name,
  role: apiAgent.role,
  persona: apiAgent.persona,
  status: apiAgent.status as Agent['status'],
  avatar: '', // No longer using emoji avatars
  color: getAgentColor(apiAgent.name),
});

// Helper function to get agent color
const getAgentColor = (name: string): string => {
  switch (name) {
    case 'CeeCee_The_CEO':
      return 'text-blue-400';
    case 'Marty_The_Marketer':
      return 'text-green-400';
    case 'Penny_The_Programmer':
      return 'text-red-400';
    case 'Paige_The_Programmer':
      return 'text-purple-400'; // Security-focused programmer
    case 'Herb_From_HR':
      return 'text-yellow-400';
    default:
      return 'text-gray-400';
  }
};

// Helper function to transform API conversation to frontend conversation
const transformConversation = (apiConversation: ApiConversation): Conversation => ({
  id: apiConversation.id,
  name: apiConversation.name,
  type: 'group', // All conversations are group channels now
  description: apiConversation.description,
  members: [], // Will be populated separately
  lastMessageTime: new Date().toISOString(), // Default to current time
  unreadCount: 0, // Will be calculated based on messages
});

// Helper function to transform API message to frontend message
const transformMessage = (apiMessage: ApiMessage): Message => ({
  id: apiMessage.id,
  conversationId: apiMessage.conversation_id,
  agentId: apiMessage.agent_id,
  agentName: apiMessage.agent_name,
  content: apiMessage.content,
  timestamp: apiMessage.timestamp,
  type: 'message', // All messages are type 'message' now
});

// API service functions
export const apiService = {
  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Get all agents
  async getAgents(): Promise<Agent[]> {
    const response = await apiClient.get<ApiAgent[]>('/agents');
    return response.data.map(transformAgent);
  },

  // Get all conversations
  async getConversations(): Promise<Conversation[]> {
    const response = await apiClient.get<ApiConversation[]>('/conversations');
    return response.data.map(transformConversation);
  },

  // Get messages for a specific conversation
  async getConversationMessages(conversationId: number, limit = 100): Promise<Message[]> {
    const response = await apiClient.get<ApiMessage[]>(
      `/conversations/${conversationId}/messages?limit=${limit}`
    );
    return response.data.reverse().map(transformMessage); // Reverse to get chronological order
  },

  // Get tasks for a specific agent
  async getAgentTasks(agentId: number): Promise<ApiAgentTasksResponse> {
    const response = await apiClient.get<ApiAgentTasksResponse>(`/agents/${agentId}/tasks`);
    return response.data;
  },
};

// WebSocket service
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private maxReconnectAttempts: number = 5;
  private reconnectAttempts: number = 0;
  private messageHandlers: ((message: any) => void)[] = [];
  private url: string;

  constructor(url?: string) {
    this.url = url || (import.meta.env.VITE_WS_URL as string) || 'ws://localhost:8000/ws';
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(message));
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  onMessage(handler: (message: any) => void): void {
    this.messageHandlers.push(handler);
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Note: Using named exports to avoid TypeScript configuration issues 