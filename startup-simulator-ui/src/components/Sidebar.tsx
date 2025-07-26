// src/components/Sidebar.tsx
import React from 'react';

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 p-4 bg-gray-800 text-white">
      <h2 className="text-xl font-bold mb-4">Agents</h2>
      <ul>
        <li>CeeCee (CEO)</li>
        <li>Marty (Marketer)</li>
        <li>Penny (Programmer)</li>
        <li>Herb (HR)</li>
      </ul>
    </div>
  );
};

export default Sidebar;
