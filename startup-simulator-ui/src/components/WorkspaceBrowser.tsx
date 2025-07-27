import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  Folder, 
  File, 
  FileText, 
  FileCode, 
  FileJson, 
  FileImage,
  ArrowUp,
  Loader2
} from 'lucide-react';

interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

interface DirectoryListing {
  path: string;
  items: FileItem[];
}

interface FileContent {
  path: string;
  name: string;
  size: number;
  modified: string;
  type: 'text' | 'binary';
  content?: string;
  message?: string;
}

const WorkspaceBrowser: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [directoryListing, setDirectoryListing] = useState<DirectoryListing | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadDirectory = async (path: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/workspace/browse?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error(`Failed to load directory: ${response.statusText}`);
      }
      const data: DirectoryListing = await response.json();
      setDirectoryListing(data);
      setCurrentPath(path);
      setSelectedFile(null); // Clear selected file when changing directory
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  const loadFile = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';  
      const response = await fetch(`${API_BASE_URL}/workspace/file?path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error(`Failed to load file: ${response.statusText}`);
      }
      const data: FileContent = await response.json();
      setSelectedFile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file');
    } finally {
      setLoading(false);
    }
  };

  const navigateToDirectory = (path: string) => {
    loadDirectory(path);
  };

  const navigateUp = () => {
    if (currentPath) {
      const parentPath = currentPath.split('/').slice(0, -1).join('/');
      loadDirectory(parentPath);
    }
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (timestamp?: string): string => {
    if (!timestamp) return '';
    const date = new Date(parseInt(timestamp) * 1000);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getFileIcon = (item: FileItem) => {
    if (item.type === 'directory') return Folder;
    
    const extension = item.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
      case 'py':
        return FileCode;
      case 'json':
        return FileJson;
      case 'md':
      case 'txt':
      case 'log':
        return FileText;
      case 'png':
      case 'jpg':
      case 'jpeg':
      case 'gif':
      case 'svg':
        return FileImage;
      default:
        return File;
    }
  };

  useEffect(() => {
    loadDirectory('');
  }, []);

  return (
    <div className="h-full bg-gray-900 text-white flex">
      {/* File Browser Panel */}
      <div className="w-1/2 border-r border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Workspace Browser</h2>
            <button
              onClick={() => loadDirectory(currentPath)}
              className="p-2 rounded hover:bg-gray-700 text-gray-400 hover:text-white"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          
          {/* Breadcrumb */}
          <div className="mt-2 text-sm text-gray-400">
            <button
              onClick={() => loadDirectory('')}
              className="hover:text-white"
            >
              workspace
            </button>
            {currentPath && currentPath.split('/').map((segment, index, array) => {
              const pathToSegment = array.slice(0, index + 1).join('/');
              return (
                <span key={index}>
                  <span className="mx-1">/</span>
                  <button
                    onClick={() => loadDirectory(pathToSegment)}
                    className="hover:text-white"
                  >
                    {segment}
                  </button>
                </span>
              );
            })}
          </div>
        </div>

        {/* Directory Listing */}
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="p-4 text-center text-gray-400">
              <Loader2 className="w-8 h-8 animate-spin mx-auto" />
              <p className="mt-2">Loading...</p>
            </div>
          )}

          {error && (
            <div className="p-4 text-red-400 bg-red-900/20 border border-red-800 m-4 rounded">
              {error}
            </div>
          )}

          {directoryListing && !loading && (
            <div className="p-2">
              {/* Up directory button */}
              {currentPath && (
                <button
                  onClick={navigateUp}
                  className="w-full text-left p-2 rounded hover:bg-gray-800 flex items-center text-gray-400 hover:text-white"
                >
                  <ArrowUp className="w-4 h-4 mr-3" />
                  <span>..</span>
                </button>
              )}

              {/* Directory items */}
              {directoryListing.items.map((item) => {
                const IconComponent = getFileIcon(item);
                return (
                  <button
                    key={item.path}
                    onClick={() => {
                      if (item.type === 'directory') {
                        navigateToDirectory(item.path);
                      } else {
                        loadFile(item.path);
                      }
                    }}
                    className="w-full text-left p-2 rounded hover:bg-gray-800 flex items-center justify-between group"
                  >
                    <div className="flex items-center min-w-0">
                      <IconComponent className="w-4 h-4 mr-3 text-blue-400" />
                      <span className="truncate group-hover:text-white">{item.name}</span>
                    </div>
                    <div className="text-xs text-gray-500 ml-2">
                      {item.type === 'file' && (
                        <>
                          <span>{formatFileSize(item.size)}</span>
                          {item.modified && (
                            <span className="ml-2">{formatDate(item.modified)}</span>
                          )}
                        </>
                      )}
                    </div>
                  </button>
                );
              })}

              {directoryListing.items.length === 0 && (
                <div className="p-4 text-center text-gray-500">
                  Directory is empty
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* File Content Panel */}
      <div className="w-1/2 flex flex-col">
        {selectedFile ? (
          <>
            {/* File Header */}
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold truncate">{selectedFile.name}</h3>
              <div className="text-sm text-gray-400 mt-1">
                <span>{formatFileSize(selectedFile.size)}</span>
                <span className="ml-4">{formatDate(selectedFile.modified)}</span>
                <span className="ml-4">{selectedFile.type === 'binary' ? 'Binary' : 'Text'} file</span>
              </div>
            </div>

            {/* File Content */}
            <div className="flex-1 overflow-auto">
              {selectedFile.type === 'binary' ? (
                <div className="p-4 text-center text-gray-400">
                  <File className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                  <p>{selectedFile.message}</p>
                  <p className="text-sm mt-2">File size: {formatFileSize(selectedFile.size)}</p>
                </div>
              ) : (
                <pre className="p-4 text-sm font-mono whitespace-pre-wrap break-words">
                  {selectedFile.content}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Folder className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p>Select a file to view its contents</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkspaceBrowser; 