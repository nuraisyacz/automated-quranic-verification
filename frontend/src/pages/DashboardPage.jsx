import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import DashboardCard from '../components/DashboardCard';

/**
 * Dashboard page component.
 * Displays greeting, system overview, and option cards for system modules.
 */
const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recentUpload, setRecentUpload] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem('lastUploadedDocument');
    if (stored) {
      try {
        setRecentUpload(JSON.parse(stored));
      } catch {
        setRecentUpload(null);
      }
    }
  }, []);

  return (
    <div className="dashboard-container">
      {/* Hero Welcome Section */}
      <section className="dashboard-hero">
        <h1>Welcome, {user?.full_name || 'Evaluator'}</h1>
        <p>
          This system helps verify digital Quranic text and translations using trusted reference data.
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
          icon="�️"
          title="Extract Quranic Text"
          description="Convert uploaded Quranic documents into extracted Arabic text and translation CSV output."
          buttonText="Extract Text"
          onButtonClick={() => navigate('/extract-text')}
        />

        <DashboardCard
          icon="�🔍"
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

        {recentUpload && (
          <div className="dashboard-card upload-preview-card">
            <div className="card-content">
              <h3 className="card-title">
                <span className="card-icon">📝</span> Recent Upload
              </h3>
              <p className="card-description">
                Last uploaded document:
                <strong> {recentUpload.original_name}</strong>
              </p>
              <p className="card-description">
                Uploaded on: {new Date(recentUpload.uploaded_at).toLocaleString()}
              </p>
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/verify-document')}>
              Upload Another
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
