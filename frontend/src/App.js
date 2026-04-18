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
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/favorite" element={<FavoritePage />} />
            <Route path="/" element={<Navigate to="/slides" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
