// frontend/src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import LoginPage from "./pages/LoginPage";
import BoardPage from "./pages/BoardPage";
import useAuthStore from "./store/authStore";

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#1f2937",
            color: "#f9fafb",
            border: "1px solid #374151",
          },
        }}
      />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/board"
          element={
            <ProtectedRoute>
              <BoardPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/board" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
