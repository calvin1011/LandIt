import React, { useState, useEffect } from 'react';

const AdminPanel = () => {
    const [importing, setImporting] = useState(false);
    const [testing, setTesting] = useState(false);
    const [stats, setStats] = useState(null);
    const [importResult, setImportResult] = useState(null);
    const [testResult, setTestResult] = useState(null);
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

    const runAllImports = async () => {
        setImporting(true);
        setImportResult(null);
        try {
            const response = await fetch('http://localhost:8000/admin/import-all-jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ max_jobs_per_source: 25 })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const result = await response.json();
            setImportResult(result);
            await fetchStats(); // Refresh stats after import
        } catch (error) {
            setImportResult({ status: 'error', summaries: { error: { error: error.message } } });
        } finally {
            setImporting(false);
        }
    };

    const testAllImporters = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const response = await fetch('http://localhost:8000/admin/test-all-importers', { method: 'POST' });

            // Check if the response was successful. If not, parse the error and throw it.
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Server responded with status ${response.status}`);
            }

            const result = await response.json();
            setTestResult(result);
        } catch (error) {
            // The catch block will now handle network errors AND server errors correctly.
            setTestResult({ general_error: { status: 'error', message: error.message } });
        } finally {
            setTesting(false);
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
                     Admin Panel
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
                         Job Database Statistics
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
                </div>
            )}

            {/* Actions Section */}
            <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
                <button onClick={testAllImporters} disabled={testing} style={{ flex: 1, padding: '12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    {testing ? 'Testing...' : 'Test All Importers'}
                </button>
                <button onClick={runAllImports} disabled={importing} style={{ flex: 1, padding: '12px', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                    {importing ? 'Importing...' : 'Import All Jobs'}
                </button>
            </div>

            {/* Test Results */}
            {testResult && (
                <div style={{ marginBottom: '20px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px' }}>
                    <h3 style={{ margin: '0 0 15px 0' }}>Test Results</h3>
                    {Object.entries(testResult).map(([key, value]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #e2e8f0' }}>
                            <span style={{ textTransform: 'capitalize', fontWeight: '500' }}>{key.replace('_', ' ')}</span>
                            <span style={{ color: value.status === 'ok' ? '#16a34a' : '#dc2626', textAlign: 'right' }}>
                                {value.status === 'ok' ? '✔ OK' : `✖ ${value.message}`}
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* Import Results */}
            {importResult && (
                <div style={{ marginBottom: '20px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px' }}>
                     <h3 style={{ margin: '0 0 15px 0' }}>Import Summary</h3>
                     {importResult.summaries && Object.entries(importResult.summaries).map(([key, summary]) => (
                         <div key={key} style={{ marginBottom: '10px' }}>
                             <h4 style={{ textTransform: 'capitalize', margin: '0 0 5px 0' }}>{key}</h4>
                             {summary.error ? (
                                 <p style={{ color: '#dc2626' }}>Error: {summary.error}</p>
                             ) : (
                                 <p>Imported: {summary.imported || 0}, Duplicates: {summary.duplicates || summary.duplicate_jobs || 0}, Failed: {summary.failed || summary.failed_imports || 0}</p>
                             )}
                         </div>
                     ))}
                </div>
            )}

        </div>
    );
};

export default AdminPanel;