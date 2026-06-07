import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Route guard component that verifies if a user is authenticated.
 * If authentication is loading, displays a loading message/spinner.
 * If the user is unauthenticated, redirects them to the Login page.
 */
const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        color: '#1b4332',
        fontSize: '1.2rem',
        fontWeight: '600',
        fontFamily: 'sans-serif'
      }}>
        Loading session...
      </div>
    );
  }

  if (!token) {
    // Redirect to Login if there is no valid authentication token
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
