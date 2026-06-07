import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Placeholder page for the Quranic Text Search module.
 * Displayed as a temporary landing during Phase 1.
 */
const SearchQuranicTextPlaceholderPage = () => {
  const navigate = useNavigate();

  return (
    <div className="placeholder-page">
      <div className="placeholder-container">
        <span className="placeholder-icon">🔍</span>
        <h2>Search Quranic Text</h2>
        <p>Quranic text search module will be developed in the next phase.</p>
        <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default SearchQuranicTextPlaceholderPage;
