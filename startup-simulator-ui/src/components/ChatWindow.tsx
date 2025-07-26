// src/components/ChatWindow.tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import AgentMessage from './AgentMessage';

interface Message {
  agent: string;
  content: string;
}

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    // Mock data for now
    const mockMessages: Message[] = [
      { agent: 'CeeCee_The_CEO', content: 'Good morning team, time to disrupt the market. This quarter, we need to launch a revolutionary product that will redefine our industry. Let\'s brainstorm some killer ideas. I want maximum synergy on this!We\'ll need a viral marketing campaign to back it up. Let\'s get to work!' },
      { agent: 'Marty_The_Marketer', content: '🚀 YES! Let\'s create a viral TikTok dance challenge! 💃🕺 It\'ll be HUGE! ✨' },
      { agent: 'Penny_The_Programmer', content: 'LOG: A TikTok dance is not a product. I will begin scaffolding the backend infrastructure.' },
      { agent: 'Herb_From_HR', content: 'Team, let\'s remember to respect everyone\'s ideas. A trust-fall exercise could really help our synergy.' },
    ];
    setMessages(mockMessages);
  }, []);

  return (
    <div className="flex-1 p-4 bg-gray-100 overflow-y-auto">
      {messages.map((msg, index) => (
        <AgentMessage key={index} agent={msg.agent} content={msg.content} />
      ))}
    </div>
  );
};

export default ChatWindow;
