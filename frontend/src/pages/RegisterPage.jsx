import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import FormInput from '../components/FormInput';

/**
 * RegisterPage component.
 * Allows users to register a new account with validations.
 */
const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();

  // Form input states
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Field validation and API feedback states
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [loading, setLoading] = useState(false);

  // Email format validation helper
  const isValidEmailFormat = (val) => {
    return /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(val);
  };

  // Password validation helper
  const isValidPasswordFormat = (val) => {
    return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(val);
  };

  const validate = () => {
    const newErrors = {};

    if (!fullName.trim()) {
      newErrors.fullName = 'Please enter your full name';
    }

    if (!email.trim()) {
      newErrors.email = 'Please enter your email';
    } else if (!isValidEmailFormat(email)) {
      newErrors.email = 'Please enter a valid email format';
    }

    if (!password) {
      newErrors.password = 'Please enter your password';
    } else if (!isValidPasswordFormat(password)) {
      newErrors.password =
        'Password must be at least 8 characters and include uppercase, lowercase, number, and special character';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');

    if (!validate()) return;

    setLoading(true);
    const result = await register(fullName, email, password, confirmPassword);
    setLoading(false);

    if (result.success) {
      // Redirect to login page and pass the success message via navigation state
      navigate('/login', {
        state: { successMessage: 'Registration successful. Please login.' }
      });
    } else {
      setApiError(result.message);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Create Account</h2>
          <p>Register as a verified system evaluator</p>
        </div>

        {apiError && (
          <div className="alert alert-danger">
            <span>⚠️</span> {apiError}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <FormInput
            label="Full Name"
            id="fullName"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="e.g. Ahmad bin Ali"
            error={errors.fullName}
            required
          />

          <FormInput
            label="Email Address"
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="e.g. ahmad.ali@example.com"
            error={errors.email}
            required
          />

          <FormInput
            label="Password"
            id="password"
            type="password"
            togglePassword
            showPasswordRequirements
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password"
            error={errors.password}
            required
          />

          <FormInput
            label="Confirm Password"
            id="confirmPassword"
            type="password"
            togglePassword
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter password"
            error={errors.confirmPassword}
            required
          />

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
            style={{ marginTop: '1rem' }}
          >
            {loading ? 'Creating Account...' : 'Register'}
          </button>
        </form>

        <div className="auth-footer">
          Already registered?{' '}
          <Link to="/login" className="btn-link">
            Login here
          </Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
