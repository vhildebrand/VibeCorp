import React, { useEffect, useRef } from 'react';
import { useAppStore } from '../store';
import AgentMessage from './AgentMessage';

const MessageList: React.FC = () => {
  const { messages, activeConversationId } = useAppStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Filter messages for the active conversation
  const conversationMessages = messages.filter(
    message => message.conversationId === activeConversationId
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationMessages]);

  if (!activeConversationId) {
    return null;
  }

  if (conversationMessages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-2">💭</div>
          <p>No messages yet</p>
          <p className="text-sm">The conversation will appear here once agents start chatting!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {conversationMessages.map((message, index) => {
          // Check if this message is from the same agent as the previous one
          // and if it was sent within 5 minutes
          const prevMessage = conversationMessages[index - 1];
          const isGrouped = prevMessage && 
            prevMessage.agentId === message.agentId &&
            new Date(message.timestamp).getTime() - new Date(prevMessage.timestamp).getTime() < 5 * 60 * 1000;

          return (
            <AgentMessage
              key={message.id}
              message={message}
              isGrouped={isGrouped}
            />
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default MessageList; 