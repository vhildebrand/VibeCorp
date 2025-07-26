import React from 'react';
import { useAppStore } from '../store';

const ChannelList: React.FC = () => {
  const { conversations, activeConversationId, setActiveConversation, sidebarCollapsed } = useAppStore();

  // Separate channels and DMs
  const channels = conversations.filter(conv => conv.type === 'group');
  const directMessages = conversations.filter(conv => conv.type === 'dm');

  const formatLastMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h`;
    } else {
      return `${Math.floor(diffInHours / 24)}d`;
    }
  };

  const ConversationItem: React.FC<{ conversation: any }> = ({ conversation }) => (
    <button
      onClick={() => setActiveConversation(conversation.id)}
      className={`w-full text-left p-2 rounded mx-2 mb-1 transition-colors ${
        activeConversationId === conversation.id
          ? 'bg-blue-600 text-white'
          : 'hover:bg-gray-700 text-gray-300'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          <span className="text-gray-400">
            {conversation.type === 'group' ? '#' : '💬'}
          </span>
          {!sidebarCollapsed && (
            <span className="font-medium truncate">
              {conversation.name}
            </span>
          )}
        </div>
        {!sidebarCollapsed && (
          <div className="flex items-center space-x-2">
            {conversation.unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs rounded-full px-2 py-1 min-w-[20px] text-center">
                {conversation.unreadCount > 99 ? '99+' : conversation.unreadCount}
              </span>
            )}
            <span className="text-xs text-gray-500">
              {formatLastMessageTime(conversation.lastMessageTime)}
            </span>
          </div>
        )}
      </div>
      {!sidebarCollapsed && conversation.description && (
        <p className="text-xs text-gray-500 mt-1 truncate">
          {conversation.description}
        </p>
      )}
    </button>
  );

  if (sidebarCollapsed) {
    return (
      <div className="py-2">
        {[...channels, ...directMessages].map((conversation) => (
          <ConversationItem key={conversation.id} conversation={conversation} />
        ))}
      </div>
    );
  }

  return (
    <div className="py-2">
      {/* Channels Section */}
      <div className="mb-4">
        <div className="px-4 mb-2">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            Channels
          </h3>
        </div>
        {channels.map((conversation) => (
          <ConversationItem key={conversation.id} conversation={conversation} />
        ))}
      </div>

      {/* Direct Messages Section */}
      <div>
        <div className="px-4 mb-2">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            Direct Messages
          </h3>
        </div>
        {directMessages.map((conversation) => (
          <ConversationItem key={conversation.id} conversation={conversation} />
        ))}
      </div>
    </div>
  );
};

export default ChannelList; 