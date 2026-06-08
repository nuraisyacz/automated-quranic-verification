import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import mammoth from 'mammoth';
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import pdfWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

const allowedFiles = ['pdf', 'docx', 'txt'];

const VerifyDocumentPlaceholderPage = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(1);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [extractedRows, setExtractedRows] = useState([]);
  const [csvContent, setCsvContent] = useState('');

  const fileSummary = useMemo(() => {
    if (!selectedFile) return null;
    return {
      name: selectedFile.name,
      type: selectedFile.type || selectedFile.name.split('.').pop().toUpperCase(),
      size: formatFileSize(selectedFile.size),
    };
  }, [selectedFile]);

  const resetPage = () => {
    setActiveStep(1);
    setSelectedFile(null);
    setFileError('');
    setLoading(false);
    setSuccessMessage('');
    setExtractedRows([]);
    setCsvContent('');
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setFileError('');
    setSuccessMessage('');
    setCsvContent('');
    setExtractedRows([]);
  };

  const handleFileSelection = (file) => {
    setSuccessMessage('');
    setExtractedRows([]);
    setCsvContent('');
    setFileError('');

    if (!file) {
      setSelectedFile(null);
      return;
    }

    const extension = getFileExtension(file.name);
    if (!allowedFiles.includes(extension)) {
      setFileError('Unsupported file type. Please upload PDF, DOCX, or TXT.');
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

    try {
      const rawText = await extractTextFromFile(selectedFile);
      const rows = parseExtractedText(rawText);

      if (!rows.length) {
        throw new Error('No extractable Quranic text found in the document.');
      }

      const csv = buildCsv(rows);
      setExtractedRows(rows);
      setCsvContent(csv);
      setSuccessMessage('Extraction completed successfully.');
      setActiveStep(2);
    } catch (error) {
      setFileError(error?.message || 'Unable to extract text from the document.');
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = () => {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = selectedFile ? `${selectedFile.name.split('.').slice(0, -1).join('.') || 'extracted'}-translation.csv` : 'extracted-translation.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderStepContent = () => {
    if (activeStep === 1) {
      return (
        <div className="verify-stage-card">
          <h3>Upload Document</h3>
          <p className="stage-description">
            Upload a Quranic translation file in PDF, DOCX or TXT format. Then click Extract Text to continue.
          </p>
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
                <p>or choose a file from your computer</p>
              </div>
              <input
                id="verify-file-input"
                type="file"
                accept=".pdf,.docx,.txt"
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
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M9 3V4H4V6H5V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V6H20V4H15V3H9ZM7 6H17V19H7V6ZM9 8V17H11V8H9ZM13 8V17H15V8H13Z" fill="currentColor" />
                    <path d="M10 1H14V2H10V1Z" fill="currentColor" />
                  </svg>
                </button>
              </div>
            )}
            {fileError && <div className="alert alert-danger">{fileError}</div>}
            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={handleExtractText}
              disabled={!selectedFile || loading}
            >
              {loading ? 'Extracting...' : 'Extract Text'}
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="verify-stage-card extract-stage">
        <div className="stage-top-row">
          <div>
            <h3>Extracted CSV Preview</h3>
            <p className="stage-description">
              Review the extracted Quranic translation rows below. Download or open the CSV when ready.
            </p>
          </div>
          {successMessage && <div className="alert alert-success">{successMessage}</div>}
        </div>

        {selectedFile && (
          <div className="file-summary-banner">
            <p><strong>File:</strong> {fileSummary.name}</p>
            <p>{fileSummary.type} · {fileSummary.size}</p>
          </div>
        )}

        <div className="table-preview-wrapper">
          <table className="csv-preview-table">
            <thead>
              <tr>
                <th>Surah</th>
                <th>Ayah</th>
                <th>Translation</th>
              </tr>
            </thead>
            <tbody>
              {extractedRows.slice(0, 10).map((row, index) => (
                <tr key={`${row.surah_number}-${row.ayah_number}-${index}`}>
                  <td>{row.surah_number || '-'}</td>
                  <td>{row.ayah_number || '-'}</td>
                  <td>{row.translation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="csv-actions-row">
          <button type="button" className="btn btn-secondary" onClick={() => setActiveStep(1)}>
            ← Back to Upload
          </button>
          <div className="csv-actions">
            <button type="button" className="btn btn-primary" onClick={downloadCsv} disabled={!csvContent}>
              Download Extracted CSV
            </button>
          </div>
        </div>

        <div className="notice-card">
          <h4>Step 3</h4>
          <p>Translation verification is currently under development.</p>
        </div>
      </div>
    );
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
            <p>Upload a Quranic translation document and extract its content before verification.</p>
          </div>
        </div>

        <div className="step-flow">
          <div className={`step-card ${activeStep > 1 ? 'completed' : 'active'}`}>
            <div className={`step-circle ${activeStep > 1 ? 'completed' : 'active'}`}>1</div>
            <div className="step-card-title">Upload Document</div>
            <div className="step-card-subtitle">Select PDF, DOCX or TXT</div>
          </div>
          <div className={`step-card ${activeStep === 2 ? 'active' : activeStep > 2 ? 'completed' : ''}`}>
            <div className={`step-circle ${activeStep === 2 ? 'active' : activeStep > 2 ? 'completed' : ''}`}>2</div>
            <div className="step-card-title">Extract Text</div>
            <div className="step-card-subtitle">Generate structured CSV</div>
          </div>
          <div className="step-card disabled">
            <div className="step-circle disabled">3</div>
            <div className="step-card-title">Verify Translation</div>
            <div className="step-card-subtitle">Feature under development</div>
          </div>
          <div className="step-card disabled">
            <div className="step-circle disabled">4</div>
            <div className="step-card-title">Generate Report</div>
            <div className="step-card-subtitle">Feature under development</div>
          </div>
        </div>

        {renderStepContent()}
      </div>
    </div>
  );
};

const getFileExtension = (fileName) => {
  return fileName.split('.').pop().toLowerCase();
};

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const extractTextFromFile = async (file) => {
  const extension = getFileExtension(file.name);
  if (extension === 'txt') {
    return readFileAsText(file);
  }
  if (extension === 'docx') {
    const arrayBuffer = await readFileAsArrayBuffer(file);
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value || '';
  }
  if (extension === 'pdf') {
    const arrayBuffer = await readFileAsArrayBuffer(file);
    return await extractTextFromPdf(arrayBuffer);
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

const parseExtractedText = (rawText) => {
  const lines = rawText
    .replace(/\u00A0/g, ' ')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  const rows = [];
  let currentSurah = '';

  lines.forEach((line) => {
    let text = line.replace(/\s{2,}/g, ' ').trim();
    if (!text) return;

    const surahOnlyMatch = text.match(/^(?:Surah|Sura)\s*(\d+)$/i);
    if (surahOnlyMatch) {
      currentSurah = surahOnlyMatch[1];
      return;
    }

    let surah = '';
    let ayah = '';
    let translation = '';

    const patterns = [
      /^(?:Surah\s*(\d+)\s*)?(?:Ayah|Ayat|Verse)\s*(\d+)\s*[:.-]?\s*(.*)$/i,
      /^(\d+)\s*[:.]\s*(\d+)\s*(.*)$/,
      /^(\d+)\s+(\d+)\s+(.*)$/,
      /^(\d+)[\.)]\s*(.*)$/,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        if (pattern === patterns[0]) {
          surah = match[1] || currentSurah;
          ayah = match[2];
          translation = match[3];
        } else if (pattern === patterns[1] || pattern === patterns[2]) {
          surah = match[1];
          ayah = match[2];
          translation = match[3];
          currentSurah = surah;
        } else {
          ayah = match[1];
          translation = match[2];
          surah = currentSurah;
        }
        break;
      }
    }

    if (!translation) {
      const singleNumberMatch = text.match(/^(\d+)\s+(.*)$/);
      if (singleNumberMatch) {
        ayah = singleNumberMatch[1];
        translation = singleNumberMatch[2];
        surah = currentSurah;
      }
    }

    const cleanedText = cleanTranslation(translation || text);
    if (!cleanedText) return;

    const isContinuation = !ayah && !surah && rows.length > 0 && !/^(Surah|Sura|Ayah|Ayat|Verse)\b/i.test(text);
    if (isContinuation) {
      rows[rows.length - 1].translation += ` ${cleanedText}`;
      rows[rows.length - 1].translation = cleanTranslation(rows[rows.length - 1].translation);
      return;
    }

    rows.push({
      surah_number: surah || '',
      ayah_number: ayah || '',
      translation: cleanedText,
    });
  });

  return rows;
};

const buildCsv = (rows) => {
  const header = 'surah_number,ayah_number,translation';
  const lines = rows.map((row) => {
    const translation = row.translation.replace(/"/g, '""');
    return `${row.surah_number},${row.ayah_number},"${translation}"`;
  });
  return [header, ...lines].join('\n');
};

export default VerifyDocumentPlaceholderPage;
