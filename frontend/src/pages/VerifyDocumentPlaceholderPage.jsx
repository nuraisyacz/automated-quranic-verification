import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Placeholder page for the Document Verification module.
 * Displayed as a temporary landing during Phase 1.
 */
const VerifyDocumentPlaceholderPage = () => {
  const navigate = useNavigate();

  return (
    <div className="placeholder-page">
      <div className="placeholder-container">
        <span className="placeholder-icon">📄</span>
        <h2>Verify Document</h2>
        <p>Document verification module will be developed in the next phase.</p>
        <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default VerifyDocumentPlaceholderPage;
