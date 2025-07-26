import React from 'react';
import { useAppStore } from '../store';
import Sidebar from './Sidebar';
import ChatPane from './ChatPane';

const Layout: React.FC = () => {
  const sidebarCollapsed = useAppStore((state) => state.sidebarCollapsed);

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Sidebar */}
      <div className={`transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      } flex-shrink-0`}>
        <Sidebar />
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <ChatPane />
      </div>
    </div>
  );
};

export default Layout; 