import React from 'react';

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
  required = false 
}) => {
  return (
    <div className="form-group">
      <label htmlFor={id} className="form-label">
        {label} {required && <span style={{ color: 'var(--error-color)' }}>*</span>}
      </label>
      <input
        type={type}
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`form-input ${error ? 'is-invalid' : ''}`}
        required={required}
      />
      {error && <span className="form-error-msg">{error}</span>}
    </div>
  );
};

export default FormInput;
