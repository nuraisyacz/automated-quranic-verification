import React, { useState } from 'react';

/**
 * Reusable Form Input component.
 * Displays field label, input field, and inline error validation message.
 */
const FormInput = ({ 
  label, 
  id, 
  name, 
  type = 'text', 
  value, 
  onChange, 
  placeholder, 
  error, 
  required = false,
  togglePassword = false,
  showPasswordRequirements = false,
}) => {
  const [visible, setVisible] = useState(false);

  const inputType = type === 'password' && togglePassword ? (visible ? 'text' : 'password') : type;

  return (
    <div className="form-group">
      <label htmlFor={id} className="form-label">
        {label} {required && <span style={{ color: 'var(--error-color)' }}>*</span>}
        {type === 'password' && togglePassword && showPasswordRequirements && (
          <span className="password-help-icon" title="Password requirements">
            ?
            <span className="password-tooltip">
              <strong>Password Requirements:</strong>
              <ul>
                <li>At least 8 characters</li>
                <li>At least one uppercase letter</li>
                <li>At least one lowercase letter</li>
                <li>At least one number</li>
                <li>At least one special character</li>
              </ul>
            </span>
          </span>
        )}
      </label>

      <div className="input-with-toggle">
        <input
          type={inputType}
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`form-input ${togglePassword ? 'with-toggle' : ''} ${error ? 'is-invalid' : ''}`}
          required={required}
        />

        {type === 'password' && togglePassword && (
          <button
            type="button"
            className="input-toggle-text"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? 'Hide password' : 'Show password'}
          >
            {visible ? 'Hide' : 'Show'}
          </button>
        )}
      </div>

      {error && <span className="form-error-msg">{error}</span>}
    </div>
  );
};

export default FormInput;
