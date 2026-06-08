import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const isPositiveInt = (val) => {
  if (val === null || val === undefined || val === '') return false;
  const n = Number(val);
  return Number.isInteger(n) && n > 0;
};

const SearchTranslationPage = () => {
  const navigate = useNavigate();
  const [surah, setSurah] = useState('');
  const [ayah, setAyah] = useState('');
  const [keyword, setKeyword] = useState('');
  const [language, setLanguage] = useState('bahasa');
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
    const kw = keyword.trim();

    if (!hasSurah && !hasAyah && kw === '') {
      setError('Please enter at least one search criteria.');
      return;
    }

    const params = {};
    if (hasSurah) params.surah_number = Number(surah);
    if (hasAyah) params.ayah_number = Number(ayah);
    if (kw !== '') params.keyword = kw;

    setLoading(true);
    try {
      const resp = await axios.get('/api/quran/search', { params });
      if (resp.data && resp.data.success) {
        if (resp.data.count === 0) {
          setResults([]);
          setStatusMessage('No matching translation found.');
        } else {
          setResults(resp.data.results || []);
        }
      } else {
        setError(resp.data?.message || 'Unexpected response');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <div className="search-header-row">
        <button type="button" className="btn btn-secondary btn-back" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
        <div className="search-header">
          <h2>Search Quranic Translation</h2>
          <p>Search translations by Surah number, Ayah number, or keyword.</p>
        </div>
      </div>

      <div className="search-layout">
        <div className="search-input-card">
          <h3>Search Criteria</h3>
          <form onSubmit={handleSearch} className="search-form">
            <div className="form-group">
              <label className="form-label">Language</label>
              <select
                className="form-input"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="english" disabled>
                  English (not available)
                </option>
                <option value="bahasa">Bahasa Melayu</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Keyword</label>
              <input
                className="form-input"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Enter keyword"
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
                  placeholder="e.g. 27"
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
                  placeholder="e.g. 55"
                />
              </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="form-actions">
              <button className="btn btn-primary" type="submit" disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
              </button>
              <button className="btn btn-secondary" type="button" onClick={clear} disabled={loading}>
                Clear
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
                {results.map((r) => (
                  <div key={`${r.surah_number}-${r.ayah_number}`} className="translation-result-card">
                    <div className="translation-result-meta">
                      <span>Surah: {r.surah_number}</span>
                      <span>Ayah: {r.ayah_number}</span>
                    </div>
                    <p>{r.translation}</p>
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

export default SearchTranslationPage;
