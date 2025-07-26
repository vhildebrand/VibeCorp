import React from 'react';
import { useAppStore } from '../store';

interface ActivityItem {
  id: string;
  type: 'task_created' | 'agent_status' | 'message' | 'background_activity';
  agent?: string;
  content: string;
  timestamp: string;
  icon: string;
}

const ActivityFeed: React.FC = () => {
  const { messages, agents, tasks } = useAppStore();
  
  // Generate activity feed from recent events
  const generateActivityFeed = (): ActivityItem[] => {
    const activities: ActivityItem[] = [];
    
    // Recent messages as activities
    const recentMessages = messages
      .slice(-10)
      .map(msg => {
        const agent = agents.find(a => a.id === msg.agentId);
        return {
          id: `msg-${msg.id}`,
          type: 'message' as const,
          agent: agent?.name,
          content: msg.content.length > 60 ? `${msg.content.substring(0, 60)}...` : msg.content,
          timestamp: msg.timestamp,
          icon: agent?.avatar || '💬'
        };
      });
    
    // Recent tasks as activities
    const recentTasks = tasks
      .slice(-5)
      .map(task => ({
        id: `task-${task.id}`,
        type: 'task_created' as const,
        content: `New task: ${task.title}`,
        timestamp: task.createdAt,
        icon: '🎯'
      }));
    
    // Agent status changes (mock for now)
    const statusUpdates = agents
      .filter(agent => agent.status !== 'idle')
      .map(agent => ({
        id: `status-${agent.id}`,
        type: 'agent_status' as const,
        agent: agent.name,
        content: `${agent.name.replace(/_/g, ' ')} is ${agent.status.replace(/_/g, ' ')}`,
        timestamp: new Date().toISOString(),
        icon: getStatusIcon(agent.status)
      }));
    
    activities.push(...recentMessages, ...recentTasks, ...statusUpdates);
    
    // Sort by timestamp (most recent first)
    return activities
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 15);
  };
  
  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'coding': return '💻';
      case 'in_meeting': return '🤝';
      case 'tweeting': return '📱';
      case 'researching': return '🔍';
      case 'debugging': return '🐛';
      case 'reviewing_metrics': return '📊';
      case 'strategic_planning': return '🎯';
      case 'content_creation': return '✍️';
      case 'social_media': return '📲';
      case 'interviewing': return '👥';
      default: return '⚡';
    }
  };
  
  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };
  
  const getActivityColor = (type: string): string => {
    switch (type) {
      case 'task_created': return 'text-blue-400';
      case 'agent_status': return 'text-green-400';
      case 'message': return 'text-gray-300';
      case 'background_activity': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };
  
  const activities = generateActivityFeed();
  
  return (
    <div className="h-full bg-gray-800 border-l border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <h2 className="text-lg font-semibold text-white">Live Activity</h2>
        </div>
        <p className="text-sm text-gray-400 mt-1">Real-time autonomous agent activities</p>
      </div>
      
      {/* Activity Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activities.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <div className="text-4xl mb-2">🤖</div>
            <p>Waiting for agent activities...</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start space-x-3 p-3 bg-gray-750 rounded-lg hover:bg-gray-700 transition-colors"
            >
              {/* Icon */}
              <div className="flex-shrink-0 text-lg">
                {activity.icon}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className={`text-sm font-medium ${getActivityColor(activity.type)}`}>
                    {activity.type.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(activity.timestamp)}
                  </span>
                </div>
                
                {activity.agent && (
                  <p className="text-xs text-gray-400 mb-1">
                    {activity.agent.replace(/_/g, ' ')}
                  </p>
                )}
                
                <p className="text-sm text-gray-300 leading-relaxed">
                  {activity.content}
                </p>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-700">
        <div className="text-xs text-gray-500 text-center">
          <div className="flex items-center justify-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span>Tasks</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Status</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-gray-300 rounded-full"></div>
              <span>Messages</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ActivityFeed; 