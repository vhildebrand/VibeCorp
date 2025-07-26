import ChatWindow from './components/ChatWindow';
import Sidebar from './components/Sidebar';
import TaskStatus from './components/TaskStatus';

function App() {
  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <div className="flex flex-col flex-1">
        <TaskStatus />
        <ChatWindow />
      </div>
    </div>
  );
}

export default App;
