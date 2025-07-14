import { ThemeToggle } from "./theme-toggle";
import { useAuth } from "../../context/AuthContext";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "react-router-dom";
import { Plus, LogOut } from "lucide-react";

interface HeaderProps {
  onNewChat?: () => void;
}

export const Header = ({ onNewChat }: HeaderProps) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    // Clear chat memory through WebSocket if available
    const ws = new WebSocket("ws://localhost:8092");
    ws.onopen = () => {
      ws.send("LOGOUT");
      ws.close();
    };
    navigate('/');
  };

  return (
    <>
      <header className="flex items-center justify-between px-2 sm:px-4 py-2 bg-background text-black dark:text-white w-full border-b">
        <div className="flex items-center space-x-1 sm:space-x-2">
          <h1 className="text-lg font-semibold">CHARUSAT Chatbot</h1>
        </div>
        
        <div className="flex items-center space-x-2">
          {isAuthenticated && onNewChat && (
            <Button
              variant="outline"
              size="sm"
              onClick={onNewChat}
              className="flex items-center space-x-1"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">New Chat</span>
            </Button>
          )}
          
          {isAuthenticated ? (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400 hidden sm:inline">
                Welcome, {user?.username}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                className="flex items-center space-x-1"
              >
                <LogOut size={16} />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Link to="/login">
                <Button variant="outline" size="sm">
                  Login
                </Button>
              </Link>
              <Link to="/register">
                <Button size="sm">
                  Register
                </Button>
              </Link>
            </div>
          )}
          <ThemeToggle />
        </div>
      </header>
    </>
  );
};