import React, { useState } from 'react';
import { useAppStore } from '../store';
import Sidebar from './Sidebar';
import ChatPane from './ChatPane';
import ActivityFeed from './ActivityFeed';
import AgentProfile from './AgentProfile';
import WorkspaceBrowser from './WorkspaceBrowser';
import TaskGraphVisualizer from './TaskGraphVisualizer';
import { MessageCircle, FolderOpen, GitBranch } from 'lucide-react';

type MainViewType = 'chat' | 'workspace' | 'tasks';

const Layout: React.FC = () => {
  const { sidebarCollapsed, selectedAgentId } = useAppStore();
  const [mainView, setMainView] = useState<MainViewType>('chat');

  const renderMainContent = () => {
    switch (mainView) {
      case 'chat':
        return <ChatPane />;
      case 'workspace':
        return <WorkspaceBrowser />;
      case 'tasks':
        return <TaskGraphVisualizer />;
      default:
        return <ChatPane />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Left Sidebar */}
      <div className={`transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      } flex-shrink-0`}>
        <Sidebar />
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Tab Bar */}
        <div className="bg-gray-800 border-b border-gray-700 px-4">
          <div className="flex space-x-1">
            <button
              onClick={() => setMainView('chat')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                mainView === 'chat'
                  ? 'bg-gray-900 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <span className="flex items-center">
                <MessageCircle className="w-4 h-4 mr-2" />
                Chat
              </span>
            </button>
            <button
              onClick={() => setMainView('workspace')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                mainView === 'workspace'
                  ? 'bg-gray-900 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <span className="flex items-center">
                <FolderOpen className="w-4 h-4 mr-2" />
                Workspace
              </span>
            </button>
            <button
              onClick={() => setMainView('tasks')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                mainView === 'tasks'
                  ? 'bg-gray-900 text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <span className="flex items-center">
                <GitBranch className="w-4 h-4 mr-2" />
                Tasks
              </span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 min-h-0">
          {renderMainContent()}
        </div>
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