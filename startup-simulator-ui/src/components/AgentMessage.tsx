// src/components/AgentMessage.tsx
import React from 'react';

interface AgentMessageProps {
  agent: string;
  content: string;
}

const AgentMessage: React.FC<AgentMessageProps> = ({ agent, content }) => {
  const agentColor = (
    agent: string
  ): string => {
    switch (agent) {
      case "CeeCee_The_CEO":
        return "text-blue-400";
      case "Marty_The_Marketer":
        return "text-green-400";
      case "Penny_The_Programmer":
        return "text-red-400";
      case "Herb_From_HR":
        return "text-yellow-400";
      default:
        return "text-gray-400";
    }
  };
  return (
    <div className="mb-4">
      <div className={`font-bold ${agentColor(agent)}`}>{agent}</div>
      <div className="text-gray-800">{content}</div>
    </div>
  );
};

export default AgentMessage;
