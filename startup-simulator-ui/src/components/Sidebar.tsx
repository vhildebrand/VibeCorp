// src/components/Sidebar.tsx
import React, { useState } from 'react';
import { useAppStore } from '../store';
import ChannelList from './ChannelList';
import AgentProfile from './AgentProfile';

const Sidebar: React.FC = () => {
  const { 
    conversations, 
    agents, 
    sidebarCollapsed, 
    toggleSidebar,
    selectedAgentId,
    setSelectedAgent
  } = useAppStore();
  
  const handleAgentClick = (agentId: number) => {
    // Toggle agent profile panel
    if (selectedAgentId === agentId) {
      setSelectedAgent(null); // Close if same agent clicked
    } else {
      setSelectedAgent(agentId); // Open agent profile
    }
  };

  const handleCloseProfile = () => {
    setSelectedAgent(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle':
        return 'bg-gray-500';
      case 'coding':
        return 'bg-red-500';
      case 'in_meeting':
        return 'bg-yellow-500';
      case 'tweeting':
        return 'bg-green-500';
      case 'researching':
        return 'bg-blue-500';
      default:
        return 'bg-purple-500';
    }
  };

  return (
    <>
      <div className="h-full bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-lg font-bold text-white">VibeCorp</h1>
                <p className="text-sm text-gray-400">AI Startup Simulation</p>
              </div>
            )}
            <button
              onClick={toggleSidebar}
              className="p-1 rounded hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
              title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d={sidebarCollapsed ? "M13 5l7 7-7 7M5 5l7 7-7 7" : "M11 19l-7-7 7-7m8 14l-7-7 7-7"} />
              </svg>
            </button>
          </div>
        </div>

        {/* Agent Status Section */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
              Agents
            </h2>
            <div className="space-y-2">
              {agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => handleAgentClick(agent.id)}
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-200 ${
                    selectedAgentId === agent.id 
                      ? 'ring-2 ring-blue-500 transform scale-110' 
                      : 'hover:transform hover:scale-105'
                  } ${getStatusColor(agent.status)}`}
                  title={`${agent.name.replace(/_/g, ' ')} (${agent.role}) - ${agent.status}`}
                >
                  {agent.avatar}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Channel and DM Lists */}
        <div className="flex-1 overflow-y-auto">
          <ChannelList />
        </div>
      </div>
    </>
  );
};

export default Sidebar;
