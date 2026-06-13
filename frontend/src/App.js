import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthenticatedLayout from "./components/AuthenticatedLayout";
import DashboardPage from "./pages/DashboardPage";
import FavoritePage from "./pages/FavoritePage";
import Login from "./pages/Login";
import SlidePage from "./pages/SlidePage";
import VoiceChatPage from "./pages/VoiceChatPage";

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <ProtectedRoute>
                <AuthenticatedLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/slides" element={<SlidePage />} />
            <Route path="/chat" element={<VoiceChatPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/favorite" element={<FavoritePage />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
