import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const isPositiveInt = (val) => {
  if (val === null || val === undefined || val === '') return false;
  const n = Number(val);
  return Number.isInteger(n) && n > 0;
};

const SearchQuranicTextPage = () => {
  const navigate = useNavigate();
  const [surah, setSurah] = useState('');
  const [ayah, setAyah] = useState('');
  const [juz, setJuz] = useState('30');
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState([]);
  const [statusMessage, setStatusMessage] = useState('No results to display. Enter search criteria and press Search.');

  const clear = () => {
    setSurah('');
    setAyah('');
    setKeyword('');
    setResults([]);
    setError('');
    setStatusMessage('No results to display. Enter search criteria and press Search.');
  };

  const handleSearch = async (e) => {
    e && e.preventDefault();
    setError('');
    setStatusMessage('');
    setResults([]);

    const hasSurah = isPositiveInt(surah);
    const hasAyah = isPositiveInt(ayah);
    const hasJuz = isPositiveInt(juz);
    const kw = keyword.trim();

    if (!hasSurah && !hasAyah && !hasJuz && kw === '') {
      setError('Please provide at least one search criteria.');
      return;
    }

    const params = {};
    if (hasSurah) params.surah_number = Number(surah);
    if (hasAyah) params.ayah_number = Number(ayah);
    if (hasJuz) params.juz_number = Number(juz);
    if (kw !== '') params.keyword = kw;

    setLoading(true);
    try {
      const resp = await axios.get('/api/search-quranic-text', { params });
      if (resp.data && resp.data.success) {
        if (resp.data.count === 0) {
          setResults([]);
          setStatusMessage('No matching Quranic text found.');
        } else {
          setResults(resp.data.results || []);
        }
      } else {
        setError(resp.data?.message || 'Unexpected response from server.');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Request failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <div className="search-header">
        <h2>Search Quranic Text</h2>
        <p>Search Quranic text by Juz number, Surah number, Ayah number, or keyword.</p>
      </div>

      <div className="search-layout">
        <div className="search-input-card">
          <h3>Search Criteria</h3>
          <form onSubmit={handleSearch} className="search-form">
            <div className="form-group">
              <label className="form-label">Juz Number</label>
              <input
                className="form-input"
                type="number"
                min="1"
                value={juz}
                onChange={(e) => setJuz(e.target.value)}
                placeholder="e.g. 30"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Surah Number</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  value={surah}
                  onChange={(e) => setSurah(e.target.value)}
                  placeholder="e.g. 112"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Ayah Number</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  value={ayah}
                  onChange={(e) => setAyah(e.target.value)}
                  placeholder="e.g. 4"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Keyword</label>
              <input
                className="form-input"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Search Arabic text or surah name"
              />
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="form-actions">
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
              </button>
              <button className="btn btn-secondary" type="button" onClick={clear} disabled={loading}>
                Clear
              </button>
              <button className="btn btn-secondary" type="button" onClick={() => navigate('/dashboard')}>
                ← Back to Dashboard
              </button>
            </div>
          </form>
        </div>

        <div className="search-results-card">
          <h3>Search Results</h3>
          <div className="results-panel">
            {loading && <div className="alert">Searching...</div>}
            {!loading && results.length === 0 && !error && (
              <div className="empty-results">{statusMessage}</div>
            )}
            {results.length > 0 && (
              <div className="translation-results-list">
                {results.map((item) => (
                  <div key={`${item.surah_number}-${item.ayah_number}`} className="translation-result-card">
                    <div className="translation-result-meta">
                      <span>Juz: {item.juz_number}</span>
                      <span>Surah: {item.surah_number}</span>
                      <span>Ayah: {item.ayah_number}</span>
                      <span>{item.surah_name}</span>
                    </div>
                    <p style={{ fontSize: '1.25rem', lineHeight: '1.8', textAlign: 'right' }}>{item.arabic_text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchQuranicTextPage;
