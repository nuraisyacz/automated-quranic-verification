import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import mammoth from 'mammoth';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import pdfWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

const allowedFiles = ['pdf', 'docx', 'txt', 'csv'];

const STATUS_LABELS = {
  accurate: 'Accurate',
  partially_accurate: 'Partially Accurate',
  inaccurate: 'Inaccurate',
  reference_not_found: 'No Reference',
  invalid_row: 'Invalid Row',
};

const FLOW_CONFIG = {
  translation: {
    label: 'Translation',
    uploadDescription: 'Upload a Quranic translation as CSV, TXT, PDF, or DOCX. CSV format is recommended (surah_number, ayah_number, translation).',
    extractTitle: 'Extracted Translation CSV',
    extractDescription: 'Review the extracted translation rows below. When ready, proceed to verification.',
    contentColumn: 'Translation',
    contentField: 'translation',
    verifyEndpoint: '/api/verify/translation',
    pdfEndpoint: '/api/verify/translation/report/pdf',
    verifyButton: 'Verify Translation',
    verifySuccess: 'Translation verification completed.',
    stepVerifyTitle: 'Verify Translation',
    csvSuffix: 'translation',
    referenceLabel: 'Approved translation repository',
  },
  quranic_text: {
    label: 'Quranic Text',
    uploadDescription: 'Upload Quranic Arabic text as CSV, TXT, PDF, or DOCX. CSV format is recommended (surah_number, ayah_number, arabic_text).',
    extractTitle: 'Extracted Quranic Text CSV',
    extractDescription: 'Review the extracted Arabic text rows below. When ready, proceed to verification.',
    contentColumn: 'Arabic Text',
    contentField: 'arabic_text',
    verifyEndpoint: '/api/verify/quranic-text',
    pdfEndpoint: '/api/verify/quranic-text/report/pdf',
    verifyButton: 'Verify Quranic Text',
    verifySuccess: 'Quranic text verification completed.',
    stepVerifyTitle: 'Verify Quranic Text',
    csvSuffix: 'quranic-text',
    referenceLabel: 'Trusted Quranic text repository',
  },
};

const VerifyDocumentPlaceholderPage = () => {
  const navigate = useNavigate();
  const [verificationType, setVerificationType] = useState(null);
  const [activeStep, setActiveStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [extractedRows, setExtractedRows] = useState([]);
  const [csvContent, setCsvContent] = useState('');
  const [verificationReport, setVerificationReport] = useState(null);
  const [resultFilter, setResultFilter] = useState('all');
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const config = FLOW_CONFIG[verificationType] || FLOW_CONFIG.translation;

  const fileSummary = useMemo(() => {
    if (!selectedFile) return null;
    return {
      name: selectedFile.name,
      type: selectedFile.type || selectedFile.name.split('.').pop().toUpperCase(),
      size: formatFileSize(selectedFile.size),
    };
  }, [selectedFile]);

  const filteredDetails = useMemo(() => {
    if (!verificationReport?.details) return [];
    if (resultFilter === 'all') return verificationReport.details;
    if (resultFilter === 'mismatches') {
      return verificationReport.details.filter((d) => d.status !== 'accurate');
    }
    return verificationReport.details.filter((d) => d.status === resultFilter);
  }, [verificationReport, resultFilter]);

  const resetPage = () => {
    setVerificationType(null);
    setActiveStep(1);
    setSelectedFile(null);
    setFileError('');
    setLoading(false);
    setSuccessMessage('');
    setExtractedRows([]);
    setCsvContent('');
    setVerificationReport(null);
    setResultFilter('all');
  };

  const clearWorkflowData = () => {
    setSelectedFile(null);
    setFileError('');
    setSuccessMessage('');
    setExtractedRows([]);
    setCsvContent('');
    setVerificationReport(null);
    setResultFilter('all');
  };

  const handleSelectType = (type) => {
    setVerificationType(type);
    clearWorkflowData();
    setActiveStep(2);
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setFileError('');
    setSuccessMessage('');
    setCsvContent('');
    setExtractedRows([]);
    setVerificationReport(null);
  };

  const handleFileSelection = (file) => {
    setSuccessMessage('');
    setExtractedRows([]);
    setCsvContent('');
    setVerificationReport(null);
    setFileError('');

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const extension = getFileExtension(file.name);
    if (!allowedFiles.includes(extension)) {
      setFileError('Unsupported file type. Please upload PDF, DOCX, TXT, or CSV.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleInputChange = (event) => {
    handleFileSelection(event.target.files?.[0]);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      handleFileSelection(file);
    }
  };

  const handleExtractText = async () => {
    if (!selectedFile) {
      setFileError('Please choose a file before extraction.');
      return;
    }

    setLoading(true);
    setFileError('');
    setSuccessMessage('');
    setVerificationReport(null);

    try {
      const extension = getFileExtension(selectedFile.name);
      let rows = [];

      if (extension === 'csv') {
        const rawCsv = await readFileAsText(selectedFile);
        rows = parseUploadedCsv(rawCsv, verificationType);
      } else {
        const rawText = await extractTextFromFile(selectedFile);
        rows = verificationType === 'quranic_text'
          ? parseExtractedArabicText(rawText)
          : parseExtractedText(rawText);
      }

      if (!rows.length) {
        throw new Error(
          verificationType === 'quranic_text'
            ? 'No extractable Quranic Arabic text found. Use CSV with columns surah_number, ayah_number, arabic_text, or a TXT file with lines like "Surah 102" then "1 <arabic text>".'
            : 'No extractable Quranic translation found in the document.',
        );
      }

      const csv = buildCsv(rows, verificationType);
      setExtractedRows(rows);
      setCsvContent(csv);
      setSuccessMessage('Extraction completed successfully.');
      setActiveStep(3);
    } catch (error) {
      setFileError(error?.message || 'Unable to extract text from the document.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!extractedRows.length) {
      setFileError('No extracted rows to verify. Please extract text first.');
      return;
    }

    setLoading(true);
    setFileError('');
    setSuccessMessage('');

    try {
      const response = await axios.post(config.verifyEndpoint, {
        filename: selectedFile?.name || 'uploaded-document',
        rows: extractedRows,
      });

      if (!response.data?.success) {
        throw new Error(response.data?.message || 'Verification failed.');
      }

      setVerificationReport(response.data.report);
      setSuccessMessage(config.verifySuccess);
      setActiveStep(4);
    } catch (error) {
      setFileError(error.response?.data?.message || error.message || 'Verification request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!verificationReport) return;

    setDownloadingPdf(true);
    setFileError('');

    try {
      const response = await axios.post(
        config.pdfEndpoint,
        { report: verificationReport },
        { responseType: 'blob' },
      );

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      const baseName = (selectedFile?.name || 'verification').replace(/\.[^.]+$/, '');
      link.download = `${baseName}-${config.csvSuffix}-verification-report.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      setFileError('Failed to download PDF report.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const downloadCsv = () => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    const baseName = selectedFile
      ? `${selectedFile.name.split('.').slice(0, -1).join('.') || 'extracted'}`
      : 'extracted';
    link.download = `${baseName}-${config.csvSuffix}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getRowContent = (row) => row[config.contentField] || row.translation || row.arabic_text || '';

  const renderStepIndicator = () => {
    const steps = [
      { num: 1, title: 'Choose Type', subtitle: 'Translation or text' },
      { num: 2, title: 'Upload Document', subtitle: 'PDF, DOCX or TXT' },
      { num: 3, title: 'Extract Text', subtitle: 'Generate CSV' },
      { num: 4, title: config.stepVerifyTitle, subtitle: 'Compare with reference' },
      { num: 5, title: 'Generate Report', subtitle: 'View and download' },
    ];

    return (
      <div className="step-flow">
        {steps.map((step) => (
          <div
            key={step.num}
            className={`step-card ${
              activeStep === step.num ? 'active' : activeStep > step.num ? 'completed' : ''
            }`}
          >
            <div className={`step-circle ${
              activeStep === step.num ? 'active' : activeStep > step.num ? 'completed' : ''
            }`}
            >
              {step.num}
            </div>
            <div className="step-card-title">{step.title}</div>
            <div className="step-card-subtitle">{step.subtitle}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderChooseTypeStep = () => (
    <div className="verify-stage-card">
      <h3>Choose Verification Type</h3>
      <p className="stage-description">
        Select whether you want to verify a Quranic translation or the Quranic Arabic text.
      </p>

      <div className="verification-type-grid">
        <button
          type="button"
          className={`verification-type-card ${verificationType === 'translation' ? 'selected' : ''}`}
          onClick={() => handleSelectType('translation')}
        >
          <h4>Verify Translation</h4>
          <p>
            Compare uploaded translations (e.g. Bahasa Melayu, English) against approved translation sources.
          </p>
        </button>
        <button
          type="button"
          className={`verification-type-card ${verificationType === 'quranic_text' ? 'selected' : ''}`}
          onClick={() => handleSelectType('quranic_text')}
        >
          <h4>Verify Quranic Text</h4>
          <p>
            Compare uploaded Arabic Quranic text against the trusted reference repository verse by verse.
          </p>
        </button>
      </div>
    </div>
  );

  const renderUploadStep = () => (
    <div className="verify-stage-card">
      <h3>Upload Document</h3>
      <p className="stage-description">{config.uploadDescription}</p>

      <div className="reference-info-banner">
        Verification type: <strong>{config.label}</strong>
        {verificationType === 'quranic_text' && (
          <span>
            {' '}— Recommended: upload a CSV with columns <code>surah_number</code>, <code>ayah_number</code>, <code>arabic_text</code>.
          </span>
        )}
      </div>

      <div className="file-drop-area">
        <label
          htmlFor="verify-file-input"
          className={`file-dropzone ${selectedFile ? 'file-selected' : ''} ${dragActive ? 'drag-active' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div>
            <strong>Drag & drop a file here</strong>
            <p>PDF, DOCX, TXT, or CSV</p>
          </div>
          <input
            id="verify-file-input"
            type="file"
            accept=".pdf,.docx,.txt,.csv"
            onChange={handleInputChange}
            hidden
          />
        </label>
        {selectedFile && (
          <div className="file-summary file-summary-row">
            <div>
              <p><strong>Selected file:</strong> {fileSummary.name}</p>
              <p>{fileSummary.type} · {fileSummary.size}</p>
            </div>
            <button
              type="button"
              className="btn btn-secondary btn-sm btn-danger-icon"
              onClick={removeSelectedFile}
              aria-label="Remove file"
              title="Remove file"
            >
              ✕
            </button>
          </div>
        )}
        {fileError && <div className="alert alert-danger">{fileError}</div>}
        <div className="csv-actions-row">
          <button type="button" className="btn btn-secondary" onClick={() => { setActiveStep(1); setVerificationType(null); }}>
            ← Back to Choose Type
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleExtractText}
            disabled={!selectedFile || loading}
          >
            {loading ? 'Extracting...' : 'Extract Text →'}
          </button>
        </div>
      </div>
    </div>
  );

  const renderExtractStep = () => (
    <div className="verify-stage-card extract-stage">
      <div className="stage-top-row">
        <div>
          <h3>{config.extractTitle}</h3>
          <p className="stage-description">{config.extractDescription}</p>
        </div>
        {successMessage && <div className="alert alert-success">{successMessage}</div>}
      </div>

      {selectedFile && (
        <div className="file-summary-banner">
          <p><strong>File:</strong> {fileSummary.name}</p>
          <p>{fileSummary.type} · {fileSummary.size} · {extractedRows.length} rows extracted</p>
        </div>
      )}

      <div className="table-preview-wrapper">
        <table className="csv-preview-table">
          <thead>
            <tr>
              <th>Surah</th>
              <th>Ayah</th>
              <th>{config.contentColumn}</th>
            </tr>
          </thead>
          <tbody>
            {extractedRows.slice(0, 10).map((row, index) => (
              <tr key={`${row.surah_number}-${row.ayah_number}-${index}`}>
                <td>{row.surah_number || '-'}</td>
                <td>{row.ayah_number || '-'}</td>
                <td className={verificationType === 'quranic_text' ? 'arabic-cell' : ''}>
                  {getRowContent(row)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {extractedRows.length > 10 && (
          <p className="stage-description">Showing first 10 of {extractedRows.length} rows.</p>
        )}
      </div>

      {fileError && <div className="alert alert-danger">{fileError}</div>}

      <div className="csv-actions-row">
        <button type="button" className="btn btn-secondary" onClick={() => setActiveStep(2)}>
          ← Back to Upload
        </button>
        <div className="csv-actions">
          <button type="button" className="btn btn-secondary" onClick={downloadCsv} disabled={!csvContent}>
            Download CSV
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleVerify}
            disabled={loading || !extractedRows.length}
          >
            {loading ? 'Verifying...' : `${config.verifyButton} →`}
          </button>
        </div>
      </div>
    </div>
  );

  const renderVerificationStep = () => {
    const summary = verificationReport?.summary || {};
    const status = summary.verification_status || 'unknown';

    return (
      <div className="verify-stage-card">
        <div className="stage-top-row">
          <div>
            <h3>Verification Results</h3>
            <p className="stage-description">
              Comparison of extracted {config.label.toLowerCase()} against the approved reference repository.
            </p>
          </div>
          {successMessage && <div className="alert alert-success">{successMessage}</div>}
        </div>

        <div className="reference-info-banner">
          Reference source: {verificationReport?.document?.reference_source || config.referenceLabel}
          {' '}({verificationReport?.document?.reference_ayah_count || 0} ayahs in database)
        </div>

        <div className={`verification-status-banner ${status}`}>
          <span>Overall Status: {STATUS_LABELS[status] || status}</span>
          <span>Accuracy: {summary.accuracy_percentage ?? 0}%</span>
        </div>

        <div className="verification-summary-grid">
          <div className="summary-stat-card">
            <div className="stat-value">{summary.total_uploaded_rows ?? 0}</div>
            <div className="stat-label">Uploaded Rows</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.exact_matches ?? 0}</div>
            <div className="stat-label">Exact Matches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.partial_matches ?? 0}</div>
            <div className="stat-label">Partial Matches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.mismatches ?? 0}</div>
            <div className="stat-label">Mismatches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.reference_not_found ?? 0}</div>
            <div className="stat-label">No Reference</div>
          </div>
        </div>

        <div className="verification-filter-row">
          {[
            { key: 'all', label: 'All' },
            { key: 'mismatches', label: 'Mismatches Only' },
            { key: 'accurate', label: 'Accurate' },
            { key: 'partially_accurate', label: 'Partial' },
            { key: 'inaccurate', label: 'Inaccurate' },
          ].map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={`filter-chip ${resultFilter === key ? 'active' : ''}`}
              onClick={() => setResultFilter(key)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="table-preview-wrapper">
          <table className="csv-preview-table">
            <thead>
              <tr>
                <th>Surah</th>
                <th>Ayah</th>
                <th>Status</th>
                <th>Similarity</th>
                <th>Uploaded</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {filteredDetails.slice(0, 50).map((row, index) => (
                <tr key={`${row.surah_number}-${row.ayah_number}-${index}`}>
                  <td>{row.surah_number}</td>
                  <td>{row.ayah_number}</td>
                  <td>
                    <span className={`status-badge ${row.status}`}>
                      {STATUS_LABELS[row.status] || row.status}
                    </span>
                  </td>
                  <td>
                    {row.similarity_percentage ?? 0}%
                    <div className="similarity-bar">
                      <div
                        className={`similarity-bar-fill ${
                          row.similarity_percentage >= 98 ? 'high' : row.similarity_percentage >= 70 ? 'medium' : 'low'
                        }`}
                        style={{ width: `${Math.min(row.similarity_percentage || 0, 100)}%` }}
                      />
                    </div>
                  </td>
                  <td className={verificationType === 'quranic_text' ? 'arabic-cell' : ''}>
                    {truncateText(row.uploaded_text, 120)}
                  </td>
                  <td className={verificationType === 'quranic_text' ? 'arabic-cell' : ''}>
                    {truncateText(row.reference_text, 120) || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredDetails.length > 50 && (
            <p className="stage-description">Showing first 50 of {filteredDetails.length} results.</p>
          )}
        </div>

        {fileError && <div className="alert alert-danger">{fileError}</div>}

        <div className="report-actions-row">
          <button type="button" className="btn btn-secondary" onClick={() => setActiveStep(3)}>
            ← Back to Extract
          </button>
          <button type="button" className="btn btn-primary" onClick={() => setActiveStep(5)}>
            View Full Report →
          </button>
        </div>
      </div>
    );
  };

  const renderReportStep = () => {
    const summary = verificationReport?.summary || {};
    const status = summary.verification_status || 'unknown';
    const mismatchDetails = (verificationReport?.details || []).filter((d) => d.status !== 'accurate');

    return (
      <div className="verify-stage-card">
        <div className="stage-top-row">
          <div>
            <h3>Verification Report</h3>
            <p className="stage-description">
              Full {config.label.toLowerCase()} verification report with document details, accuracy, and mismatches.
            </p>
          </div>
        </div>

        <div className="file-summary-banner">
          <p><strong>Document:</strong> {verificationReport?.document?.filename || 'N/A'}</p>
          <p><strong>Type:</strong> {config.label}</p>
          <p><strong>Generated:</strong> {formatDate(verificationReport?.generated_at)}</p>
          <p><strong>Total Rows:</strong> {verificationReport?.document?.total_rows ?? 0}</p>
        </div>

        <div className={`verification-status-banner ${status}`}>
          <span>Verification Status: {STATUS_LABELS[status] || status}</span>
          <span>Accuracy: {summary.accuracy_percentage ?? 0}%</span>
        </div>

        <div className="verification-summary-grid">
          <div className="summary-stat-card">
            <div className="stat-value">{summary.exact_matches ?? 0}</div>
            <div className="stat-label">Exact Matches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.partial_matches ?? 0}</div>
            <div className="stat-label">Partial Matches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.mismatches ?? 0}</div>
            <div className="stat-label">Mismatches</div>
          </div>
          <div className="summary-stat-card">
            <div className="stat-value">{summary.reference_not_found ?? 0}</div>
            <div className="stat-label">No Reference Found</div>
          </div>
        </div>

        <h4 style={{ marginBottom: '0.75rem' }}>Mismatch Details</h4>
        {mismatchDetails.length === 0 ? (
          <div className="reference-info-banner">All compared rows matched the approved reference.</div>
        ) : (
          mismatchDetails.slice(0, 20).map((item, index) => (
            <div key={`mismatch-${index}`} className="translation-result-card">
              <div className="translation-result-meta">
                <span>Surah {item.surah_number}, Ayah {item.ayah_number}</span>
                <span className={`status-badge ${item.status}`}>
                  {STATUS_LABELS[item.status] || item.status}
                </span>
                <span>{item.similarity_percentage ?? 0}% similar</span>
              </div>
              <p className={verificationType === 'quranic_text' ? 'arabic-cell' : ''}>
                <strong>Uploaded:</strong> {item.uploaded_text}
              </p>
              {item.reference_text && (
                <p className={verificationType === 'quranic_text' ? 'arabic-cell' : ''}>
                  <strong>Reference:</strong> {item.reference_text}
                </p>
              )}
              {item.message && <p><em>{item.message}</em></p>}
            </div>
          ))
        )}
        {mismatchDetails.length > 20 && (
          <p className="stage-description">
            Showing first 20 of {mismatchDetails.length} mismatches. Download PDF for full report.
          </p>
        )}

        {fileError && <div className="alert alert-danger">{fileError}</div>}

        <div className="report-actions-row">
          <button type="button" className="btn btn-secondary" onClick={() => setActiveStep(4)}>
            ← Back to Results
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
          >
            {downloadingPdf ? 'Generating PDF...' : 'Download PDF Report'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={resetPage}>
            Verify Another Document
          </button>
        </div>
      </div>
    );
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 1: return renderChooseTypeStep();
      case 2: return renderUploadStep();
      case 3: return renderExtractStep();
      case 4: return renderVerificationStep();
      case 5: return renderReportStep();
      default: return renderChooseTypeStep();
    }
  };

  return (
    <div className="verify-document-page">
      <div className="verify-document-card">
        <div className="verify-header-row">
          <button type="button" className="btn btn-secondary btn-back" onClick={() => navigate('/dashboard')}>
            ← Back to Dashboard
          </button>
          <div className="verify-header">
            <h1>Verify Document</h1>
            <p>
              Choose verification type, upload your document, extract content, and verify against trusted references.
            </p>
          </div>
        </div>

        {renderStepIndicator()}
        {renderStepContent()}
      </div>
    </div>
  );
};

const truncateText = (text, maxLen) => {
  if (!text) return '';
  return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
};

const formatDate = (iso) => {
  if (!iso) return 'N/A';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
};

const getFileExtension = (fileName) => fileName.split('.').pop().toLowerCase();

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const extractTextFromFile = async (file) => {
  const extension = getFileExtension(file.name);
  if (extension === 'txt') return readFileAsText(file);
  if (extension === 'docx') {
    const arrayBuffer = await readFileAsArrayBuffer(file);
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value || '';
  }
  if (extension === 'pdf') {
    const arrayBuffer = await readFileAsArrayBuffer(file);
    return extractTextFromPdf(arrayBuffer);
  }
  throw new Error('Unsupported file type.');
};

const extractTextFromPdf = async (arrayBuffer) => {
  const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
  const pdf = await loadingTask.promise;
  let text = '';
  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();
    const pageText = content.items.map((item) => item.str).join(' ');
    text += `${pageText}\n`;
  }
  return text;
};

const readFileAsText = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result.toString());
  reader.onerror = () => reject(new Error('Unable to read the file.'));
  reader.readAsText(file, 'UTF-8');
});

const readFileAsArrayBuffer = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => resolve(reader.result);
  reader.onerror = () => reject(new Error('Unable to read the file.'));
  reader.readAsArrayBuffer(file);
});

const cleanTranslation = (text) => {
  if (!text) return '';
  return text
    .replace(/\[\d+\]/g, '')
    .replace(/\(\d+\)/g, '')
    .replace(/[†‡*]+/g, '')
    .replace(/\s+/g, ' ')
    .trim();
};

const cleanArabicText = (text) => {
  if (!text) return '';
  return text.replace(/\s+/g, ' ').trim();
};

const hasArabicChars = (text) => /[\u0600-\u06FF]/.test(text);

const normalizeWesternDigits = (text) => {
  if (!text) return '';
  return text
    .replace(/[٠-٩]/g, (ch) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(ch)))
    .replace(/[۰-۹]/g, (ch) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(ch)));
};

const parseCsvLine = (line) => {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
};

const parseUploadedCsv = (csvText, verificationType) => {
  const contentField = verificationType === 'quranic_text' ? 'arabic_text' : 'translation';
  const lines = csvText.replace(/^\uFEFF/, '').split(/\r?\n/).filter((line) => line.trim());
  if (lines.length < 2) return [];

  const headers = parseCsvLine(lines[0]).map((h) => h.trim().toLowerCase());
  const surahIdx = headers.findIndex((h) => h === 'surah_number' || h === 'surah');
  const ayahIdx = headers.findIndex((h) => h === 'ayah_number' || h === 'ayah');
  const contentIdx = headers.findIndex((h) => (
    h === contentField || h === 'translation' || h === 'arabic_text' || h === 'text'
  ));

  if (surahIdx === -1 || ayahIdx === -1 || contentIdx === -1) {
    return [];
  }

  const rows = [];
  for (let i = 1; i < lines.length; i += 1) {
    const cols = parseCsvLine(lines[i]);
    if (!cols.length) continue;

    const surah = normalizeWesternDigits(cols[surahIdx] || '').trim();
    const ayah = normalizeWesternDigits(cols[ayahIdx] || '').trim();
    const content = (cols[contentIdx] || '').trim();

    if (!surah || !ayah || !content) continue;
    if (verificationType === 'quranic_text' && !hasArabicChars(content)) continue;

    rows.push({
      surah_number: surah,
      ayah_number: ayah,
      [contentField]: content,
    });
  }

  return rows;
};

const parseStructuredRows = (rawText, contentField, cleanFn) => {
  const lines = rawText
    .replace(/\uFEFF/g, '')
    .replace(/\u00A0/g, ' ')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const rows = [];
  let currentSurah = '';

  lines.forEach((line) => {
    let text = normalizeWesternDigits(line.replace(/\s{2,}/g, ' ').trim());
    if (!text) return;

    const surahOnlyMatch = text.match(/^(?:Surah|Sura|سورة)\s*(\d+)$/i);
    if (surahOnlyMatch) {
      currentSurah = surahOnlyMatch[1];
      return;
    }

    let surah = '';
    let ayah = '';
    let content = '';

    const patterns = [
      /^(?:Surah\s*(\d+)\s*)?(?:Ayah|Ayat|Verse|آية)\s*(\d+)\s*[:.-]?\s*(.*)$/i,
      /^(\d+)\s*[:.]\s*(\d+)\s*(.*)$/,
      /^(\d+)\s+(\d+)\s+(.*)$/,
      /^(\d+)[\.)]\s*(.*)$/,
      /^(\d+)\s*[-–]\s*(.*)$/,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        if (pattern === patterns[0]) {
          surah = match[1] || currentSurah;
          ayah = match[2];
          content = match[3];
        } else if (pattern === patterns[1] || pattern === patterns[2]) {
          surah = match[1];
          ayah = match[2];
          content = match[3];
          currentSurah = surah;
        } else {
          ayah = match[1];
          content = match[2];
          surah = currentSurah;
        }
        break;
      }
    }

    if (!content) {
      const singleNumberMatch = text.match(/^(\d+)\s+(.+)$/);
      if (singleNumberMatch) {
        ayah = singleNumberMatch[1];
        content = singleNumberMatch[2];
        surah = currentSurah;
      }
    }

    const cleanedText = cleanFn(content || text);
    if (!cleanedText) return;

    if (contentField === 'arabic_text' && !hasArabicChars(cleanedText)) {
      return;
    }

    if (!ayah && !surah && contentField === 'arabic_text') {
      return;
    }

    const isContinuation = !ayah && !surah && rows.length > 0
      && !/^(Surah|Sura|Ayah|Ayat|Verse)\b/i.test(text);
    if (isContinuation) {
      const last = rows[rows.length - 1];
      last[contentField] = cleanFn(`${last[contentField]} ${cleanedText}`);
      return;
    }

    rows.push({
      surah_number: surah || '',
      ayah_number: ayah || '',
      [contentField]: cleanedText,
    });
  });

  return rows;
};

const parseExtractedText = (rawText) => parseStructuredRows(rawText, 'translation', cleanTranslation);

const parseExtractedArabicText = (rawText) => parseStructuredRows(rawText, 'arabic_text', cleanArabicText);

const buildCsv = (rows, type) => {
  const contentField = type === 'quranic_text' ? 'arabic_text' : 'translation';
  const header = `surah_number,ayah_number,${contentField}`;
  const lines = rows.map((row) => {
    const content = (row[contentField] || '').replace(/"/g, '""');
    return `${row.surah_number},${row.ayah_number},"${content}"`;
  });
  return [header, ...lines].join('\n');
};

export default VerifyDocumentPlaceholderPage;
