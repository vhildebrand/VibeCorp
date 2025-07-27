import React, { useEffect } from 'react';
import { useAppStore, type AgentTask } from '../store';

interface TodoListProps {
  agentId: number;
  className?: string;
}

const TodoList: React.FC<TodoListProps> = ({ agentId, className = '' }) => {
  const { agentTasks, loading, loadAgentTasks, agents } = useAppStore();
  
  const agent = agents.find(a => a.id === agentId);
  const tasks = agentTasks[agentId] || [];
  
  useEffect(() => {
    // Load tasks when component mounts or agentId changes
    if (agentId) {
      loadAgentTasks(agentId);
    }
  }, [agentId, loadAgentTasks]);

  const getStatusIcon = (status: AgentTask['status']) => {
    switch (status) {
      case 'pending':
        return '📌';
      case 'in_progress':
        return '⏳';
      case 'completed':
        return '✅';
      case 'blocked':
        return '🚫';
      default:
        return '📌';
    }
  };

  const getStatusColor = (status: AgentTask['status']) => {
    switch (status) {
      case 'pending':
        return 'text-gray-400';
      case 'in_progress':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'blocked':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getPriorityColor = (priority: number) => {
    if (priority <= 3) return 'text-red-400'; // High priority
    if (priority <= 7) return 'text-yellow-400'; // Medium priority
    return 'text-green-400'; // Low priority
  };

  if (loading.agentTasks) {
    return (
      <div className={`space-y-3 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-600 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-600 rounded flex-1 animate-pulse"></div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-600 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-600 rounded flex-1 animate-pulse"></div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-600 rounded animate-pulse"></div>
          <div className="h-4 bg-gray-600 rounded flex-1 animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-400 ${className}`}>
        <div className="text-4xl mb-2">🎉</div>
        <p className="text-sm">
          {agent?.name.replace('_', ' ')} has no pending tasks!
        </p>
        <p className="text-xs text-gray-500 mt-1">
          All caught up for now.
        </p>
      </div>
    );
  }

  // Separate tasks by status for better organization
  const pendingTasks = tasks.filter(t => t.status === 'pending');
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress');
  const completedTasks = tasks.filter(t => t.status === 'completed');
  const blockedTasks = tasks.filter(t => t.status === 'blocked');

  const renderTaskSection = (title: string, tasks: AgentTask[]) => {
    if (tasks.length === 0) return null;

    return (
      <div className="mb-4">
        <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
          {title} ({tasks.length})
        </h4>
        <div className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="bg-gray-800 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start space-x-3">
                <span className="text-lg flex-shrink-0 mt-0.5">
                  {getStatusIcon(task.status)}
                </span>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <h5 className="text-sm font-medium text-white truncate">
                      {task.title}
                    </h5>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${getPriorityColor(task.priority)}`}>
                      P{task.priority}
                    </span>
                  </div>
                  
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {task.description}
                  </p>
                  
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs font-medium ${getStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">
                      ID: {task.id}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <span className="text-lg">{agent?.avatar || '🤖'}</span>
        <h3 className="text-lg font-semibold text-white">
          {agent?.name.replace('_', ' ') || 'Agent'}'s To-Do List
        </h3>
        <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
          {tasks.length} tasks
        </span>
      </div>

      <div className="max-h-96 overflow-y-auto space-y-4 pr-2">
        {renderTaskSection('In Progress', inProgressTasks)}
        {renderTaskSection('Pending', pendingTasks)}
        {renderTaskSection('Blocked', blockedTasks)}
        {renderTaskSection('Completed', completedTasks)}
      </div>
    </div>
  );
};

export default TodoList; 