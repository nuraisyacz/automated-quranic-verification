import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import VerifyDocumentPlaceholderPage from './pages/VerifyDocumentPlaceholderPage';
import ExtractQuranicTextPage from './pages/ExtractQuranicTextPage';
import SearchQuranicTextPage from './pages/SearchQuranicTextPlaceholderPage';
import SearchTranslationPage from './pages/SearchTranslationPage';
import './styles.css';

/**
 * Main application component configuring routes and state providers.
 */
function App() {
  return (
    <Router>
      <AuthProvider>
        {/* Navbar is displayed globally and adjusts links based on auth state */}
        <Navbar />
        
        {/* Route Definitions */}
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Protected Routes (requires authentication) */}
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/verify-document" 
            element={
              <ProtectedRoute>
                <VerifyDocumentPlaceholderPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/extract-text" 
            element={
              <ProtectedRoute>
                <ExtractQuranicTextPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/search-text" 
            element={
              <ProtectedRoute>
                <SearchQuranicTextPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/search-translation" 
            element={
              <ProtectedRoute>
                <SearchTranslationPage />
              </ProtectedRoute>
            } 
          />
          
          {/* Default fallback redirects to Dashboard (which redirects to Login if unauthenticated) */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
