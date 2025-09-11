import React, { useState, useEffect } from 'react';

// Icon Components
const Briefcase = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2V8a2 2 0 012-2V6z" />
    </svg>
);

const MapPin = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
);

const DollarSign = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
    </svg>
);

const ThumbsUp = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2v0a2 2 0 00-2 2v6.5L7 20" />
    </svg>
);

const ThumbsDown = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2v0a2 2 0 002-2v-6.5L17 4" />
    </svg>
);

const ExternalLink = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
);

const Refresh = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
);

const JobRecommendations = ({ userEmail }) => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (userEmail) {
            fetchRecommendations();
        }
    }, [userEmail]);

    const fetchRecommendations = async () => {
        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:8000/jobs/find-matches', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_email: userEmail,
                    top_k: 10,
                    min_similarity: 0.3
                })
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Please upload your resume first to get job recommendations.');
                } else {
                    throw new Error('Failed to fetch job recommendations. Please try again.');
                }
            }

            const data = await response.json();
            setRecommendations(data.matches || []);
        } catch (err) {
            console.error('Error fetching recommendations:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async (recommendationId, feedbackType, rating = null) => {
        try {
            const response = await fetch('http://localhost:8000/jobs/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_email: userEmail,
                    recommendation_id: recommendationId,
                    feedback_type: feedbackType,
                    overall_rating: rating,
                    action_taken: feedbackType
                })
            });

            if (response.ok) {
                // Update local state to reflect feedback
                setRecommendations(prev => prev.map(rec =>
                    rec.recommendation_id === recommendationId
                        ? { ...rec, userFeedback: feedbackType }
                        : rec
                ));
            }
        } catch (err) {
            console.error('Error submitting feedback:', err);
        }
    };

    const getMatchQualityColor = (score) => {
        if (score >= 0.8) return '#10b981'; // Green
        if (score >= 0.6) return '#f59e0b'; // Yellow
        return '#ef4444'; // Red
    };

    const getMatchQualityLabel = (score) => {
        if (score >= 0.8) return 'Excellent Match';
        if (score >= 0.6) return 'Good Match';
        return 'Fair Match';
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
                <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔍</div>
                <div style={{ fontSize: '18px', color: '#6b7280' }}>
                    Finding perfect job matches for you...
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
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '25px'
            }}>
                <div>
                    <h2 style={{
                        margin: 0,
                        fontSize: '24px',
                        fontWeight: '600',
                        color: '#1f2937',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                    }}>
                        🎯 Job Recommendations
                    </h2>
                    <p style={{
                        margin: 0,
                        fontSize: '14px',
                        color: '#6b7280',
                        marginTop: '5px'
                    }}>
                        AI-powered job matches based on your resume
                    </p>
                </div>

                <button
                    onClick={fetchRecommendations}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        background: '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.background = '#4f46e5'}
                    onMouseOut={(e) => e.target.style.background = '#6366f1'}
                >
                    <Refresh style={{ width: '14px', height: '14px' }} />
                    Refresh
                </button>
            </div>

            {/* Error Message */}
            {error && (
                <div style={{
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '12px',
                    padding: '16px',
                    marginBottom: '20px',
                    color: '#dc2626',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    <span>⚠️</span>
                    <span>{error}</span>
                </div>
            )}

            {/* Recommendations List */}
            {recommendations.length === 0 && !error ? (
                <div style={{
                    textAlign: 'center',
                    padding: '40px',
                    color: '#6b7280'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>💼</div>
                    <h3 style={{ margin: 0, marginBottom: '10px' }}>No job recommendations yet</h3>
                    <p style={{ margin: 0 }}>Upload your resume to get personalized job matches</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {recommendations.map((job) => (
                        <div
                            key={job.job_id}
                            style={{
                                background: '#f8fafc',
                                border: '1px solid #e2e8f0',
                                borderRadius: '16px',
                                padding: '24px',
                                transition: 'all 0.2s'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            {/* Job Header */}
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'flex-start',
                                marginBottom: '16px'
                            }}>
                                <div style={{ flex: 1 }}>
                                    <h3 style={{
                                        margin: 0,
                                        fontSize: '20px',
                                        fontWeight: '600',
                                        color: '#1f2937',
                                        marginBottom: '4px'
                                    }}>
                                        {job.title}
                                    </h3>
                                    <p style={{
                                        margin: 0,
                                        fontSize: '16px',
                                        color: '#6366f1',
                                        fontWeight: '500'
                                    }}>
                                        {job.company}
                                    </p>
                                </div>

                                {/* Match Quality Badge */}
                                <div style={{
                                    background: getMatchQualityColor(job.overall_score),
                                    color: 'white',
                                    padding: '6px 12px',
                                    borderRadius: '20px',
                                    fontSize: '12px',
                                    fontWeight: '600',
                                    textAlign: 'center'
                                }}>
                                    {Math.round(job.overall_score * 100)}% Match
                                </div>
                            </div>

                            {/* Job Details */}
                            <div style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: '16px',
                                marginBottom: '16px'
                            }}>
                                {job.location && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <MapPin style={{ width: '16px', height: '16px', color: '#6b7280' }} />
                                        <span style={{ fontSize: '14px', color: '#6b7280' }}>
                                            {job.location}
                                            {job.remote_allowed && ' (Remote OK)'}
                                        </span>
                                    </div>
                                )}

                                {(job.salary_min || job.salary_max) && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <DollarSign style={{ width: '16px', height: '16px', color: '#6b7280' }} />
                                        <span style={{ fontSize: '14px', color: '#6b7280' }}>
                                            {job.salary_min && job.salary_max
                                                ? `${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}`
                                                : job.salary_min
                                                    ? `${job.salary_min.toLocaleString()}+`
                                                    : `Up to ${job.salary_max.toLocaleString()}`
                                            }
                                        </span>
                                    </div>
                                )}

                                {job.experience_level && (
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Briefcase style={{ width: '16px', height: '16px', color: '#6b7280' }} />
                                        <span style={{ fontSize: '14px', color: '#6b7280' }}>
                                            {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)} Level
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Match Explanation */}
                            <div style={{
                                background: 'rgba(99, 102, 241, 0.05)',
                                border: '1px solid rgba(99, 102, 241, 0.1)',
                                borderRadius: '8px',
                                padding: '12px',
                                marginBottom: '16px'
                            }}>
                                <p style={{
                                    margin: 0,
                                    fontSize: '14px',
                                    color: '#4f46e5',
                                    fontWeight: '500'
                                }}>
                                    {job.match_explanation}
                                </p>
                            </div>

                            {/* Skills Match */}
                            {job.skill_matches && job.skill_matches.length > 0 && (
                                <div style={{ marginBottom: '16px' }}>
                                    <h4 style={{
                                        margin: 0,
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        color: '#1f2937',
                                        marginBottom: '8px'
                                    }}>
                                        Matching Skills:
                                    </h4>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                        {job.skill_matches.slice(0, 5).map((skill, index) => (
                                            <span
                                                key={index}
                                                style={{
                                                    background: '#dcfce7',
                                                    color: '#166534',
                                                    padding: '4px 8px',
                                                    borderRadius: '12px',
                                                    fontSize: '12px',
                                                    fontWeight: '500'
                                                }}
                                            >
                                                {skill}
                                            </span>
                                        ))}
                                        {job.skill_matches.length > 5 && (
                                            <span style={{
                                                color: '#6b7280',
                                                fontSize: '12px',
                                                alignSelf: 'center'
                                            }}>
                                                +{job.skill_matches.length - 5} more
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Skill Gaps */}
                            {job.skill_gaps && job.skill_gaps.length > 0 && (
                                <div style={{ marginBottom: '16px' }}>
                                    <h4 style={{
                                        margin: 0,
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        color: '#1f2937',
                                        marginBottom: '8px'
                                    }}>
                                        Skills to develop:
                                    </h4>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                        {job.skill_gaps.slice(0, 3).map((skill, index) => (
                                            <span
                                                key={index}
                                                style={{
                                                    background: '#fef3c7',
                                                    color: '#92400e',
                                                    padding: '4px 8px',
                                                    borderRadius: '12px',
                                                    fontSize: '12px',
                                                    fontWeight: '500'
                                                }}
                                            >
                                                {skill}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                paddingTop: '16px',
                                borderTop: '1px solid #e5e7eb'
                            }}>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        onClick={() => handleFeedback(job.recommendation_id, 'interested', 5)}
                                        disabled={job.userFeedback === 'interested'}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '6px 12px',
                                            background: job.userFeedback === 'interested' ? '#10b981' : '#f3f4f6',
                                            color: job.userFeedback === 'interested' ? 'white' : '#374151',
                                            border: 'none',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            fontWeight: '500',
                                            cursor: job.userFeedback === 'interested' ? 'default' : 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseOver={(e) => {
                                            if (job.userFeedback !== 'interested') {
                                                e.target.style.background = '#e5e7eb';
                                            }
                                        }}
                                        onMouseOut={(e) => {
                                            if (job.userFeedback !== 'interested') {
                                                e.target.style.background = '#f3f4f6';
                                            }
                                        }}
                                    >
                                        <ThumbsUp style={{ width: '14px', height: '14px' }} />
                                        Interested
                                    </button>

                                    <button
                                        onClick={() => handleFeedback(job.recommendation_id, 'not_interested', 2)}
                                        disabled={job.userFeedback === 'not_interested'}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '4px',
                                            padding: '6px 12px',
                                            background: job.userFeedback === 'not_interested' ? '#ef4444' : '#f3f4f6',
                                            color: job.userFeedback === 'not_interested' ? 'white' : '#374151',
                                            border: 'none',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            fontWeight: '500',
                                            cursor: job.userFeedback === 'not_interested' ? 'default' : 'pointer',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseOver={(e) => {
                                            if (job.userFeedback !== 'not_interested') {
                                                e.target.style.background = '#e5e7eb';
                                            }
                                        }}
                                        onMouseOut={(e) => {
                                            if (job.userFeedback !== 'not_interested') {
                                                e.target.style.background = '#f3f4f6';
                                            }
                                        }}
                                    >
                                        <ThumbsDown style={{ width: '14px', height: '14px' }} />
                                        Not Interested
                                    </button>
                                </div>

                                <button
                                    onClick={() => handleFeedback(job.recommendation_id, 'applied')}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        padding: '8px 16px',
                                        background: '#6366f1',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                    onMouseOver={(e) => e.target.style.background = '#4f46e5'}
                                    onMouseOut={(e) => e.target.style.background = '#6366f1'}
                                >
                                    <ExternalLink style={{ width: '14px', height: '14px' }} />
                                    Apply Now
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );}

export default JobRecommendations;