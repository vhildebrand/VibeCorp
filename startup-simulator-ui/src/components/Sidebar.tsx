// src/components/Sidebar.tsx
import React from 'react';
import { useAppStore } from '../store';
import ChannelList from './ChannelList';
import { 
  Crown, 
  Megaphone, 
  Code, 
  Shield, 
  Users, 
  ChevronLeft, 
  ChevronRight,
  Circle
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const { 
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

  const getAgentIcon = (name: string) => {
    switch (name) {
      case 'CeeCee_The_CEO':
        return Crown;
      case 'Marty_The_Marketer':
        return Megaphone;
      case 'Penny_The_Programmer':
        return Code;
      case 'Paige_The_Programmer':
        return Shield;
      case 'Herb_From_HR':
        return Users;
      default:
        return Circle;
    }
  };

  const getAgentColor = (name: string) => {
    switch (name) {
      case 'CeeCee_The_CEO':
        return 'text-blue-400';
      case 'Marty_The_Marketer':
        return 'text-green-400';
      case 'Penny_The_Programmer':
        return 'text-red-400';
      case 'Paige_The_Programmer':
        return 'text-purple-400';
      case 'Herb_From_HR':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
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
              {sidebarCollapsed ? (
                <ChevronRight className="w-5 h-5" />
              ) : (
                <ChevronLeft className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Agent Status Section */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-700">
            <h2 className="text-sm font-semibold text-gray-300 mb-3 uppercase tracking-wide">
              Team Members
            </h2>
            <div className="space-y-2">
              {agents.map((agent) => {
                const IconComponent = getAgentIcon(agent.name);
                const colorClass = getAgentColor(agent.name);
                
                return (
                  <button
                    key={agent.id}
                    onClick={() => handleAgentClick(agent.id)}
                    className={`w-full p-3 rounded-lg border transition-all duration-200 text-left ${
                      selectedAgentId === agent.id 
                        ? 'bg-blue-600 border-blue-500 ring-2 ring-blue-400' 
                        : 'bg-gray-700 border-gray-600 hover:bg-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-full bg-gray-600 ${colorClass}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-white truncate">
                              {agent.name.replace(/_/g, ' ')}
                            </p>
                            <p className="text-xs text-gray-300 truncate">
                              {agent.role}
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                        <span className="text-xs text-gray-400 capitalize">
                          {agent.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Collapsed Agent Status Section */}
        {sidebarCollapsed && (
          <div className="p-2 border-b border-gray-700">
            <div className="space-y-2">
              {agents.map((agent) => {
                const IconComponent = getAgentIcon(agent.name);
                const colorClass = getAgentColor(agent.name);
                
                return (
                  <button
                    key={agent.id}
                    onClick={() => handleAgentClick(agent.id)}
                    className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-200 relative bg-gray-700 hover:bg-gray-600 ${
                      selectedAgentId === agent.id 
                        ? 'ring-2 ring-blue-500 transform scale-110' 
                        : 'hover:transform hover:scale-105'
                    }`}
                    title={`${agent.name.replace(/_/g, ' ')} (${agent.role}) - ${agent.status}`}
                  >
                    <IconComponent className={`w-5 h-5 ${colorClass}`} />
                    <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-800 ${getStatusColor(agent.status)}`} />
                  </button>
                );
              })}
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
