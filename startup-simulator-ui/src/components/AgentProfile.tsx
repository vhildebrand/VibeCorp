import React from 'react';
import { useAppStore, type Agent } from '../store';
import TodoList from './TodoList';

interface AgentProfileProps {
  agentId: number;
  onClose?: () => void;
}

const AgentProfile: React.FC<AgentProfileProps> = ({ agentId, onClose }) => {
  const { agents } = useAppStore();
  
  const agent = agents.find(a => a.id === agentId);
  
  if (!agent) {
    return (
      <div className="p-6 text-center text-gray-400">
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
    <div className="bg-gray-900 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <span className="text-3xl">{agent.avatar}</span>
              <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-800 ${getStatusColor(agent.status)}`} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                {formatAgentName(agent.name)}
              </h2>
              <p className="text-sm text-gray-400 capitalize">
                {agent.role} • {agent.status.replace(/_/g, ' ')}
              </p>
            </div>
          </div>
          
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              title="Close profile"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
        {/* Agent Info */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">About</h3>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <p className="text-sm text-gray-300 leading-relaxed">
              {agent.persona}
            </p>
            
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
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
                Last updated: {new Date(agent.lastStatusUpdate).toLocaleString()}
              </div>
            )}
          </div>
        </div>

        {/* To-Do List */}
        <div>
          <TodoList agentId={agentId} />
        </div>
      </div>
    </div>
  );
};

export default AgentProfile; 