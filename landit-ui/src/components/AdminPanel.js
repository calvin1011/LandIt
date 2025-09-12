import React, { useState, useEffect } from 'react';

const AdminPanel = () => {
    const [importing, setImporting] = useState(false);
    const [stats, setStats] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const response = await fetch('http://localhost:8000/admin/jobs/stats');
            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        } finally {
            setLoading(false);
        }
    };

    const importJobs = async () => {
    setImporting(true);
    setImportResult(null);

    // Placeholder for a user's email. You would get this from user authentication.
    const userEmail = "testuser@example.com";

    try {
        const response = await fetch('http://localhost:8000/admin/import-jobs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                max_jobs: 30  // Import up to 30 jobs per category
            })
        });

        if (response.ok) {
            const result = await response.json();
            setImportResult(result);
            // Refresh stats after import
            await fetchStats();
        } else {
            throw new Error('Import failed');
        }
    } catch (error) {
        console.error('Error importing jobs:', error);
        setImportResult({
            success: false,
            error: error.message
        });
    } finally {
        setImporting(false);
    }
};

const findMatches = async () => {
    try {
        const userEmail = "test@example.com"; // ⚠️ IMPORTANT: Replace with a dynamic user email from your application state

        const response = await fetch('http://localhost:8000/jobs/find-matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_email: userEmail
            })
        });

        if (response.ok) {
            const result = await response.json();
            console.log("Job Matches found:", result.matches);
            alert(`Found ${result.total_found} job matches!`);
            // You can now display these matches in the UI
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to find matches');
        }
    } catch (error) {
        console.error('Error finding job matches:', error);
        alert(`Failed to find job matches: ${error.message}`);
    }
};

    if (loading) {
        return (
            <div style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '20px',
                padding: '40px',
                border: '1px solid rgba(255,255,255,0.2)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                textAlign: 'center'
            }}>
                <div style={{ fontSize: '18px', color: '#6b7280' }}>
                    Loading admin panel...
                </div>
            </div>
        );
    }

    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            padding: '30px',
            border: '1px solid rgba(255,255,255,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
        }}>
            {/* Header */}
            <div style={{ marginBottom: '30px' }}>
                <h2 style={{
                    margin: 0,
                    fontSize: '24px',
                    fontWeight: '600',
                    color: '#1f2937',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                }}>
                    ⚙️ Admin Panel
                </h2>
                <p style={{
                    margin: 0,
                    fontSize: '14px',
                    color: '#6b7280',
                    marginTop: '5px'
                }}>
                    Manage job database and imports
                </p>
            </div>

            {/* Job Statistics */}
            {stats && (
                <div style={{
                    background: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px'
                }}>
                    <h3 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                        📊 Job Database Statistics
                    </h3>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '15px'
                    }}>
                        <div style={{
                            background: '#dbeafe',
                            padding: '15px',
                            borderRadius: '8px',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '24px', fontWeight: '700', color: '#1e40af' }}>
                                {stats.total_jobs}
                            </div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>Total Jobs</div>
                        </div>

                        <div style={{
                            background: '#dcfce7',
                            padding: '15px',
                            borderRadius: '8px',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '24px', fontWeight: '700', color: '#166534' }}>
                                {stats.unique_companies}
                            </div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>Companies</div>
                        </div>

                        <div style={{
                            background: '#fef3c7',
                            padding: '15px',
                            borderRadius: '8px',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '24px', fontWeight: '700', color: '#92400e' }}>
                                {Object.keys(stats.jobs_by_source).length}
                            </div>
                            <div style={{ fontSize: '14px', color: '#6b7280' }}>Data Sources</div>
                        </div>
                    </div>

                    {/* Experience Level Breakdown */}
                    <div style={{ marginTop: '20px' }}>
                        <h4 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
                            Experience Levels:
                        </h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {Object.entries(stats.jobs_by_experience_level).map(([level, count]) => (
                                <span key={level} style={{
                                    background: '#e0e7ff',
                                    color: '#3730a3',
                                    padding: '4px 8px',
                                    borderRadius: '12px',
                                    fontSize: '12px',
                                    fontWeight: '500'
                                }}>
                                    {level}: {count}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Import Section */}
            <div style={{
                background: '#f0f9ff',
                border: '1px solid #bfdbfe',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '20px'
            }}>
                <h3 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                    📥 Import Jobs from The Muse
                </h3>

                <p style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#6b7280' }}>
                    Import real job postings from The Muse API. This will add fresh job opportunities to your database.
                </p>

                <button
                    onClick={importJobs}
                    disabled={importing}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '12px 24px',
                        background: importing ? '#9ca3af' : '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: importing ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        if (!importing) {
                            e.target.style.background = '#4f46e5';
                        }
                    }}
                    onMouseOut={(e) => {
                        if (!importing) {
                            e.target.style.background = '#6366f1';
                        }
                    }}
                >
                    {importing ? (
                        <>
                            <div style={{
                                width: '16px',
                                height: '16px',
                                border: '2px solid transparent',
                                borderTop: '2px solid white',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite'
                            }}></div>
                            Importing Jobs...
                        </>
                    ) : (
                        <>📥 Import Jobs from The Muse</>
                    )}
                </button>
            </div>

            {/* Import Results */}
            {importResult && (
                <div style={{
                    background: importResult.success ? '#f0fdf4' : '#fef2f2',
                    border: `1px solid ${importResult.success ? '#bbf7d0' : '#fecaca'}`,
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px'
                }}>
                    <h3 style={{
                        margin: '0 0 15px 0',
                        fontSize: '18px',
                        fontWeight: '600',
                        color: importResult.success ? '#166534' : '#dc2626'
                    }}>
                        {importResult.success ? '✅ Import Successful!' : '❌ Import Failed'}
                    </h3>

                    {importResult.success ? (
                        <div>
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                                gap: '15px',
                                marginBottom: '15px'
                            }}>
                                <div style={{
                                    background: 'rgba(34, 197, 94, 0.1)',
                                    padding: '10px',
                                    borderRadius: '8px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '20px', fontWeight: '700', color: '#166534' }}>
                                        {importResult.summary.imported}
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Imported</div>
                                </div>

                                <div style={{
                                    background: 'rgba(251, 191, 36, 0.1)',
                                    padding: '10px',
                                    borderRadius: '8px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '20px', fontWeight: '700', color: '#92400e' }}>
                                        {importResult.summary.skipped}
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Skipped</div>
                                </div>

                                <div style={{
                                    background: 'rgba(239, 68, 68, 0.1)',
                                    padding: '10px',
                                    borderRadius: '8px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '20px', fontWeight: '700', color: '#dc2626' }}>
                                        {importResult.summary.errors}
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Errors</div>
                                </div>

                                <div style={{
                                    background: 'rgba(99, 102, 241, 0.1)',
                                    padding: '10px',
                                    borderRadius: '8px',
                                    textAlign: 'center'
                                }}>
                                    <div style={{ fontSize: '20px', fontWeight: '700', color: '#4f46e5' }}>
                                        {importResult.summary.success_rate.toFixed(1)}%
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#6b7280' }}>Success Rate</div>
                                </div>
                            </div>

                            <p style={{
                                margin: 0,
                                fontSize: '14px',
                                color: '#166534'
                            }}>
                                Processing time: {importResult.processing_time.toFixed(2)} seconds
                            </p>
                        </div>
                    ) : (
                        <p style={{
                            margin: 0,
                            fontSize: '14px',
                            color: '#dc2626'
                        }}>
                            Error: {importResult.error}
                        </p>
                    )}
                </div>
            )}

            {/* Instructions */}
            <div style={{
                background: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '12px',
                padding: '20px'
            }}>
                <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: '600', color: '#92400e' }}>
                    💡 How it Works
                </h3>
                <ul style={{
                    margin: 0,
                    paddingLeft: '20px',
                    fontSize: '14px',
                    color: '#6b7280',
                    lineHeight: '1.6'
                }}>
                    <li>Imports real job postings from The Muse API (free, no API key required)</li>
                    <li>Automatically extracts skills, experience levels, and job details</li>
                    <li>Generates AI embeddings for intelligent job matching</li>
                    <li>Stores jobs in your database for user recommendations</li>
                    <li>Categories include: Software Engineer, Data Science, Product Management, Design, etc.</li>
                </ul>
            </div>

            {/* Add some CSS for animations */}
            <style jsx>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
};

export default AdminPanel;