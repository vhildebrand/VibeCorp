import React from 'react';
import { useAppStore } from '../store';
import MessageList from './MessageList';

const ChatPane: React.FC = () => {
  const { conversations, activeConversationId, agents } = useAppStore();

  const activeConversation = conversations.find(conv => conv.id === activeConversationId);

  if (!activeConversation) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="text-center text-gray-600">
          <div className="text-6xl mb-4">💬</div>
          <h2 className="text-xl font-semibold mb-2">Select a conversation</h2>
          <p>Choose a channel or direct message to start viewing the conversation.</p>
        </div>
      </div>
    );
  }

  // Get conversation members for header display
  const conversationMembers = activeConversation.members
    .map(memberId => agents.find(agent => agent.id === memberId))
    .filter(Boolean);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className="text-xl">
                {activeConversation.type === 'group' ? '#' : '💬'}
              </span>
              <h1 className="text-xl font-bold text-gray-900">
                {activeConversation.name}
              </h1>
            </div>
            {activeConversation.description && (
              <div className="hidden md:block">
                <span className="text-gray-500">|</span>
                <span className="ml-2 text-sm text-gray-600">
                  {activeConversation.description}
                </span>
              </div>
            )}
          </div>
          
          {/* Member count and avatars */}
          <div className="flex items-center space-x-2">
            <div className="flex -space-x-2">
              {conversationMembers.slice(0, 4).map((member) => (
                <div
                  key={member?.id}
                  className="w-8 h-8 rounded-full bg-gray-300 border-2 border-white flex items-center justify-center text-sm"
                  title={member?.name.replace(/_/g, ' ')}
                >
                  {member?.avatar}
                </div>
              ))}
              {conversationMembers.length > 4 && (
                <div className="w-8 h-8 rounded-full bg-gray-400 border-2 border-white flex items-center justify-center text-xs text-white">
                  +{conversationMembers.length - 4}
                </div>
              )}
            </div>
            <span className="text-sm text-gray-500 ml-2">
              {conversationMembers.length} member{conversationMembers.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        <MessageList />
      </div>
    </div>
  );
};

export default ChatPane; 