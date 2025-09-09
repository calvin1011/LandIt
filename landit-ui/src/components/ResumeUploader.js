import React, { useState, useCallback } from 'react';
import axios from 'axios';

// Simple SVG Icon Components
const Upload = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
);

const FileText = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
);

const CheckCircle = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const AlertCircle = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const X = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
);

const Eye = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
);

const ResumeUploader = ({ onUploadSuccess }) => {
    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, processing, success, error
    const [progress, setProgress] = useState(0);
    const [errorMessage, setErrorMessage] = useState('');
    const [extractedData, setExtractedData] = useState(null);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    }, []);

    const handleFileInput = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (selectedFile) => {
        // Validate file type
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];

        if (!allowedTypes.includes(selectedFile.type)) {
            setErrorMessage('Please upload a PDF, DOCX, or TXT file');
            setUploadStatus('idle');
            return;
        }

        // Validate file size (5MB limit)
        if (selectedFile.size > 5 * 1024 * 1024) {
            setErrorMessage('File size must be less than 5MB');
            setUploadStatus('idle');
            return;
        }

        setFile(selectedFile);
        setErrorMessage('');
        uploadFile(selectedFile);
    };

    const uploadFile = async (fileToUpload) => {
        setUploadStatus('uploading');
        setProgress(0);

        try {
            // For text files, read content and send to hybrid text endpoint
            if (fileToUpload.type === 'text/plain') {
                const text = await readFileAsText(fileToUpload);
                await processTextDirectly(text);
                return;
            }

            // For PDF/DOCX files, use the optimized file upload endpoint
            const formData = new FormData();
            formData.append('file', fileToUpload);

            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            // Call the optimized file upload endpoint
            const response = await axios.post('http://localhost:8000/parse-resume-file', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                },
                timeout: 30000
            });

            clearInterval(progressInterval);
            setProgress(100);
            setUploadStatus('processing');

            // Format the response
            const processedData = formatApiResponse(response.data);

            // Simulate processing delay for better UX
            setTimeout(() => {
                setExtractedData(processedData);
                setUploadStatus('success');
                onUploadSuccess(processedData);
            }, 1500);

        } catch (error) {
            setUploadStatus('error');
            handleUploadError(error);
        }
    };

    const readFileAsText = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    };

    const processTextDirectly = async (text) => {
        setUploadStatus('processing');
        setProgress(50);

        try {
            // Always use hybrid processing for best results
            const response = await axios.post('http://localhost:8000/parse-resume-hybrid', {
                text: text,
                analysis_level: "full",
                include_suggestions: true
            }, {
                headers: { 'Content-Type': 'application/json' },
                timeout: 30000
            });

            setProgress(100);
            const processedData = formatApiResponse(response.data);

            setTimeout(() => {
                setExtractedData(processedData);
                setUploadStatus('success');
                onUploadSuccess(processedData);
            }, 1000);

        } catch (error) {
            setUploadStatus('error');
            handleUploadError(error);
        }
    };

    const handleUploadError = (error) => {
        console.error('Upload error:', error);

        if (error.code === 'ECONNREFUSED') {
            setErrorMessage('Cannot connect to processing server. Please ensure the server is running.');
        } else if (error.response?.status === 400) {
            setErrorMessage(error.response.data?.detail || 'Invalid file format or content');
        } else if (error.response?.status === 500) {
            setErrorMessage('Server processing error. Please try again or contact support.');
        } else if (error.code === 'ECONNABORTED') {
            setErrorMessage('Request timed out. File might be too large or complex.');
        } else {
            setErrorMessage('Failed to process resume. Please try again.');
        }
    };

    const formatApiResponse = (data) => {
        console.log('Raw API response:', data);

        let entities = [];

        // Handle different response formats
        if (data.entities && Array.isArray(data.entities)) {
            entities = data.entities;
        } else if (data.method === 'hybrid_extraction' && data.entities) {
            entities = data.entities;
        } else {
            console.error('No entities found in response:', data);
            return [];
        }

        // Convert to frontend format
        const converted = entities.map(entity => ({
            type: entity.label,
            value: entity.text,
            confidence: entity.confidence || 0.8,
            section: entity.section,
            source: entity.source || 'ai'
        }));

        console.log('Converted data:', converted);
        return converted;
    };

    const resetUpload = () => {
        setFile(null);
        setUploadStatus('idle');
        setProgress(0);
        setErrorMessage('');
        setExtractedData(null);
    };

    const getFileIcon = () => {
        if (!file) return <FileText style={{ width: '3rem', height: '3rem', color: '#9ca3af' }} />;

        if (file.type === 'application/pdf') {
            return (
                <div style={{
                    width: '2rem',
                    height: '2rem',
                    backgroundColor: '#ef4444',
                    color: 'white',
                    borderRadius: '0.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                }}>
                    PDF
                </div>
            );
        }

        if (file.type === 'text/plain') {
            return (
                <div style={{
                    width: '2rem',
                    height: '2rem',
                    backgroundColor: '#10b981',
                    color: 'white',
                    borderRadius: '0.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 'bold'
                }}>
                    TXT
                </div>
            );
        }

        return (
            <div style={{
                width: '2rem',
                height: '2rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '0.25rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 'bold'
            }}>
                DOCX
            </div>
        );
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            padding: '40px',
            border: '1px solid rgba(255,255,255,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
        }}>
            <div style={{ marginBottom: '30px', textAlign: 'center' }}>
                <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                    Upload Your Resume
                </h2>
                <p style={{ color: '#6b7280', fontSize: '16px', margin: 0 }}>
                    Upload your resume and let our AI extract and organize your information automatically.
                </p>
            </div>

            {/* Upload Area */}
            {uploadStatus === 'idle' && (
                <div
                    style={{
                        border: dragActive ? '2px dashed #6366f1' : '2px dashed #d1d5db',
                        backgroundColor: dragActive ? '#eff6ff' : '#f8fafc',
                        borderRadius: '16px',
                        padding: '3rem',
                        transition: 'all 0.3s',
                        cursor: 'pointer',
                        textAlign: 'center'
                    }}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <Upload style={{
                        width: '4rem',
                        height: '4rem',
                        color: dragActive ? '#6366f1' : '#9ca3af',
                        margin: '0 auto 1.5rem auto'
                    }} />
                    <div>
                        <p style={{ fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                            {dragActive ? 'Drop your resume here' : 'Drag and drop your resume'}
                        </p>
                        <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '20px' }}>or</p>
                        <label style={{
                            display: 'inline-block',
                            backgroundColor: '#6366f1',
                            color: 'white',
                            padding: '12px 24px',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            fontSize: '16px',
                            fontWeight: '500'
                        }}
                        onMouseOver={(e) => e.target.style.backgroundColor = '#4f46e5'}
                        onMouseOut={(e) => e.target.style.backgroundColor = '#6366f1'}
                        >
                            Choose File
                            <input
                                type="file"
                                style={{ display: 'none' }}
                                accept=".pdf,.docx,.txt"
                                onChange={handleFileInput}
                            />
                        </label>
                    </div>
                    <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '20px', margin: 0 }}>
                        Supports PDF, DOCX, TXT • Max file size: 5MB
                    </p>
                </div>
            )}

            {/* File Info & Progress */}
            {file && uploadStatus !== 'idle' && (
                <div style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '16px',
                    padding: '24px'
                }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            {getFileIcon()}
                            <div>
                                <p style={{ fontWeight: '600', color: '#1f2937', margin: 0, fontSize: '16px' }}>{file.name}</p>
                                <p style={{ fontSize: '14px', color: '#6b7280', margin: 0, marginTop: '4px' }}>
                                    {formatFileSize(file.size)} • AI Processing
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={resetUpload}
                            style={{
                                color: '#9ca3af',
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                transition: 'color 0.15s',
                                padding: '4px'
                            }}
                            onMouseOver={(e) => e.target.style.color = '#4b5563'}
                            onMouseOut={(e) => e.target.style.color = '#9ca3af'}
                        >
                            <X style={{ width: '20px', height: '20px' }} />
                        </button>
                    </div>

                    {/* Progress Bar */}
                    {(uploadStatus === 'uploading' || uploadStatus === 'processing') && (
                        <div style={{ marginBottom: '20px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                                <span>
                                    {uploadStatus === 'uploading' ? 'Uploading...' : 'Processing with AI...'}
                                </span>
                                <span>{uploadStatus === 'uploading' ? `${progress}%` : ''}</span>
                            </div>
                            <div style={{
                                width: '100%',
                                backgroundColor: '#e5e7eb',
                                borderRadius: '9999px',
                                height: '8px'
                            }}>
                                <div
                                    style={{
                                        height: '8px',
                                        borderRadius: '9999px',
                                        backgroundColor: uploadStatus === 'uploading' ? '#6366f1' : '#10b981',
                                        width: uploadStatus === 'uploading' ? `${progress}%` : '100%',
                                        transition: 'all 0.3s',
                                        animation: uploadStatus === 'processing' ? 'pulse 2s infinite' : 'none'
                                    }}
                                ></div>
                            </div>
                        </div>
                    )}

                    {/* Status Messages */}
                    {uploadStatus === 'success' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#059669', marginBottom: '20px' }}>
                            <CheckCircle style={{ width: '20px', height: '20px' }} />
                            <span style={{ fontWeight: '500', fontSize: '16px' }}>
                                Resume processed successfully!
                            </span>
                        </div>
                    )}

                    {uploadStatus === 'error' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626', marginBottom: '20px' }}>
                            <AlertCircle style={{ width: '20px', height: '20px' }} />
                            <span style={{ fontWeight: '500', fontSize: '16px' }}>{errorMessage}</span>
                        </div>
                    )}

                    {/* Quick Preview */}
                    {uploadStatus === 'success' && extractedData && (
                        <div style={{
                            marginTop: '20px',
                            padding: '20px',
                            backgroundColor: '#f0f9ff',
                            borderRadius: '12px',
                            border: '1px solid #bfdbfe'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                                <h4 style={{ fontWeight: '600', color: '#1f2937', margin: 0, fontSize: '16px' }}>Extracted Information</h4>
                                <Eye style={{ width: '16px', height: '16px', color: '#9ca3af' }} />
                            </div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>
                                <p style={{ margin: 0, marginBottom: '12px' }}>
                                    Found {extractedData.length} data points including names, skills, experience, and more
                                </p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {extractedData.slice(0, 3).map((item, index) => (
                                        <span key={index} style={{
                                            display: 'inline-block',
                                            backgroundColor: '#dbeafe',
                                            color: '#1e40af',
                                            padding: '4px 8px',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            fontWeight: '500'
                                        }}>
                                            {item.type}: {item.value.length > 20 ? item.value.substring(0, 20) + '...' : item.value}
                                        </span>
                                    ))}
                                    {extractedData.length > 3 && (
                                        <span style={{
                                            display: 'inline-block',
                                            backgroundColor: '#f3f4f6',
                                            color: '#4b5563',
                                            padding: '4px 8px',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            fontWeight: '500'
                                        }}>
                                            +{extractedData.length - 3} more
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Error Display */}
            {errorMessage && uploadStatus === 'idle' && (
                <div style={{
                    marginTop: '20px',
                    padding: '16px',
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '12px'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626' }}>
                        <AlertCircle style={{ width: '20px', height: '20px' }} />
                        <span style={{ fontWeight: '500' }}>{errorMessage}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResumeUploader;