// src/components/Sidebar.tsx
import React from 'react';
import { useAppStore } from '../store';
import ChannelList from './ChannelList';

const Sidebar: React.FC = () => {
  const { agents, sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
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
              <div key={agent.id} className="flex items-center space-x-3 p-2 rounded hover:bg-gray-700 transition-colors">
                <div className="relative">
                  <span className="text-lg">{agent.avatar}</span>
                  <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800 ${
                    agent.status === 'idle' ? 'bg-gray-500' :
                    agent.status === 'coding' ? 'bg-red-500' :
                    agent.status === 'in_meeting' ? 'bg-yellow-500' :
                    agent.status === 'tweeting' ? 'bg-green-500' :
                    agent.status === 'researching' ? 'bg-blue-500' :
                    'bg-purple-500'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${agent.color} truncate`}>
                    {agent.name.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-gray-400 capitalize">
                    {agent.status.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Channel and DM Lists */}
      <div className="flex-1 overflow-y-auto">
        <ChannelList />
      </div>
    </div>
  );
};

export default Sidebar;
