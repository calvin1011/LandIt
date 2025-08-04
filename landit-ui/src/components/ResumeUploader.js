import React, { useState, useCallback } from 'react';
import axios from 'axios';

// Simple SVG Icon Components
const Upload = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
    </svg>
);

const FileText = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
);

const CheckCircle = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const AlertCircle = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const X = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
);

const Eye = ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(selectedFile.type)) {
            setErrorMessage('Please upload a PDF or Word document');
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

        const formData = new FormData();
        formData.append('resume', fileToUpload);

        try {
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

            const response = await axios.post('http://localhost:5001/api/parse-resume', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            clearInterval(progressInterval);
            setProgress(100);
            setUploadStatus('processing');

            // Simulate processing delay for better UX
            setTimeout(() => {
                setExtractedData(response.data.extracted);
                setUploadStatus('success');
                onUploadSuccess(response.data.extracted);
            }, 1500);

        } catch (error) {
            setUploadStatus('error');
            setErrorMessage('Failed to process resume. Please try again.');
            console.error('Upload error:', error);
        }
    };

    const resetUpload = () => {
        setFile(null);
        setUploadStatus('idle');
        setProgress(0);
        setErrorMessage('');
        setExtractedData(null);
    };

    const getFileIcon = () => {
        if (!file) return <FileText style={{ width: '2rem', height: '2rem', color: '#9ca3af' }} />;

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
                DOC
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
        <div style={{ maxWidth: '42rem', margin: '0 auto', padding: '1.5rem' }}>
            <div style={{ marginBottom: '1.5rem' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#111827', marginBottom: '0.5rem' }}>
                    Upload Your Resume
                </h2>
                <p style={{ color: '#4b5563' }}>
                    Upload your resume and let our AI extract and organize your information automatically.
                </p>
            </div>

            {/* Upload Area */}
            {uploadStatus === 'idle' && (
                <div
                    style={{
                        border: dragActive ? '2px dashed #3b82f6' : '2px dashed #d1d5db',
                        backgroundColor: dragActive ? '#eff6ff' : 'transparent',
                        borderRadius: '0.5rem',
                        padding: '2rem',
                        transition: 'all 0.2s',
                        cursor: 'pointer'
                    }}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <div style={{ textAlign: 'center' }}>
                        <Upload style={{
                            width: '3rem',
                            height: '3rem',
                            color: dragActive ? '#3b82f6' : '#9ca3af',
                            margin: '0 auto'
                        }} />
                        <div style={{ marginTop: '1rem' }}>
                            <p style={{ fontSize: '1.125rem', fontWeight: '500', color: '#111827' }}>
                                {dragActive ? 'Drop your resume here' : 'Drag and drop your resume'}
                            </p>
                            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>or</p>
                            <label style={{
                                marginTop: '0.5rem',
                                display: 'inline-block',
                                backgroundColor: '#2563eb',
                                color: 'white',
                                padding: '0.5rem 1rem',
                                borderRadius: '0.375rem',
                                cursor: 'pointer',
                                transition: 'background-color 0.15s'
                            }}
                            onMouseOver={(e) => e.target.style.backgroundColor = '#1d4ed8'}
                            onMouseOut={(e) => e.target.style.backgroundColor = '#2563eb'}
                            >
                                Browse Files
                                <input
                                    type="file"
                                    style={{ display: 'none' }}
                                    accept=".pdf,.doc,.docx"
                                    onChange={handleFileInput}
                                />
                            </label>
                        </div>
                        <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '1rem' }}>
                            Supports PDF, DOC, DOCX • Max file size: 5MB
                        </p>
                    </div>
                </div>
            )}

            {/* File Info & Progress */}
            {file && uploadStatus !== 'idle' && (
                <div style={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '0.5rem',
                    padding: '1.5rem',
                    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            {getFileIcon()}
                            <div>
                                <p style={{ fontWeight: '500', color: '#111827' }}>{file.name}</p>
                                <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>{formatFileSize(file.size)}</p>
                            </div>
                        </div>
                        <button
                            onClick={resetUpload}
                            style={{
                                color: '#9ca3af',
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                transition: 'color 0.15s'
                            }}
                            onMouseOver={(e) => e.target.style.color = '#4b5563'}
                            onMouseOut={(e) => e.target.style.color = '#9ca3af'}
                        >
                            <X style={{ width: '1.25rem', height: '1.25rem' }} />
                        </button>
                    </div>

                    {/* Progress Bar */}
                    {(uploadStatus === 'uploading' || uploadStatus === 'processing') && (
                        <div style={{ marginBottom: '1rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', color: '#4b5563', marginBottom: '0.5rem' }}>
                                <span>
                                    {uploadStatus === 'uploading' ? 'Uploading...' : 'Processing with AI...'}
                                </span>
                                <span>{uploadStatus === 'uploading' ? `${progress}%` : ''}</span>
                            </div>
                            <div style={{
                                width: '100%',
                                backgroundColor: '#e5e7eb',
                                borderRadius: '9999px',
                                height: '0.5rem'
                            }}>
                                <div
                                    style={{
                                        height: '0.5rem',
                                        borderRadius: '9999px',
                                        backgroundColor: uploadStatus === 'uploading' ? '#3b82f6' : '#10b981',
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#059669', marginBottom: '1rem' }}>
                            <CheckCircle style={{ width: '1.25rem', height: '1.25rem' }} />
                            <span style={{ fontWeight: '500' }}>Resume processed successfully!</span>
                        </div>
                    )}

                    {uploadStatus === 'error' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#dc2626', marginBottom: '1rem' }}>
                            <AlertCircle style={{ width: '1.25rem', height: '1.25rem' }} />
                            <span style={{ fontWeight: '500' }}>{errorMessage}</span>
                        </div>
                    )}

                    {/* Quick Preview */}
                    {uploadStatus === 'success' && extractedData && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '1rem',
                            backgroundColor: '#f9fafb',
                            borderRadius: '0.5rem'
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                <h4 style={{ fontWeight: '500', color: '#111827' }}>Extracted Information</h4>
                                <Eye style={{ width: '1rem', height: '1rem', color: '#9ca3af' }} />
                            </div>
                            <div style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                                <p>Found {extractedData.length} data points including names, skills, experience, and more.</p>
                                <div style={{ marginTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {extractedData.slice(0, 3).map((item, index) => (
                                        <span key={index} style={{
                                            display: 'inline-block',
                                            backgroundColor: '#dbeafe',
                                            color: '#1e40af',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '0.25rem',
                                            fontSize: '0.75rem'
                                        }}>
                                            {item.type}: {item.value.length > 20 ? item.value.substring(0, 20) + '...' : item.value}
                                        </span>
                                    ))}
                                    {extractedData.length > 3 && (
                                        <span style={{
                                            display: 'inline-block',
                                            backgroundColor: '#f3f4f6',
                                            color: '#4b5563',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '0.25rem',
                                            fontSize: '0.75rem'
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
                    marginTop: '1rem',
                    padding: '1rem',
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '0.5rem'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#dc2626' }}>
                        <AlertCircle style={{ width: '1.25rem', height: '1.25rem' }} />
                        <span style={{ fontWeight: '500' }}>{errorMessage}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResumeUploader;