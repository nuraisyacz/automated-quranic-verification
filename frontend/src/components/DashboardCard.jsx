import React from 'react';

/**
 * Reusable Dashboard Card component.
 * Displays icon, title, description, and action button to route to the module.
 */
const DashboardCard = ({ icon, title, description, buttonText, onButtonClick }) => {
  return (
    <div className="dashboard-card">
      <div className="card-content">
        <h3 className="card-title">
          <span className="card-icon">{icon}</span> {title}
        </h3>
        <p className="card-description">{description}</p>
      </div>
      <button onClick={onButtonClick} className="btn btn-primary">
        {buttonText}
      </button>
    </div>
  );
};

export default DashboardCard;
