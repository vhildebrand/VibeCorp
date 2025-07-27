import React from 'react';
import { useAppStore, type Agent } from '../store';
import TodoList from './TodoList';

interface AgentProfileProps {
  agentId: number;
}

const AgentProfile: React.FC<AgentProfileProps> = ({ agentId }) => {
  const { agents, setSelectedAgent } = useAppStore();
  
  const agent = agents.find(a => a.id === agentId);
  
  if (!agent) {
    return (
      <div className="h-full bg-gray-800 border-l border-gray-700 p-6 text-center text-gray-400">
        <div className="text-4xl mb-2">🤖</div>
        <p>Agent not found</p>
      </div>
    );
  }

  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'idle': return 'bg-gray-500';
      case 'coding': return 'bg-red-500';
      case 'in_meeting': return 'bg-yellow-500';
      case 'tweeting': return 'bg-green-500';
      case 'researching': return 'bg-blue-500';
      case 'thinking': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  const formatAgentName = (name: string) => {
    return name.replace(/_/g, ' ');
  };

  return (
    <div className="h-full bg-gray-800 border-l border-gray-700 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 px-4 py-3 border-b border-gray-700 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <span className="text-2xl">{agent.avatar}</span>
              <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800 ${getStatusColor(agent.status)}`} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {formatAgentName(agent.name)}
              </h2>
              <p className="text-xs text-gray-400 capitalize">
                {agent.role} • {agent.status.replace(/_/g, ' ')}
              </p>
            </div>
          </div>
          
          <button
            onClick={() => setSelectedAgent(null)}
            className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            title="Close profile"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Agent Info */}
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-white mb-2">Status</h3>
          <div className="bg-gray-700 rounded-lg p-3 border border-gray-600">
            <div className="text-xs text-gray-300 space-y-1">
              <div>
                <span className="text-gray-400">Role:</span>
                <span className="text-white ml-2 font-medium">{agent.role}</span>
              </div>
              <div>
                <span className="text-gray-400">Status:</span>
                <span className={`ml-2 font-medium capitalize ${agent.color}`}>
                  {agent.status.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
            
            {agent.lastStatusUpdate && (
              <div className="mt-2 text-xs text-gray-500">
                Updated: {new Date(agent.lastStatusUpdate).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        {/* To-Do List */}
        <div className="flex-1">
          <TodoList agentId={agentId} className="h-full" />
        </div>
      </div>
    </div>
  );
};

export default AgentProfile; 