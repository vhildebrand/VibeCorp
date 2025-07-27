import React, { useState } from 'react';
import { useAppStore } from '../store';
import Sidebar from './Sidebar';
import ChatPane from './ChatPane';
import ActivityFeed from './ActivityFeed';
import AgentProfile from './AgentProfile';
import WorkspaceBrowser from './WorkspaceBrowser';
import TaskGraphVisualizer from './TaskGraphVisualizer';

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
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
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
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 1v6" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 1v6" />
                </svg>
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
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
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