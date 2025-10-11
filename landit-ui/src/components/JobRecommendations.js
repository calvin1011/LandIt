import React, { useState, useEffect, useCallback } from 'react';
import { Briefcase, MapPin, DollarSign, ExternalLink, RefreshCw, Bookmark, TrendingUp, ArrowRight, X, CheckCircle, BrainCircuit } from 'lucide-react';

// Reusable component for the match score display
const MatchScore = ({ score }) => {
    const scorePercentage = Math.round(score * 100);
    const circumference = 2 * Math.PI * 40; // 2 * pi * radius
    const strokeDashoffset = circumference - (score * circumference);

    const getScoreColor = () => {
        if (scorePercentage >= 90) return '#34D399'; // Green
        if (scorePercentage >= 70) return '#60A5FA'; // Blue
        return '#FBBF24'; // Amber
    };

    return (
        <div style={{
            width: '180px',
            flexShrink: 0,
            background: '#1F2937', // Dark background
            borderRadius: '0 16px 16px 0',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            color: 'white'
        }}>
            <div style={{ position: 'relative', width: '100px', height: '100px', marginBottom: '12px' }}>
                <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                    <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke="#374151"
                        strokeWidth="8"
                        fill="transparent"
                    />
                    <circle
                        cx="50"
                        cy="50"
                        r="40"
                        stroke={getScoreColor()}
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dashoffset 0.5s ease-out' }}
                    />
                </svg>
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontSize: '24px',
                    fontWeight: 'bold',
                    color: getScoreColor()
                }}>
                    {scorePercentage}<span style={{fontSize: '14px'}}>%</span>
                </div>
            </div>
            <div style={{ fontWeight: '600', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Strong Match
            </div>
        </div>
    );
};


const JobCard = ({ job, userEmail, onGenerateLearningPlan }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [saved, setSaved] = useState(false);

    const handleSaveJob = async () => {
        if (saved) return;
        try {
            const response = await fetch('http://localhost:8000/jobs/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: userEmail, job_id: job.job_id }),
            });
            if (response.ok) setSaved(true);
        } catch (err) {
            console.error('Error saving job:', err);
        }
    };

    return (
        <div style={{
            background: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            transition: 'all 0.2s ease-in-out',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
            display: 'flex',
            overflow: 'hidden',
        }}
        onMouseOver={(e) => { e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -4px rgba(0, 0, 0, 0.07)'; e.currentTarget.style.transform = 'translateY(-2px)';}}
        onMouseOut={(e) => { e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)'; e.currentTarget.style.transform = 'translateY(0)';}}
        >
            <div style={{ padding: '24px', flex: 1 }}>
                {/* Job Header */}
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '8px',
                        background: '#f1f5f9',
                        marginRight: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        color: '#475569'
                    }}>
                        {job.company.charAt(0)}
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>{job.title}</h3>
                        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>{job.company}</p>
                    </div>
                </div>

                {/* Job Metadata */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
                    {job.location && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <MapPin style={{ width: '16px' }} /> {job.location}
                        </span>
                    )}
                    {job.experience_level && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Briefcase style={{ width: '16px' }} /> {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)}
                        </span>
                    )}
                    {(job.salary_min || job.salary_max) && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <DollarSign style={{ width: '16px' }} />
                            {job.salary_min && job.salary_max ? `$${job.salary_min/1000}k - $${job.salary_max/1000}k` : (job.salary_min ? `$${job.salary_min/1000}k+` : `Up to $${job.salary_max/1000}k`)}
                        </span>
                    )}
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                     <button
                        onClick={() => window.open(job.job_url, '_blank')}
                        style={{
                            padding: '8px 16px',
                            background: '#34D399',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            fontSize: '14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}>
                        Apply Now <ArrowRight size={16} />
                    </button>
                    <button
                        onClick={() => onGenerateLearningPlan(job)}
                        style={{
                            padding: '8px 16px',
                            background: 'transparent',
                            color: '#6366f1',
                            border: '1px solid #e0e7ff',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: 500,
                            fontSize: '14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}>
                        <BrainCircuit size={16} /> Get Learning Plan
                    </button>
                    <button
                        onClick={handleSaveJob}
                        style={{
                            padding: '8px 12px',
                            background: 'transparent',
                            color: saved ? '#6366f1' : '#64748b',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: saved ? 'default': 'pointer',
                            fontSize: '14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                        }}>
                        <Bookmark size={16} fill={saved ? '#6366f1' : 'none'} />
                    </button>
                </div>
            </div>

            {/* Match Score */}
            <MatchScore score={job.overall_score} />
        </div>
    );
};

const JobRecommendations = ({ userEmail, onNavigateToLearning, initialJobs = [] }) => {
    const [recommendations, setRecommendations] = useState(initialJobs);
    const [loading, setLoading] = useState(initialJobs.length === 0);
    const [error, setError] = useState('');
    const [shownJobIds, setShownJobIds] = useState(new Set());
    const [hasMore, setHasMore] = useState(true);
    const [offset, setOffset] = useState(0);

    const fetchRecommendations = useCallback(async (reset = false) => {
        setLoading(true);
        setError('');
        if (reset) {
            setRecommendations([]);
            setShownJobIds(new Set());
            setOffset(0);
        }
        try {
            const response = await fetch('http://localhost:8000/jobs/find-matches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: userEmail,
                    top_k: 10,
                    offset: reset ? 0 : offset,
                    exclude_job_ids: reset ? [] : Array.from(shownJobIds),
                })
            });
            if (!response.ok) throw new Error('Failed to fetch recommendations.');
            const data = await response.json();
            const newMatches = data.matches || [];

            setRecommendations(prev => reset ? newMatches : [...prev, ...newMatches]);
            setShownJobIds(prev => new Set([...prev, ...newMatches.map(j => j.job_id)]));
            setHasMore(data.has_more || false);
            setOffset(data.next_offset || 0);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [userEmail, offset, shownJobIds]);

    useEffect(() => {
        if (userEmail && initialJobs.length === 0) {
            fetchRecommendations(true);
        } else if (initialJobs.length > 0) {
            setShownJobIds(new Set(initialJobs.map(j => j.job_id)));
        }
    }, [userEmail, initialJobs, fetchRecommendations]);

    if (loading && recommendations.length === 0) {
        return <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>Finding job matches...</div>;
    }

    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '20px',
            padding: '30px',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937' }}>Job Recommendations</h2>
                    <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#6b7280' }}>
                        AI-powered matches based on your resume
                    </p>
                </div>
                <button
                    onClick={() => fetchRecommendations(true)}
                    disabled={loading}
                    style={{ padding: '8px 16px', background: '#6366f1', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                    {loading ? 'Refreshing...' : 'Get Fresh Jobs'}
                </button>
            </div>

            {error && <div style={{ color: '#dc2626', marginBottom: '20px' }}>Error: {error}</div>}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {recommendations.map(job => (
                    <JobCard key={job.job_id} job={job} userEmail={userEmail} onGenerateLearningPlan={onNavigateToLearning} />
                ))}
            </div>

            {hasMore && (
                <div style={{ textAlign: 'center', marginTop: '30px' }}>
                    <button
                        onClick={() => fetchRecommendations(false)}
                        disabled={loading}
                        style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', borderRadius: '8px', cursor: 'pointer', fontWeight: 500 }}>
                        {loading ? 'Loading...' : 'Show More Jobs'}
                    </button>
                </div>
            )}
        </div>
    );
};

export default JobRecommendations;