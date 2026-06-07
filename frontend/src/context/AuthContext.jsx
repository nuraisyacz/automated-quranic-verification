import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

// Create the authentication context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Set default authorization headers for Axios requests if token exists
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }

  // Check if user is logged in (verify token with backend) on mount
  useEffect(() => {
    const verifyUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      
      try {
        // Call the endpoint to fetch logged-in user profile info
        const response = await axios.get('/api/auth/me');
        setUser(response.data.user);
      } catch (error) {
        console.error("Token verification failed:", error);
        // If the token is expired/invalid, clear local authentication state
        logoutLocal();
      } finally {
        setLoading(false);
      }
    };

    verifyUser();
  }, [token]);

  // Perform client-side state cleanup for logging out
  const logoutLocal = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  /**
   * Action: Register a new user
   */
  const register = async (fullName, email, password, confirmPassword) => {
    try {
      const response = await axios.post('/api/auth/register', {
        full_name: fullName,
        email,
        password,
        confirm_password: confirmPassword
      });
      return { success: true, message: response.data.message };
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Registration failed. Please check your inputs.';
      return { success: false, message: errorMsg };
    }
  };

  /**
   * Action: Authenticate and login user
   */
  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { access_token, user: loggedUser } = response.data;
      
      // Update local storage and authorization headers
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(loggedUser);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true, message: response.data.message };
    } catch (error) {
      const errorMsg = error.response?.data?.message || 'Login failed. Please check your credentials.';
      return { success: false, message: errorMsg };
    }
  };

  /**
   * Action: Logout user
   */
  const logout = async () => {
    try {
      // Send optional call to backend logout endpoint
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.warn("Backend logout endpoint failed or unreachable", error);
    } finally {
      // Always clear local authentication credentials
      logoutLocal();
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to consume the AuthContext safely
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
