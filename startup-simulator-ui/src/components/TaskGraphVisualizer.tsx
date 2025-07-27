import React, { useState, useEffect } from 'react';
import { useAppStore } from '../store';

interface TaskNode {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: number;
  agent_id: number;
  agent_name: string;
  parent_id?: number;
  children: number[];
}

interface TaskGraph {
  agent_id: number;
  agent_name: string;
  nodes: TaskNode[];
  edges: Array<{ from: number; to: number; type: string }>;
}

const TaskGraphVisualizer: React.FC = () => {
  const { agents, selectedAgentId } = useAppStore();
  const [taskGraphs, setTaskGraphs] = useState<TaskGraph[]>([]);
  const [selectedAgentGraph, setSelectedAgentGraph] = useState<TaskGraph | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'all' | 'agent'>('all');

  const loadAllTaskGraphs = async () => {
    setLoading(true);
    setError(null);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/task-graph/all`);
      if (!response.ok) {
        throw new Error(`Failed to load task graphs: ${response.statusText}`);
      }
      const data: TaskGraph[] = await response.json();
      setTaskGraphs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task graphs');
    } finally {
      setLoading(false);
    }
  };

  const loadAgentTaskGraph = async (agentId: number) => {
    setLoading(true);
    setError(null);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/agents/${agentId}/task-graph`);
      if (!response.ok) {
        throw new Error(`Failed to load agent task graph: ${response.statusText}`);
      }
      const data: TaskGraph = await response.json();
      setSelectedAgentGraph(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent task graph');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending':
        return 'bg-gray-600 border-gray-500';
      case 'in_progress':
        return 'bg-blue-600 border-blue-500';
      case 'completed':
        return 'bg-green-600 border-green-500';
      case 'blocked':
        return 'bg-red-600 border-red-500';
      default:
        return 'bg-gray-600 border-gray-500';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'in_progress':
        return '🔄';
      case 'completed':
        return '✅';
      case 'blocked':
        return '🚫';
      default:
        return '❓';
    }
  };

  const getPriorityColor = (priority: number): string => {
    if (priority <= 1) return 'text-red-400';
    if (priority <= 3) return 'text-yellow-400';
    return 'text-green-400';
  };

  const renderTaskNode = (node: TaskNode, isRoot: boolean = false) => {
    return (
      <div
        key={node.id}
        className={`p-3 rounded-lg border-2 ${getStatusColor(node.status)} ${
          isRoot ? 'ring-2 ring-purple-500' : ''
        } transition-all hover:scale-105 cursor-pointer`}
        title={node.description}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg">{getStatusIcon(node.status)}</span>
          <span className={`text-xs font-bold ${getPriorityColor(node.priority)}`}>
            P{node.priority}
          </span>
        </div>
        <h4 className="text-sm font-semibold text-white mb-1 line-clamp-2">
          {node.title}
        </h4>
        <p className="text-xs text-gray-300 line-clamp-2 mb-2">
          {node.description}
        </p>
        <div className="text-xs text-gray-400">
          {node.agent_name}
        </div>
      </div>
    );
  };

  const renderTaskHierarchy = (nodes: TaskNode[], parentId: number | null = null, level: number = 0) => {
    const childNodes = nodes.filter(node => node.parent_id === parentId);
    
    if (childNodes.length === 0) return null;

    return (
      <div className={`${level > 0 ? 'ml-8 border-l-2 border-gray-600 pl-4' : ''}`}>
        {childNodes.map((node) => (
          <div key={node.id} className="mb-4">
            {renderTaskNode(node, level === 0)}
            {renderTaskHierarchy(nodes, node.id, level + 1)}
          </div>
        ))}
      </div>
    );
  };

  const renderAgentTaskGraph = (graph: TaskGraph) => {
    if (graph.nodes.length === 0) {
      return (
        <div className="text-center text-gray-400 py-8">
          <div className="text-4xl mb-4">📋</div>
          <p>No tasks found for {graph.agent_name}</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            {graph.agent_name} Tasks
          </h3>
          <div className="text-sm text-gray-400">
            {graph.nodes.length} task{graph.nodes.length !== 1 ? 's' : ''}
          </div>
        </div>
        
        {/* Task Statistics */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {['pending', 'in_progress', 'completed', 'blocked'].map(status => {
            const count = graph.nodes.filter(n => n.status === status).length;
            return (
              <div key={status} className={`p-2 rounded text-center ${getStatusColor(status)}`}>
                <div className="text-lg">{getStatusIcon(status)}</div>
                <div className="text-xs">{count}</div>
              </div>
            );
          })}
        </div>

        {/* Hierarchical Task View */}
        <div className="space-y-2">
          {renderTaskHierarchy(graph.nodes)}
        </div>
      </div>
    );
  };

  useEffect(() => {
    if (viewMode === 'all') {
      loadAllTaskGraphs();
    } else if (selectedAgentId) {
      loadAgentTaskGraph(selectedAgentId);
    }
  }, [viewMode, selectedAgentId]);

  return (
    <div className="h-full bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Task Graph Visualizer</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('all')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'all' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              All Agents
            </button>
            <button
              onClick={() => setViewMode('agent')}
              className={`px-3 py-1 rounded text-sm ${
                viewMode === 'agent' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
              disabled={!selectedAgentId}
            >
              Selected Agent
            </button>
            <button
              onClick={() => {
                if (viewMode === 'all') {
                  loadAllTaskGraphs();
                } else if (selectedAgentId) {
                  loadAgentTaskGraph(selectedAgentId);
                }
              }}
              className="p-2 rounded hover:bg-gray-700 text-gray-400 hover:text-white"
              title="Refresh"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="text-center text-gray-400 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2">Loading task graphs...</p>
          </div>
        )}

        {error && (
          <div className="p-4 text-red-400 bg-red-900/20 border border-red-800 rounded">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {viewMode === 'all' && (
              <div className="space-y-6">
                {taskGraphs.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    <div className="text-4xl mb-4">📊</div>
                    <p>No task graphs available</p>
                  </div>
                ) : (
                  taskGraphs.map((graph) => (
                    <div key={graph.agent_id} className="bg-gray-800 rounded-lg p-4">
                      {renderAgentTaskGraph(graph)}
                    </div>
                  ))
                )}
              </div>
            )}

            {viewMode === 'agent' && (
              <>
                {!selectedAgentId ? (
                  <div className="text-center text-gray-400 py-8">
                    <div className="text-4xl mb-4">👤</div>
                    <p>Select an agent to view their task graph</p>
                  </div>
                ) : selectedAgentGraph ? (
                  <div className="bg-gray-800 rounded-lg p-4">
                    {renderAgentTaskGraph(selectedAgentGraph)}
                  </div>
                ) : (
                  <div className="text-center text-gray-400 py-8">
                    <div className="text-4xl mb-4">📋</div>
                    <p>No task graph data available</p>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TaskGraphVisualizer; 