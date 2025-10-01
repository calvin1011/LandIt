import React, { useState, useEffect, useCallback } from 'react';

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

const Plus = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
);

// new icon for learning/improvement
const TrendingUp = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
);


const BookOpen = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C20.832 18.477 19.246 18 17.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
);

const Clock = ({ style }) => (
    <svg style={style} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);

const SkillsGapAnalysis = ({ job, onGenerateLearningPlan }) => {
    const gapData = job.skill_gaps_detailed || {};
    const analysis = job.gap_analysis || {};

    const getDifficultyColor = (level) => {
        switch(level) {
            case 'high': return '#ef4444';
            case 'medium': return '#f59e0b';
            case 'low': return '#10b981';
            default: return '#6b7280';
        }
    };

    const getTimeColor = (weeks) => {
        if (weeks <= 4) return '#10b981';
        if (weeks <= 8) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <div style={{
            background: 'rgba(99, 102, 241, 0.03)',
            border: '1px solid rgba(99, 102, 241, 0.1)',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '16px'
        }}>
            {/* Gap Analysis Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px'
            }}>
                <h4 style={{
                    margin: 0,
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#4f46e5',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                }}>
                    <TrendingUp style={{ width: '16px', height: '16px' }} />
                    Skills Gap Analysis
                </h4>

                <div style={{
                    background: getDifficultyColor(analysis.difficulty_level),
                    color: 'white',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: '600',
                    textTransform: 'uppercase'
                }}>
                    {analysis.difficulty_level} Priority
                </div>
            </div>

            {/* Summary */}
            <p style={{
                margin: '0 0 12px 0',
                fontSize: '13px',
                color: '#6b7280',
                lineHeight: '1.4'
            }}>
                {job.improvement_summary}
            </p>

            {/* Gap Categories */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {/* Critical Skills */}
                {gapData.critical && gapData.critical.length > 0 && (
                    <div>
                        <span style={{
                            fontSize: '11px',
                            fontWeight: '600',
                            color: '#dc2626',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            Critical ({gapData.critical.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.critical.slice(0, 3).map((skill, index) => (
                                <span
                                    key={index}
                                    style={{
                                        background: '#fef2f2',
                                        color: '#dc2626',
                                        padding: '2px 6px',
                                        borderRadius: '8px',
                                        fontSize: '11px',
                                        fontWeight: '500',
                                        border: '1px solid #fecaca'
                                    }}
                                >
                                    {skill}
                                </span>
                            ))}
                            {gapData.critical.length > 3 && (
                                <span style={{ fontSize: '11px', color: '#6b7280', alignSelf: 'center' }}>
                                    +{gapData.critical.length - 3} more
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Important Skills */}
                {gapData.important && gapData.important.length > 0 && (
                    <div>
                        <span style={{
                            fontSize: '11px',
                            fontWeight: '600',
                            color: '#d97706',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            Important ({gapData.important.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.important.slice(0, 3).map((skill, index) => (
                                <span
                                    key={index}
                                    style={{
                                        background: '#fffbeb',
                                        color: '#d97706',
                                        padding: '2px 6px',
                                        borderRadius: '8px',
                                        fontSize: '11px',
                                        fontWeight: '500',
                                        border: '1px solid #fed7aa'
                                    }}
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Trending Skills */}
                {gapData.trending && gapData.trending.length > 0 && (
                    <div>
                        <span style={{
                            fontSize: '11px',
                            fontWeight: '600',
                            color: '#7c3aed',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            Trending ({gapData.trending.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.trending.slice(0, 2).map((skill, index) => (
                                <span
                                    key={index}
                                    style={{
                                        background: '#faf5ff',
                                        color: '#7c3aed',
                                        padding: '2px 6px',
                                        borderRadius: '8px',
                                        fontSize: '11px',
                                        fontWeight: '500',
                                        border: '1px solid #e9d5ff'
                                    }}
                                >
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Learning Metrics */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '12px',
                paddingTop: '12px',
                borderTop: '1px solid rgba(99, 102, 241, 0.1)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock style={{ width: '14px', height: '14px', color: getTimeColor(analysis.estimated_learning_weeks) }} />
                    <span style={{
                        fontSize: '12px',
                        color: getTimeColor(analysis.estimated_learning_weeks),
                        fontWeight: '500'
                    }}>
                        ~{analysis.estimated_learning_weeks} weeks to bridge gaps
                    </span>
                </div>

                <button
                    onClick={() => onGenerateLearningPlan(job)}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        padding: '6px 12px',
                        background: '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => e.target.style.background = '#4f46e5'}
                    onMouseOut={(e) => e.target.style.background = '#6366f1'}
                >
                    <BookOpen style={{ width: '14px', height: '14px' }} />
                    Get Learning Plan
                </button>
            </div>
        </div>
    );
};

// Enhanced Match Breakdown Component
const MatchBreakdown = ({ job }) => (
  <div style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span>Skills Match:</span>
      <span>{Math.round((job.skill_score || job.overall_score) * 100)}%</span>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span>Experience Level:</span>
      <span>{Math.round((job.experience_score || job.overall_score) * 100)}%</span>
    </div>
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <span>Location:</span>
      <span>{Math.round((job.location_score || job.overall_score) * 100)}%</span>
    </div>
  </div>
);

const JobRecommendations = ({ userEmail, onNavigateToLearning }) => {
    const [recommendations, setRecommendations] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [shownJobIds, setShownJobIds] = useState(new Set()); // Track shown jobs
    const [hasMore, setHasMore] = useState(true);
    const [offset, setOffset] = useState(0);
    const [sortBy, setSortBy] = useState("match");
    const [experienceFilter, setExperienceFilter] = useState("all");
    const [remoteOnly, setRemoteOnly] = useState(false);
    const [savedJobs, setSavedJobs] = useState(new Set()); // New state to track saved jobs

    useEffect(() => {
        if (userEmail) {
            fetchRecommendations(true); // Reset on user change
        }
    }, [userEmail]);

    const fetchRecommendations = useCallback(async (reset = false) => {
        setLoading(true);
        setError('');

        const currentOffset = reset ? 0 : offset;
        const currentShownIds = reset ? [] : Array.from(shownJobIds);

        if (reset) {
            setRecommendations([]);
            setShownJobIds(new Set());
            setHasMore(true);
        }

        try {
            const response = await fetch('http://localhost:8000/jobs/find-matches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: userEmail,
                    top_k: 10,
                    min_similarity: 0.3,
                    offset: currentOffset,
                    exclude_job_ids: currentShownIds,
                    randomize: false
                })
            });

            if (!response.ok) {
                if (response.status === 429) {
                    console.log('Duplicate request ignored - already processing');
                    return;
                }
                if (response.status === 404) {
                    throw new Error('Please upload your resume first to get job recommendations.');
                } else {
                    throw new Error('Failed to fetch job recommendations. Please try again.');
                }
            }

            const data = await response.json();
            const newMatches = (data.matches || []).sort((a, b) => b.overall_score - a.overall_score);

            setRecommendations(prev => {
                const existing = reset ? [] : prev;
                const existingIds = new Set(existing.map(job => job.job_id));
                const uniqueNewMatches = newMatches.filter(job => !existingIds.has(job.job_id));
                const combined = [...existing, ...uniqueNewMatches];
                return combined.sort((a, b) => b.overall_score - a.overall_score);
            });

            setShownJobIds(prev => new Set([...prev, ...newMatches.map(job => job.job_id)]));
            setHasMore(data.has_more || false);
            setOffset(data.next_offset || 0);

        } catch (err) {
            console.error('Error fetching recommendations:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [userEmail, offset, shownJobIds]);

    useEffect(() => {
        if (userEmail) {
            fetchRecommendations(true); // Reset on user change
        }
    }, [userEmail]);

    const loadMoreJobs = () => {
        if (!loading && hasMore) {
            fetchRecommendations(false);
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

    const generateLearningPlan = async (job) => {
        if (onNavigateToLearning) {
            onNavigateToLearning(job);
        }
    };

    const getMatchQualityColor = (score) => {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.6) return '#f59e0b';
        return '#ef4444';
    };

    if (loading && recommendations.length === 0) {
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

    const sortedAndFilteredRecommendations = recommendations
        .filter(job => {
            if (remoteOnly && !job.remote_allowed) {
                return false;
            }
            if (experienceFilter !== 'all' && job.experience_level !== experienceFilter) {
                return false;
            }
            return true;
        })
        .sort((a, b) => {
            switch (sortBy) {
                case 'salary':
                    return (b.salary_max || 0) - (a.salary_max || 0);
                case 'recent':
                    return new Date(b.posted_date) - new Date(a.posted_date);
                case 'match':
                default:
                    return b.overall_score - a.overall_score;
            }
        });

    const handleSaveJob = async (jobId) => {
        if (savedJobs.has(jobId)) return; // Don't save if already saved

        try {
            const response = await fetch('http://localhost:8000/jobs/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_email: userEmail,
                    job_id: jobId,
                }),
            });

            if (response.ok) {
                console.log(`Job ${jobId} saved successfully!`);
                setSavedJobs(prev => new Set(prev).add(jobId)); // Update state to reflect save
            } else {
                 const errorData = await response.json();
                 console.error("Failed to save job:", errorData.detail);
            }
        } catch (err) {
            console.error('Error saving job:', err);
        }
    };

    const handleQuickApply = (job) => {
        console.log(`Quick applying to ${job.title} at ${job.company}`);
        // Here you would typically open a modal or make an API call to quick apply
    };

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
                        AI-powered job matches based on your resume • {recommendations.length} jobs shown
                    </p>
                </div>

                <button
                    onClick={() => fetchRecommendations(true)}
                    disabled={loading}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        background: loading ? '#9ca3af' : '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        if (!loading) e.target.style.background = '#4f46e5';
                    }}
                    onMouseOut={(e) => {
                        if (!loading) e.target.style.background = '#6366f1';
                    }}
                >
                    <Refresh style={{ width: '14px', height: '14px' }} />
                    {loading ? 'Finding...' : 'Fresh Jobs'}
                </button>


            </div>
            <div style={{ display: 'flex', gap: '12px',
                marginBottom: '20px', flexWrap: 'wrap' }}>
              <select
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                padding: '8px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
              >
                <option value="match">Best Match</option>
                <option value="salary">Highest Salary</option>
                <option value="recent">Most Recent</option>
              </select>

              <select
                onChange={(e) => setExperienceFilter(e.target.value)}
                style={{
                padding: '8px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
              >
                <option value="all">All Levels</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior</option>
              </select>

              <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                />
                Remote Only
              </label>
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
                    {sortedAndFilteredRecommendations.map((job) => (
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
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: '8px'
                                }}>
                                  <div style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '50%',
                                    background: `conic-gradient(${getMatchQualityColor(job.overall_score)} ${job.overall_score * 360}deg, #e5e7eb 0deg)`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '10px',
                                    fontWeight: 'bold',
                                    color: getMatchQualityColor(job.overall_score)
                                  }}>
                                    {Math.round(job.overall_score * 100)}
                                  </div>
                                  <div>
                                    <div style={{ fontSize: '12px', fontWeight: '600' }}>Match</div>
                                    <div style={{ fontSize: '10px', color: '#6b7280' }}>Score</div>
                                  </div>
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

                            <MatchBreakdown job={job} />

                            {/* Enhanced Skills Gap Analysis */}
                            {(job.skill_gaps_detailed &&
                              (job.skill_gaps_detailed.critical?.length > 0 ||
                               job.skill_gaps_detailed.important?.length > 0)) && (
                                <SkillsGapAnalysis
                                    job={job}
                                    onGenerateLearningPlan={generateLearningPlan}
                                />
                            )}

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
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <button
                                    onClick={() => handleSaveJob(job.job_id)}
                                    disabled={savedJobs.has(job.job_id)}
                                    style={{
                                        padding: '8px 14px',
                                        background: savedJobs.has(job.job_id) ? '#e5e7eb' : '#f3f4f6',
                                        color: savedJobs.has(job.job_id) ? '#6b7280' : '#374151',
                                        border: '1px solid #d1d5db',
                                        borderRadius: '8px',
                                        fontSize: '13px',
                                        fontWeight: '500',
                                        cursor: savedJobs.has(job.job_id) ? 'default' : 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                  >
                                    {savedJobs.has(job.job_id) ? '💾 Saved' : '💾 Save'}
                                  </button>
                                  <button
                                    onClick={() => handleQuickApply(job)}
                                    style={{
                                      padding: '6px 12px',
                                      background: '#10b981',
                                      color: 'white',
                                      border: 'none',
                                      borderRadius: '6px',
                                      cursor: 'pointer'
                                    }}
                                  >
                                    ⚡ Quick Apply
                                  </button>
                                </div>

                                <button
                                    onClick={() => {
                                        handleFeedback(job.recommendation_id, 'applied');
                                        if (job.job_url) {
                                            window.open(job.job_url, '_blank');
                                        } else {
                                            const searchQuery = `${job.title} ${job.company} careers`;
                                            const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
                                            window.open(searchUrl, '_blank');
                                        }
                                    }}
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

                    {/* Load More Button */}
                    {hasMore && (
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            paddingTop: '20px',
                            borderTop: '1px solid #e5e7eb'
                        }}>
                            <button
                                onClick={loadMoreJobs}
                                disabled={loading}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '12px 24px',
                                    background: loading ? '#9ca3af' : '#f3f4f6',
                                    color: loading ? 'white' : '#374151',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '12px',
                                    fontSize: '14px',
                                    fontWeight: '500',
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    transition: 'all 0.2s'
                                }}
                                onMouseOver={(e) => {
                                    if (!loading) {
                                        e.target.style.background = '#e5e7eb';
                                        e.target.style.borderColor = '#9ca3af';
                                    }
                                }}
                                onMouseOut={(e) => {
                                    if (!loading) {
                                        e.target.style.background = '#f3f4f6';
                                        e.target.style.borderColor = '#d1d5db';
                                    }
                                }}
                            >
                                <Plus style={{ width: '16px', height: '16px' }} />
                                {loading ? 'Loading more jobs...' : 'Show More Jobs'}
                            </button>
                        </div>
                    )}

                    {/* End of results message */}
                    {!hasMore && recommendations.length > 0 && (
                        <div style={{
                            textAlign: 'center',
                            paddingTop: '20px',
                            borderTop: '1px solid #e5e7eb',
                            color: '#6b7280',
                            fontSize: '14px'
                        }}>
                            You've seen all available job matches. Click "Fresh Jobs" to get new recommendations!
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default JobRecommendations;