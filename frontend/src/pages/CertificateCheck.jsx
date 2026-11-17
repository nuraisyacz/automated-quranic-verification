import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const LABEL = { accurate: 'Verified', partially_accurate: 'Partially verified', inaccurate: 'Not verified' };
const TYPE_LABEL = { quranic_text: 'Quranic text', translation: 'Quranic translation' };

export default function CertificateCheck() {
  const { ref } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`/api/verify/certificate/${encodeURIComponent(ref)}`)
      .then((r) => setData(r.data))
      .catch(() => setError('Could not check this certificate. Please try again.'));
  }, [ref]);

  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!data) return <p>Checking certificate…</p>;
  if (!data.valid) return <div className="alert alert-danger">{data.message}</div>;

  const c = data.certificate;
  return (
    <div className="verify-stage-card">
      <h3>Certificate {c.reference_no}</h3>
      <p><strong>Type:</strong> {TYPE_LABEL[c.verification_type] || c.verification_type}</p>
      <div className={`verification-status-banner ${c.status}`}>
        <span>{LABEL[c.status] || c.status}</span>
        <span>Accuracy: {c.accuracy_percentage}%</span>
      </div>
      <p><strong>Issued:</strong> {new Date(c.issued_at).toLocaleString()}</p>
      <p><strong>Scope:</strong> {c.scope}</p>
      <p><strong>Reference source:</strong> {c.reference_source}</p>
      <p><strong>Ayahs checked:</strong> {c.total_rows} · exact {c.exact_matches} · diacritic-only {c.partial_matches} · mismatches {c.mismatches} · missing {c.missing_ayahs}</p>
      <p><strong>Content hash:</strong> <code style={{ wordBreak: 'break-all' }}>{c.content_sha256}</code></p>
    </div>
  );
}