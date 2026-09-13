// frontend/src/components/NavBar.jsx
import { Brain, LogOut, User } from "lucide-react";
import useAuthStore from "../store/authStore";
import { useNavigate } from "react-router-dom";

export default function NavBar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Brain className="text-blue-400" size={24} />
        <span className="text-white font-bold text-lg">TaskMind</span>
        <span className="text-gray-500 text-xs ml-2">AI Task Manager</span>
      </div>

      {user && (
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <User size={16} />
            <span>{user.name}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-gray-400 hover:text-red-400 text-sm transition-colors"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}
