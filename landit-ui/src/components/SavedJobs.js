import React, { useState, useEffect } from 'react';

const Briefcase = ({ style }) => ( <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2V6z" /></svg> );
const MapPin = ({ style }) => ( <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg> );
const DollarSign = ({ style }) => ( <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" /></svg> );
const ExternalLink = ({ style }) => ( <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg> );


const SavedJobs = ({ userEmail }) => {
    const [savedJobs, setSavedJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!userEmail) return;

        const fetchSavedJobs = async () => {
            setLoading(true);
            setError('');
            try {
                const response = await fetch(`http://localhost:8000/jobs/saved/${userEmail}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch saved jobs.');
                }
                const data = await response.json();
                setSavedJobs(data.saved_jobs || []);
            } catch (err) {
                setError(err.message);
                console.error('Error fetching saved jobs:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchSavedJobs();
    }, [userEmail]);

    if (loading) {
        return <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>Loading saved jobs...</div>;
    }

    if (error) {
        return <div style={{ textAlign: 'center', padding: '40px', color: '#dc2626' }}>Error: {error}</div>;
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
            <h2 style={{ margin: '0 0 25px 0', fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>
                💾 Saved Jobs
            </h2>

            {savedJobs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                    You haven't saved any jobs yet.
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {savedJobs.map((job) => (
                        <div key={job.id} style={{
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            borderRadius: '16px',
                            padding: '24px',
                        }}>
                             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: '20px', fontWeight: '600', color: '#1f2937', marginBottom: '4px' }}>
                                        {job.title}
                                    </h3>
                                    <p style={{ margin: 0, fontSize: '16px', color: '#6366f1', fontWeight: '500' }}>
                                        {job.company}
                                    </p>
                                </div>
                                <button
                                    onClick={() => window.open(job.job_url, '_blank')}
                                    style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', background: '#6366f1', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
                                >
                                    <ExternalLink style={{ width: '14px', height: '14px' }} />
                                    Apply
                                </button>
                            </div>
                             <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '14px', color: '#6b7280' }}>
                                {job.location && <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><MapPin style={{ width: '16px' }} /> {job.location}</span>}
                                {(job.salary_min || job.salary_max) && <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><DollarSign style={{ width: '16px' }} /> {job.salary_min} - {job.salary_max}</span>}
                                {job.experience_level && <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Briefcase style={{ width: '16px' }} /> {job.experience_level}</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default SavedJobs;