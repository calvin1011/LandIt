import React, { useState } from 'react';
import { Briefcase, MapPin, DollarSign, RefreshCw, TrendingUp, ThumbsUp, ThumbsDown, BookOpen, Clock } from 'lucide-react';

// MatchScore Component for the right side of the card
const MatchScore = ({ job }) => {
    // Ensure scores are numbers and default to 0 if not available
    const overallScore = Math.round((job.overall_score || 0) * 100);
    const skillsScore = Math.round((job.skills_similarity || 0) * 100);
    const experienceScore = Math.round((job.experience_match || 0) * 100);
    const locationScore = Math.round((job.location_match || 0) * 100);

    const circumference = 2 * Math.PI * 40;
    const strokeDashoffset = circumference - ((overallScore / 100) * circumference);

    const getScoreColor = () => {
        if (overallScore >= 90) return '#34D399';
        if (overallScore >= 70) return '#60A5FA';
        return '#FBBF24';
    };

    const getMatchText = () => {
        if (overallScore >= 90) return 'Excellent Match';
        if (overallScore >= 70) return 'Strong Match';
        if (overallScore >= 50) return 'Good Match';
        return 'Fair Match';
    };

    const scoreDetail = (label, value) => (
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', fontSize: '12px', opacity: '0.8' }}>
            <span>{label}</span>
            <span style={{ fontWeight: '600' }}>{value}%</span>
        </div>
    );

    return (
        <div style={{
            width: '220px',
            flexShrink: 0,
            background: '#1F2937',
            borderRadius: '0 16px 16px 0',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            color: 'white'
        }}>
            <div style={{ position: 'relative', width: '100px', height: '100px', marginBottom: '16px' }}>
                <svg width="100" height="100" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
                    <circle cx="50" cy="50" r="40" stroke="#374151" strokeWidth="8" fill="transparent" />
                    <circle
                        cx="50" cy="50" r="40"
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
                    position: 'absolute', top: '50%', left: '50%',
                    transform: 'translate(-50%, -50%)', fontSize: '24px', fontWeight: 'bold',
                    color: getScoreColor()
                }}>
                    {overallScore}<span style={{fontSize: '14px'}}>%</span>
                </div>
            </div>
            <div style={{ fontWeight: '600', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                {getMatchText()}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
                {scoreDetail("Skills", skillsScore)}
                {scoreDetail("Experience", experienceScore)}
                {scoreDetail("Location", locationScore)}
            </div>
        </div>
    );
};

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
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '12px'
            }}>
                <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#4f46e5', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <TrendingUp size={16} />
                    Skills Gap Analysis
                </h4>

                <div style={{ background: getDifficultyColor(analysis.difficulty_level), color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: '600', textTransform: 'uppercase' }}>
                    {analysis.difficulty_level} Priority
                </div>
            </div>
            <p style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#6b7280', lineHeight: '1.4' }}>
                {job.improvement_summary}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {gapData.critical && gapData.critical.length > 0 && (
                    <div>
                        <span style={{ fontSize: '11px', fontWeight: '600', color: '#dc2626', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            Critical ({gapData.critical.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.critical.slice(0, 3).map((skill, index) => (
                                <span key={index} style={{ background: '#fef2f2', color: '#dc2626', padding: '2px 6px', borderRadius: '8px', fontSize: '11px', fontWeight: '500', border: '1px solid #fecaca' }}>
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

                {gapData.important && gapData.important.length > 0 && (
                    <div>
                        <span style={{ fontSize: '11px', fontWeight: '600', color: '#d97706', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            Important ({gapData.important.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.important.slice(0, 3).map((skill, index) => (
                                <span key={index} style={{ background: '#fffbeb', color: '#d97706', padding: '2px 6px', borderRadius: '8px', fontSize: '11px', fontWeight: '500', border: '1px solid #fed7aa' }}>
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {gapData.trending && gapData.trending.length > 0 && (
                    <div>
                        <span style={{ fontSize: '11px', fontWeight: '600', color: '#7c3aed', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                            Trending ({gapData.trending.length})
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                            {gapData.trending.slice(0, 2).map((skill, index) => (
                                <span key={index} style={{ background: '#faf5ff', color: '#7c3aed', padding: '2px 6px', borderRadius: '8px', fontSize: '11px', fontWeight: '500', border: '1px solid #e9d5ff' }}>
                                    {skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(99, 102, 241, 0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={14} style={{ color: getTimeColor(analysis.estimated_learning_weeks) }} />
                    <span style={{ fontSize: '12px', color: getTimeColor(analysis.estimated_learning_weeks), fontWeight: '500' }}>
                        ~{analysis.estimated_learning_weeks} weeks to bridge gaps
                    </span>
                </div>

                <button
                    onClick={() => onGenerateLearningPlan(job)}
                    style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', background: '#6366f1', color: 'white', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: '500', cursor: 'pointer' }}
                >
                    <BookOpen size={14} />
                    Get Learning Plan
                </button>
            </div>
        </div>
    );
};

// JobCard component with all original functionality
const JobCard = ({ job, userEmail, onGenerateLearningPlan, savedJobs, appliedJobs, jobToConfirm, handleSaveJob, handleQuickApply, handleConfirmApply, handleCancelApply, handleFeedback }) => {
    const isSaved = savedJobs.has(job.job_id);
    const isApplied = appliedJobs.has(job.job_id);

    return (
        <div style={{
            background: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            display: 'flex',
            overflow: 'hidden',
            position: 'relative',
            transition: 'all 0.2s'
        }} onMouseOver={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
        }} onMouseOut={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
        }}>
            {/* Confirmation Dialog */}
            {jobToConfirm && jobToConfirm.job_id === job.job_id && (
                <div style={{
                    position: 'absolute',
                    top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(248, 250, 252, 0.95)',
                    zIndex: 10,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: '16px',
                    backdropFilter: 'blur(4px)'
                }}>
                    <div style={{ background: 'white', padding: '2rem', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.1)', textAlign: 'center', border: '1px solid #e2e8f0' }}>
                        <h3 style={{ marginTop: 0, color: '#1f2937' }}>Did you apply?</h3>
                        <p style={{ color: '#4b5563' }}>
                            Did you complete the application for<br/>
                            <strong>{jobToConfirm.title}</strong> at <strong>{jobToConfirm.company}</strong>?
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1.5rem' }}>
                            <button onClick={handleConfirmApply} style={{ padding: '0.5rem 1rem', background: '#10b981', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}>
                                Yes, I Applied
                            </button>
                            <button onClick={handleCancelApply} style={{ padding: '0.5rem 1rem', background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: '8px', cursor: 'pointer' }}>
                                No, I Didn't
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Left Content */}
            <div style={{ padding: '24px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                    {/* Job Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                            <div style={{ width: '48px', height: '48px', borderRadius: '8px', background: '#f1f5f9', marginRight: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#475569' }}>
                                {job.company.charAt(0)}
                            </div>
                            <div>
                                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>{job.title}</h3>
                                <p style={{ margin: 0, fontSize: '14px', color: '#6366f1', fontWeight: '500' }}>{job.company}</p>
                            </div>
                        </div>
                    </div>

                    {/* Job Details */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '14px', color: '#64748b', marginBottom: '16px' }}>
                        {job.location && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <MapPin size={16} />
                                {job.location}
                                {job.remote_allowed && ' (Remote OK)'}
                            </span>
                        )}
                        {job.experience_level && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <Briefcase size={16} />
                                {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)} Level
                            </span>
                        )}
                        {(job.salary_min || job.salary_max) && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <DollarSign size={16} />
                                {job.salary_min && job.salary_max
                                    ? `${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()}`
                                    : job.salary_min
                                        ? `${job.salary_min.toLocaleString()}+`
                                        : `Up to ${job.salary_max.toLocaleString()}`
                                }
                            </span>
                        )}
                    </div>

                    {/* Match Explanation */}
                    {job.match_explanation && (
                        <div style={{ background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.1)', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                            <p style={{ margin: 0, fontSize: '14px', color: '#4f46e5', fontWeight: '500' }}>
                                {job.match_explanation}
                            </p>
                        </div>
                    )}

                    {/* Skills Match */}
                    {job.skill_matches && job.skill_matches.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                            <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                                Matching Skills:
                            </h4>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                {job.skill_matches.slice(0, 5).map((skill, index) => {
                                    const skillText = typeof skill === 'string' ? skill : skill.name || skill.text || JSON.stringify(skill);
                                    return (
                                        <span key={index} style={{ background: '#dcfce7', color: '#166534', padding: '4px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: '500' }}>
                                            {skillText}
                                        </span>
                                    );
                                })}
                                {job.skill_matches.length > 5 && (
                                    <span style={{ color: '#6b7280', fontSize: '12px', alignSelf: 'center' }}>
                                        +{job.skill_matches.length - 5} more
                                    </span>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Enhanced Skills Gap Analysis */}
                    {(job.skill_gaps_detailed && (job.skill_gaps_detailed.critical?.length > 0 || job.skill_gaps_detailed.important?.length > 0)) && (
                        <SkillsGapAnalysis job={job} onGenerateLearningPlan={onGenerateLearningPlan} />
                    )}
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
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
                        >
                            <ThumbsUp size={14} />
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
                        >
                            <ThumbsDown size={14} />
                            Not Interested
                        </button>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button
                            onClick={() => handleSaveJob(job.job_id)}
                            disabled={isSaved}
                            style={{
                                padding: '8px 14px',
                                background: isSaved ? '#e5e7eb' : '#f3f4f6',
                                color: isSaved ? '#6b7280' : '#374151',
                                border: '1px solid #d1d5db',
                                borderRadius: '8px',
                                fontSize: '13px',
                                fontWeight: '500',
                                cursor: isSaved ? 'default' : 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            {isSaved ? '💾 Saved' : '💾 Save'}
                        </button>

                        <button
                            onClick={() => handleQuickApply(job)}
                            disabled={isApplied}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '8px 16px',
                                background: isApplied ? '#6366f1' : '#10b981',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                fontSize: '14px',
                                fontWeight: '500',
                                cursor: isApplied ? 'default' : 'pointer',
                                transition: 'all 0.2s',
                                opacity: isApplied ? 0.7 : 1,
                            }}
                        >
                            {isApplied ? '⚡ Applied' : '⚡ Quick Apply'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Side - Score Display */}
            <MatchScore job={job} />
        </div>
    );
};

const normalizeJobData = (job) => {
    // Handle both formats: detailed from /jobs/find-matches and basic from /parse-resume-file
    return {
        job_id: job.job_id || job.id,
        title: job.title,
        company: job.company,
        job_url: job.job_url || '',
        location: job.location,
        remote_allowed: job.remote_allowed || false,
        salary_min: job.salary_min,
        salary_max: job.salary_max,
        experience_level: job.experience_level,
        skills_required: job.skills_required || [],

        // Normalize scores - handle both formats
        overall_score: job.overall_score || job.match_score || 0.5,
        skills_similarity: job.skills_similarity || job.skill_match_score || 0.5,
        experience_match: job.experience_match || 0.7,
        location_match: job.location_match || 0.8,

        // Normalize skill data
        skill_matches: job.skill_matches || [],
        skill_gaps: job.skill_gaps || [],
        skill_gaps_detailed: job.skill_gaps_detailed || {
            critical: job.skill_gaps || [],
            important: [],
            nice_to_have: [],
            trending: []
        },

        // Normalize analysis data
        gap_analysis: job.gap_analysis || {
            total_gaps: (job.skill_gaps || []).length,
            critical_gaps: (job.skill_gaps || []).length,
            estimated_learning_weeks: Math.max(4, (job.skill_gaps || []).length * 2),
            difficulty_level: (job.skill_gaps || []).length > 3 ? 'high' : 'medium'
        },

        match_explanation: job.match_explanation || `Based on your skills and experience`,
        improvement_summary: job.improvement_summary || `Focus on key skills to improve your match`,

        // Add recommendation_id if missing
        recommendation_id: job.recommendation_id || `temp_${job.job_id || job.id}`
    };
};

const JobRecommendations = ({
  userEmail,
  onNavigateToLearning,
  recommendations = [],
  loading = false,
  error = '',
  hasMore = false,
  onFetchRecommendations,
  onLoadMore,
  onFeedback,
  onSaveJob,
  onQuickApply,
  savedJobs = new Set(),
  appliedJobs = new Set(),
  jobToConfirm = null,
  onConfirmApply,
  onCancelApply
}) => {
    const [sortBy, setSortBy] = useState("match");
    const [experienceFilter, setExperienceFilter] = useState("all");
    const [remoteOnly, setRemoteOnly] = useState(false);

    const loadMoreJobs = () => {
        if (!loading && hasMore && onLoadMore) {
            onLoadMore();
        }
    };

    const handleFeedback = async (recommendationId, feedbackType, rating = null) => {
        if (onFeedback) {
            onFeedback(recommendationId, feedbackType, rating);
        }
    };

    const handleSaveJob = async (jobId) => {
        if (onSaveJob) {
            onSaveJob(jobId);
        }
    };

    const handleQuickApply = (job) => {
        if (onQuickApply) {
            onQuickApply(job);
        }
    };

    const handleConfirmApply = async () => {
        if (onConfirmApply) {
            onConfirmApply();
        }
    };

    const handleCancelApply = () => {
        if (onCancelApply) {
            onCancelApply();
        }
    };

    const generateLearningPlan = async (job) => {
        if (onNavigateToLearning) {
            onNavigateToLearning(job);
        }
    };

    const sortedAndFilteredRecommendations = recommendations
    .map(normalizeJobData) // Normalize all job data first
    .filter(job => {
        if (remoteOnly && !job.remote_allowed) return false;
        if (experienceFilter !== 'all' && job.experience_level !== experienceFilter) return false;
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        🎯 Job Recommendations
                    </h2>
                    <p style={{ margin: 0, fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                        AI-powered job matches based on your resume • {recommendations.length} jobs shown
                    </p>
                </div>

                <button
                    onClick={() => onFetchRecommendations(true)}
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
                    <RefreshCw size={14} />
                    {loading ? 'Finding...' : 'Fresh Jobs'}
                </button>
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                    <option value="match">Best Match</option>
                    <option value="salary">Highest Salary</option>
                    <option value="recent">Most Recent</option>
                </select>

                <select value={experienceFilter} onChange={(e) => setExperienceFilter(e.target.value)} style={{ padding: '8px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                    <option value="all">All Levels</option>
                    <option value="entry">Entry Level</option>
                    <option value="mid">Mid Level</option>
                    <option value="senior">Senior</option>
                </select>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} />
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
                <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>💼</div>
                    <h3 style={{ margin: 0, marginBottom: '10px' }}>No job recommendations yet</h3>
                    <p style={{ margin: 0 }}>Upload your resume to get personalized job matches</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {sortedAndFilteredRecommendations.map((job) => (
                        <JobCard
                            key={job.job_id}
                            job={job}
                            userEmail={userEmail}
                            onGenerateLearningPlan={generateLearningPlan}
                            savedJobs={savedJobs}
                            appliedJobs={appliedJobs}
                            jobToConfirm={jobToConfirm}
                            handleSaveJob={handleSaveJob}
                            handleQuickApply={handleQuickApply}
                            handleConfirmApply={handleConfirmApply}
                            handleCancelApply={handleCancelApply}
                            handleFeedback={handleFeedback}
                        />
                    ))}

                    {/* Load More Button */}
                    {hasMore && (
                        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '20px', borderTop: '1px solid #e5e7eb' }}>
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