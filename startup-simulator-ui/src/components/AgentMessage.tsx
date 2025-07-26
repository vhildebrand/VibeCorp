// src/components/AgentMessage.tsx
import React from 'react';
import { useAppStore } from '../store';
import type { Message } from '../store';

interface AgentMessageProps {
  message: Message;
  isGrouped?: boolean;
}

const AgentMessage: React.FC<AgentMessageProps> = ({ message, isGrouped = false }) => {
  const { agents } = useAppStore();
  
  const agent = agents.find(a => a.id === message.agentId);
  
  if (!agent) {
    return null;
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`group ${isGrouped ? 'mt-1' : 'mt-4'}`}>
      <div className="flex items-start space-x-3">
        {/* Avatar (only show if not grouped) */}
        {!isGrouped && (
          <div className="flex-shrink-0">
            <div className="w-10 h-10 rounded-lg bg-gray-200 flex items-center justify-center text-lg">
              {agent.avatar}
            </div>
          </div>
        )}
        
        {/* Message content */}
        <div className={`flex-1 min-w-0 ${isGrouped ? 'ml-13' : ''}`}>
          {/* Agent name and timestamp (only show if not grouped) */}
          {!isGrouped && (
            <div className="flex items-baseline space-x-2 mb-1">
              <span className={`font-semibold text-sm ${agent.color}`}>
                {agent.name.replace(/_/g, ' ')}
              </span>
              <span className="text-xs text-gray-500">
                {formatTimestamp(message.timestamp)}
              </span>
              <span className={`text-xs px-2 py-1 rounded-full ${
                agent.status === 'idle' ? 'bg-gray-100 text-gray-600' :
                agent.status === 'coding' ? 'bg-red-100 text-red-600' :
                agent.status === 'in_meeting' ? 'bg-yellow-100 text-yellow-600' :
                agent.status === 'tweeting' ? 'bg-green-100 text-green-600' :
                agent.status === 'researching' ? 'bg-blue-100 text-blue-600' :
                'bg-purple-100 text-purple-600'
              }`}>
                {agent.status.replace(/_/g, ' ')}
              </span>
            </div>
          )}
          
          {/* Message text */}
          <div className="text-gray-900 text-sm leading-relaxed">
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>
          </div>
          
          {/* Action indicators */}
          {message.type === 'action' && (
            <div className="mt-2 text-xs text-gray-500 italic">
              🔧 {agent.name} performed an action
            </div>
          )}
        </div>
        
        {/* Hover timestamp for grouped messages */}
        {isGrouped && (
          <div className="opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-400">
            {formatTimestamp(message.timestamp)}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentMessage;
