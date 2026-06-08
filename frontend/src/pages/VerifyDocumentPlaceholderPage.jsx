import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const ALLOWED_FORMATS = ['pdf', 'doc', 'docx', 'txt', 'csv'];

const VerifyDocumentPlaceholderPage = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const validateFile = (file) => {
    if (!file) return false;
    const extension = file.name.split('.').pop()?.toLowerCase();
    return ALLOWED_FORMATS.includes(extension);
  };

  const handleFileChange = (event) => {
    setSuccessMessage('');
    setErrorMessage('');

    const file = event.target.files[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!validateFile(file)) {
      setSelectedFile(null);
      setErrorMessage(`Unsupported file format. Allowed formats: ${ALLOWED_FORMATS.join(', ')}.`);
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!selectedFile) {
      setErrorMessage('Please choose a file before uploading.');
      return;
    }

    const formData = new FormData();
    formData.append('document', selectedFile);

    setIsUploading(true);
    try {
      const response = await axios.post('/api/verify-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data?.success) {
        setSuccessMessage(response.data.message || 'File uploaded successfully.');
        setSelectedFile(null);
        event.target.reset();
      } else {
        setErrorMessage(response.data?.message || 'Upload failed.');
      }
    } catch (error) {
      setErrorMessage(
        error.response?.data?.message || 'Unable to upload the file. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="placeholder-page">
      <div className="placeholder-container" style={{ maxWidth: 640 }}>
        <span className="placeholder-icon">📄</span>
        <h2>Upload Quranic Document</h2>
        <p>
          Choose a Quranic document file to upload for verification. Supported formats are PDF, DOC/DOCX, TXT, and CSV.
        </p>

        {errorMessage && (
          <div className="alert alert-danger" role="alert">
            {errorMessage}
          </div>
        )}

        {successMessage && (
          <div className="alert alert-success" role="alert">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleUpload}>
          <div className="form-group">
            <label htmlFor="documentUpload" className="form-label">
              Upload Document
            </label>
            <input
              id="documentUpload"
              type="file"
              accept=".pdf,.doc,.docx,.txt,.csv"
              className="form-input"
              onChange={handleFileChange}
            />
          </div>

          <div className="form-group">
            <button type="submit" className="btn btn-primary btn-block" disabled={isUploading}>
              {isUploading ? 'Uploading…' : 'Upload Document'}
            </button>
          </div>

          <button type="button" className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </button>
        </form>
      </div>
    </div>
  );
};

export default VerifyDocumentPlaceholderPage;
