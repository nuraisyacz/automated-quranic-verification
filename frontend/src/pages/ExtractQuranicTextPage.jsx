import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const ExtractQuranicTextPage = () => {
  const navigate = useNavigate();
  const [uploadInfo, setUploadInfo] = useState(null);
  const [message, setMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('lastUploadedDocument');
    if (stored) {
      try {
        setUploadInfo(JSON.parse(stored));
      } catch {
        setUploadInfo(null);
      }
    }
  }, []);

  const handleExtract = async () => {
    setErrorMessage('');
    setMessage('');
    setDownloadUrl('');

    if (!uploadInfo?.stored_filename) {
      setErrorMessage('No uploaded document found. Please upload a document first.');
      return;
    }

    setIsExtracting(true);

    try {
      const response = await axios.post('/api/extract-document', {
        stored_filename: uploadInfo.stored_filename
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data?.success) {
        const url = response.data.download_url;
        setDownloadUrl(url);
        setMessage(`Extraction complete: ${response.data.extracted_count} rows saved to CSV.`);
        await openCsvInNewTab(url);
      } else {
        setErrorMessage(response.data?.message || 'Extraction failed.');
      }
    } catch (error) {
      setErrorMessage(
        error.response?.data?.message || 'Unable to extract text from the uploaded document.'
      );
    } finally {
      setIsExtracting(false);
    }
  };

  const openCsvInNewTab = async (url) => {
    const newWindow = window.open('about:blank', '_blank');
    try {
      const response = await axios.get(url, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'text/csv' });
      const blobUrl = URL.createObjectURL(blob);
      if (newWindow) {
        newWindow.location.href = blobUrl;
      } else {
        window.open(blobUrl, '_blank');
      }
    } catch (error) {
      if (newWindow) {
        newWindow.close();
      }
      setErrorMessage('Failed to open extracted CSV in a new tab.');
    }
  };

  return (
    <div className="placeholder-page">
      <div className="placeholder-container" style={{ maxWidth: 680 }}>
        <span className="placeholder-icon">🗂️</span>
        <h2>Quranic Text Extraction</h2>
        <p>
          This module converts the uploaded Quranic document into a structured CSV file containing Arabic Quranic text and its translation.
          After extraction, the resulting CSV will open in a new browser tab.
        </p>

        {uploadInfo ? (
          <div className="alert alert-success" role="alert">
            <strong>Uploaded document:</strong> {uploadInfo.original_name}
            <br />
            <strong>Uploaded at:</strong> {new Date(uploadInfo.uploaded_at).toLocaleString()}
          </div>
        ) : (
          <div className="alert alert-danger" role="alert">
            No uploaded document available. Please upload a Quranic document first.
          </div>
        )}

        {errorMessage && (
          <div className="alert alert-danger" role="alert">
            {errorMessage}
          </div>
        )}

        {message && (
          <div className="alert alert-success" role="alert">
            {message}
          </div>
        )}

        <div className="form-group">
          <button
            type="button"
            className="btn btn-primary btn-block"
            onClick={handleExtract}
            disabled={isExtracting || !uploadInfo}
          >
            {isExtracting ? 'Extracting…' : 'Extract Quranic Text'}
          </button>
        </div>

        {downloadUrl && (
          <div className="form-group">
            <button
              type="button"
              className="btn btn-secondary btn-block"
              onClick={() => openCsvInNewTab(downloadUrl)}
            >
              Open Extracted CSV
            </button>
          </div>
        )}

        <button type="button" className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default ExtractQuranicTextPage;
