import React, { useEffect } from 'react';
import { useAppStore } from './store';
import Layout from './components/Layout';

function App() {
  const { loadInitialData, connectWebSocket, disconnectWebSocket, error } = useAppStore();

  useEffect(() => {
    // Load initial data when app starts
    loadInitialData();
    
    // Connect WebSocket for real-time updates
    connectWebSocket();
    
    // Cleanup WebSocket connection when app unmounts
    return () => {
      disconnectWebSocket();
    };
  }, [loadInitialData, connectWebSocket, disconnectWebSocket]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-white">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold mb-2">Connection Error</h1>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return <Layout />;
}

export default App;
