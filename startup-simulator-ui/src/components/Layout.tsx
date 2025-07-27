import React from 'react';
import { useAppStore } from '../store';
import Sidebar from './Sidebar';
import ChatPane from './ChatPane';
import ActivityFeed from './ActivityFeed';
import AgentProfile from './AgentProfile';

const Layout: React.FC = () => {
  const { sidebarCollapsed, selectedAgentId } = useAppStore();

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Left Sidebar */}
      <div className={`transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      } flex-shrink-0`}>
        <Sidebar />
      </div>
      
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatPane />
      </div>
      
      {/* Right Panel - Agent Profile or Activity Feed */}
      <div className="w-80 flex-shrink-0 hidden lg:block">
        {selectedAgentId ? (
          <AgentProfile agentId={selectedAgentId} />
        ) : (
          <ActivityFeed />
        )}
      </div>
    </div>
  );
};

export default Layout; 