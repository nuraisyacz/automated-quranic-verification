import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import DashboardCard from '../components/DashboardCard';
import heroBg from '../assets/hero.png';

/**
 * Dashboard page component.
 * Displays greeting, system overview, and option cards for system modules.
 */
const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="dashboard-container">
      {/* Hero Welcome Section */}
      <section
        className="dashboard-hero"
        style={{
          backgroundImage: `linear-gradient(180deg, rgba(29, 84, 55, 0.82), rgba(8, 30, 21, 0.88)), url(${heroBg})`,
          backgroundBlendMode: 'overlay',
        }}
      >
        <div className="dashboard-hero-copy">
          <span className="hero-label">Quranic Verification</span>
          <h1>Welcome, {user?.full_name || 'Evaluator'}</h1>
          <p>
            This system helps verify digital Quranic text and translations using trusted reference data.
          </p>
        </div>
      </section>

      <section className="dashboard-hadith-card">
        <div className="hadith-card-header">
          <span className="hadith-card-title">Hadith Reminder</span>
        </div>
        <blockquote className="hadith-text">
          “Seeking knowledge is an obligation upon every Muslim.”
        </blockquote>
        <p className="hadith-caption">
          Verify information with trustworthy sources and uphold the value of beneficial knowledge.
        </p>
      </section>

      {/* Feature cards layout grid */}
      <div className="dashboard-grid">
        <DashboardCard
          icon="📄"
          title="Verify Document"
          description="Upload Quranic text or translation documents for automated verification against standard scripts."
          buttonText="Start Verification"
          onButtonClick={() => navigate('/verify-document')}
        />

        <DashboardCard
          icon="🔍"
          title="Search Quranic Translation"
          description="Search Quranic translation records by surah, ayah, or keyword from the translation database."
          buttonText="Search Translation"
          onButtonClick={() => navigate('/search-translation')}
        />

        <DashboardCard
          icon="🔍"
          title="Search Quranic Text"
          description="Search verified Quranic text and translations by surah, ayah, juz, or keyword parameters."
          buttonText="Search Text"
          onButtonClick={() => navigate('/search-text')}
        />
      </div>
    </div>
  );
};

export default DashboardPage;
