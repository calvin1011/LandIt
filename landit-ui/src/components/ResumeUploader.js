import React, { useState, useCallback } from 'react';

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

const Search = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
);

const ResumeUploader = ({ onUploadSuccess, userEmail, jobDescriptionText }) => {
    const [dragActive, setDragActive] = useState(false);
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle');
    const [progress, setProgress] = useState(0);
    const [errorMessage, setErrorMessage] = useState('');
    const [resumeStored, setResumeStored] = useState(false);
    const [autoFindJobs, setAutoFindJobs] = useState(true);

    const handleUploadError = useCallback((error) => {
        console.error('Upload error:', error);
        let msg = 'Failed to process resume. Please try again.';
        if (error.message.includes('ECONNREFUSED')) {
            msg = 'Cannot connect to processing server. Please ensure the server is running.';
        } else if (error.message.includes('400')) {
            msg = 'Invalid file format or content';
        } else if (error.message.includes('500')) {
            msg = 'Server processing error. Please try again or contact support.';
        } else if (error.message.includes('timeout')) {
            msg = 'Request timed out. File might be too large or complex.';
        }
        setErrorMessage(msg);
    }, []);

    const storeResumeForMatching = useCallback(async (resumeData) => {
        try {
            setProgress(95);
            const structuredData = resumeData.structured_data || resumeData;

            const storeResponse = await fetch('http://localhost:8000/store-resume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: userEmail,
                    resume_data: resumeData,
                    structured_data: structuredData
                })
            });

            if (!storeResponse.ok) {
                const errorBody = await storeResponse.json();
                throw new Error(errorBody.detail || 'Failed to store resume for matching.');
            }

            const result = await storeResponse.json();
            if (result.success) {
                setResumeStored(true);
            } else {
                throw new Error(result.message || 'An unknown error occurred while storing the resume.');
            }
        } catch (error) {
            console.error('Failed to store resume for job matching:', error);
            throw error;
        }
    }, [userEmail]);

    const readFileAsText = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    };

    const processTextDirectly = useCallback(async (text) => {
        setUploadStatus('processing');
        setProgress(50);
        try {
            const response = await fetch('http://localhost:8000/parse-resume', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    analysis_level: "full",
                    include_suggestions: true
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            setProgress(100);

            if (userEmail && autoFindJobs) {
                await storeResumeForMatching(data);
            }

            setTimeout(() => {
                setUploadStatus('success');
                onUploadSuccess();
            }, 1000);

        } catch (error) {
            setUploadStatus('error');
            handleUploadError(error);
        }
    }, [userEmail, autoFindJobs, storeResumeForMatching, onUploadSuccess, handleUploadError]);

    const uploadFile = useCallback(async (fileToUpload) => {
        setUploadStatus('uploading');
        setProgress(0);
        try {
            if (fileToUpload.type === 'text/plain') {
                const text = await readFileAsText(fileToUpload);
                await processTextDirectly(text);
                return;
            }

            const formData = new FormData();
            formData.append('file', fileToUpload);

            if (jobDescriptionText) {
                formData.append('job_description_text', jobDescriptionText);
            }

            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            const response = await fetch('http://localhost:8000/parse-resume-file', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            clearInterval(progressInterval);
            setProgress(100);
            setUploadStatus('processing');

            if (userEmail && autoFindJobs) {
                await storeResumeForMatching(data);
            }

            setTimeout(() => {
                setUploadStatus('success');
                onUploadSuccess(data);
            }, 1500);
        } catch (error) {
            setUploadStatus('error');
            handleUploadError(error);
        }
    }, [userEmail, autoFindJobs, processTextDirectly, storeResumeForMatching, onUploadSuccess, handleUploadError]);

    const handleFile = useCallback((selectedFile) => {
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
        if (selectedFile.size > 10 * 1024 * 1024) {
            setErrorMessage('File size must be less than 10MB');
            setUploadStatus('idle');
            return;
        }
        setFile(selectedFile);
        setErrorMessage('');
        uploadFile(selectedFile);
    }, [uploadFile]);

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
    }, [handleFile]);

    const handleFileInput = (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const resetUpload = () => {
        setFile(null);
        setUploadStatus('idle');
        setProgress(0);
        setErrorMessage('');
        setResumeStored(false);
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
             {/* Job Matching Option */}
            {userEmail && uploadStatus === 'idle' && (
                <div style={{
                    background: '#f0f9ff',
                    border: '1px solid #bfdbfe',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '20px'
                }}>
                    <label style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        color: '#1e40af',
                        cursor: 'pointer'
                    }}>
                        <input
                            type="checkbox"
                            checked={autoFindJobs}
                            onChange={(e) => setAutoFindJobs(e.target.checked)}
                            style={{ accentColor: '#6366f1' }}
                        />
                        Automatically find job matches after uploading
                    </label>
                    <p style={{
                        margin: '8px 0 0 24px',
                        fontSize: '12px',
                        color: '#6b7280'
                    }}>
                        We'll analyze your resume and show personalized job recommendations
                    </p>
                </div>
            )}
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
                        Supports PDF, DOCX, TXT • Max file size: 10MB
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
                                    {autoFindJobs && ' + Job Matching'}
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
                                    {uploadStatus === 'uploading' ? 'Uploading...' :
                                     progress >= 95 && autoFindJobs ? 'Storing for job matching...' : 'Processing with AI...'}
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
                        <div style={{ marginBottom: '20px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#059669', marginBottom: '8px' }}>
                                <CheckCircle style={{ width: '20px', height: '20px' }} />
                                <span style={{ fontWeight: '500', fontSize: '16px' }}>
                                    Resume processed successfully!
                                </span>
                            </div>
                            {resumeStored && autoFindJobs && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6366f1' }}>
                                    <Search style={{ width: '16px', height: '16px' }} />
                                    <span style={{ fontSize: '14px' }}>
                                        Ready for job matching - check recommendations below
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {uploadStatus === 'error' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626', marginBottom: '20px' }}>
                            <AlertCircle style={{ width: '20px', height: '20px' }} />
                            <span style={{ fontWeight: '500', fontSize: '16px' }}>{errorMessage}</span>
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