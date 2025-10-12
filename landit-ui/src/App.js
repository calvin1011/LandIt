import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';
import ResumeUploader from './components/ResumeUploader';
import JobRecommendations from './components/JobRecommendations';
import Login from "./components/Login";
import Profile from './components/Profile';
import AdminPanel from './components/AdminPanel';
import './App.css';
import Learning from './components/Learning';
import SavedJobs from './components/SavedJobs';

const initialUserInfo = {
    fullName: '',
    age: '',
    profession: '',
    city: '',
    state: '',
    country: ''
};

function App() {
    const [parsedData, setParsedData] = useState([]);
    const [loggedIn, setLoggedIn] = useState(false);
    const [userEmail, setUserEmail] = useState('');
    const [userInfo, setUserInfo] = useState(initialUserInfo);
    const [loading, setLoading] = useState(true);
    const [firebaseUser, setFirebaseUser] = useState(null);
    const [showUploader, setShowUploader] = useState(false);
    const [activeTab, setActiveTab] = useState('resume');
    const [isAdmin, setIsAdmin] = useState(false);

    const [learningJobContext, setLearningJobContext] = useState(null);

    const [jobDescription, setJobDescription] = useState('');
    const [missingSkills, setMissingSkills] = useState([]);
    const [recommendedJobs, setRecommendedJobs] = useState([]);

    // Job recommendations state
    const [jobRecommendations, setJobRecommendations] = useState([]);
    const [jobsLoading, setJobsLoading] = useState(false);
    const [jobsError, setJobsError] = useState('');
    const [shownJobIds, setShownJobIds] = useState(new Set());
    const [hasMoreJobs, setHasMoreJobs] = useState(true);
    const [jobOffset, setJobOffset] = useState(0);
    const [savedJobs, setSavedJobs] = useState(new Set());
    const [appliedJobs, setAppliedJobs] = useState(new Set());
    const [jobToConfirm, setJobToConfirm] = useState(null);

    // Fetch job recommendations function
    const fetchJobRecommendations = async (reset = false) => {
        if (!userEmail) return;

        setJobsLoading(true);
        setJobsError('');

        const currentOffset = reset ? 0 : jobOffset;
        const currentShownIds = reset ? [] : Array.from(shownJobIds);

        if (reset) {
            setJobRecommendations([]);
            setShownJobIds(new Set());
            setHasMoreJobs(true);
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

            setJobRecommendations(prev => {
                const existing = reset ? [] : prev;
                const existingIds = new Set(existing.map(job => job.job_id));
                const uniqueNewMatches = newMatches.filter(job => !existingIds.has(job.job_id));
                const combined = [...existing, ...uniqueNewMatches];
                return combined.sort((a, b) => b.overall_score - a.overall_score);
            });

            setShownJobIds(prev => new Set([...prev, ...newMatches.map(job => job.job_id)]));
            setHasMoreJobs(data.has_more || false);
            setJobOffset(data.next_offset || 0);

        } catch (err) {
            console.error('Error fetching recommendations:', err);
            setJobsError(err.message);
        } finally {
            setJobsLoading(false);
        }
    };

    // Handler functions for job actions
    const handleJobFeedback = async (recommendationId, feedbackType, rating = null) => {
        try {
            const response = await fetch('http://localhost:8000/jobs/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_email: userEmail,
                    recommendation_id: recommendationId,
                    feedback_type: feedbackType,
                    overall_rating: rating,
                    action_taken: feedbackType
                })
            });

            if (response.ok) {
                setJobRecommendations(prev => prev.map(rec =>
                    rec.recommendation_id === recommendationId
                        ? { ...rec, userFeedback: feedbackType }
                        : rec
                ));
            }
        } catch (err) {
            console.error('Error submitting feedback:', err);
        }
    };

    const handleSaveJob = async (jobId) => {
        if (savedJobs.has(jobId)) return;

        try {
            const response = await fetch('http://localhost:8000/jobs/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: userEmail, job_id: jobId }),
            });

            if (response.ok) {
                console.log(`Job ${jobId} saved successfully!`);
                setSavedJobs(prev => new Set(prev).add(jobId));
            } else {
                const errorData = await response.json();
                console.error("Failed to save job:", errorData.detail);
            }
        } catch (err) {
            console.error('Error saving job:', err);
        }
    };

    const handleQuickApply = (job) => {
        console.log('Job URL:', job.job_url);
        console.log('Full job data:', job);

        sessionStorage.setItem('pendingApplicationConfirmation', JSON.stringify(job));
        setJobToConfirm(job);

        if (job.job_url) {
            console.log('Opening direct URL:', job.job_url);
            window.open(job.job_url, '_blank');
        } else {
            console.log('No URL found, using Google search');
            const searchQuery = `${job.title} ${job.company} careers`;
            const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
            window.open(searchUrl, '_blank');
        }
    };

    const handleConfirmApply = async () => {
        if (!jobToConfirm) return;

        const { job_id, recommendation_id } = jobToConfirm;

        setAppliedJobs(prev => new Set(prev).add(job_id));

        try {
            const response = await fetch('http://localhost:8000/jobs/quick-apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: userEmail, job_id: job_id }),
            });
            if (!response.ok) {
                console.error("Failed to record application on the backend.");
            } else {
                console.log(`Application for job ${job_id} successfully recorded.`);
            }
        } catch (err) {
            console.error('Error recording application:', err);
        }

        handleJobFeedback(recommendation_id, 'applied');
        setJobToConfirm(null);
    };

    const handleCancelApply = () => {
        setJobToConfirm(null);
    };

    // Handle visibility change for job confirmation
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.visibilityState === 'visible') {
                const pendingJobJSON = sessionStorage.getItem('pendingApplicationConfirmation');
                if (pendingJobJSON) {
                    const pendingJob = JSON.parse(pendingJobJSON);
                    setJobToConfirm(pendingJob);
                    sessionStorage.removeItem('pendingApplicationConfirmation');
                }
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        handleVisibilityChange();

        return () => {
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, []);

    // Only fetch jobs when user logs in or uploads resume, not when switching tabs
    useEffect(() => {
        if (loggedIn && userEmail && jobRecommendations.length === 0) {
            // Check if we have jobs from resume upload first
            const persistedData = sessionStorage.getItem('resumeAnalysisData');
            if (persistedData) {
                const data = JSON.parse(persistedData);
                if (data.recommended_jobs && data.recommended_jobs.length > 0) {
                    setJobRecommendations(data.recommended_jobs);
                    return;
                }
            }
            // Otherwise fetch from API
            fetchJobRecommendations(true);
        }
    }, [loggedIn, userEmail]);

    useEffect(() => {
        console.log('Setting up Firebase auth listener...');

        const unsubscribe = onAuthStateChanged(auth, (user) => {
            console.log(' Firebase auth state changed:', user ? user.email : 'No user');

            if (user) {
                const email = user.email;
                setFirebaseUser(user);
                setLoggedIn(true);
                setUserEmail(email);

                // Simple admin check: if the user email matches a specific one
                if (email === 'admin@landit.com' || email === 'calvinssendawula@gmail.com') {
                    setIsAdmin(true);
                } else {
                    setIsAdmin(false);
                }

                const savedUserProfile = localStorage.getItem(`userInfo_${email}`);
                if (savedUserProfile) {
                    console.log('📱 Loading saved profile for:', email);
                    setUserInfo(JSON.parse(savedUserProfile));
                } else {
                    console.log('📱 No saved profile, using initial state for:', email);
                    setUserInfo(initialUserInfo);
                }

                localStorage.setItem('currentUser', email);

            } else {
                console.log(' User signed out, clearing state');
                setFirebaseUser(null);
                setLoggedIn(false);
                setUserEmail('');
                setUserInfo(initialUserInfo);
                setParsedData([]);
                setShowUploader(false);
                setActiveTab('resume');
                localStorage.removeItem('currentUser');
                setIsAdmin(false); // Clear admin status on sign out
            }

            setLoading(false);
        });

        return () => {
            console.log(' Cleaning up Firebase auth listener');
            unsubscribe();
        };
    }, []);

    const handleLoginSuccess = (email, user = null) => {
        console.log(' Login successful for:', email);
        setParsedData([]);
        setShowUploader(false);
        setActiveTab('resume');
    };

    const handleLogout = async () => {
        console.log(' Logging out...');

        try {
            await auth.signOut();
            setParsedData([]);
            setShowUploader(false);
            setActiveTab('resume');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    const handleAccountSwitch = (newEmail) => {
        console.log(' Account switch detected:', userEmail, '→', newEmail);

        if (userEmail && userEmail !== newEmail) {
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }

        setParsedData([]);
        setShowUploader(false);
        setActiveTab('resume');

        const newUserProfile = localStorage.getItem(`userInfo_${newEmail}`);
        if (newUserProfile) {
            setUserInfo(JSON.parse(newUserProfile));
        } else {
            setUserInfo(initialUserInfo);
        }
    };

    const handleNavigateToLearning = (job) => {
        setLearningJobContext(job);
        setActiveTab('learning');
    };

    const handleUploadNew = () => {
        setShowUploader(true);
        setParsedData([]);
        setActiveTab('resume');
    };

    const handleUploadSuccess = (data) => {
        setShowUploader(false);

        // Set parsed resume data and missing skills
        setParsedData(data.entities || []);
        setMissingSkills(data.missing_skills || []);

        // Fetch fresh job recommendations, clearing any old ones
        fetchJobRecommendations(true);

        // Save the entire data object to sessionStorage
        sessionStorage.setItem('resumeAnalysisData', JSON.stringify(data));

        // Automatically switch to the jobs tab
        setActiveTab('jobs');
    };

    useEffect(() => {
        if (loggedIn && userEmail && !loading) {
            console.log(' Saving profile data for:', userEmail);
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }
    }, [userInfo, loggedIn, userEmail, loading]);

    useEffect(() => {
        const lastUser = localStorage.getItem('currentUser');
        if (lastUser && userEmail && lastUser !== userEmail) {
            handleAccountSwitch(userEmail);
        }
    }, [userEmail]);

    useEffect(() => {
        // Check sessionStorage for persisted data when the app loads
        const persistedData = sessionStorage.getItem('resumeAnalysisData');
        if (persistedData) {
            const data = JSON.parse(persistedData);
            setParsedData(data.entities || []);
            setMissingSkills(data.missing_skills || []);
        }
    }, []);

    if (loading) {
        return (
            <div style={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }}>
                <div style={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    borderRadius: '20px',
                    padding: '40px',
                    textAlign: 'center',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔄</div>
                    <div style={{ fontSize: '18px', color: '#6b7280' }}>
                        Checking authentication...
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            {!loggedIn ? (
                <Login onLoginSuccess={handleLoginSuccess} />
            ) : (
                <div style={{
                    height: '100vh',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    position: 'relative',
                    overflow: 'auto'
                }}>
                    {/* Animated Background Elements */}
                    <div style={{
                        position: 'absolute',
                        top: '-50%',
                        left: '-10%',
                        width: '500px',
                        height: '500px',
                        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
                        borderRadius: '50%',
                        animation: 'float 20s infinite ease-in-out',
                        pointerEvents: 'none'
                    }}></div>
                    <div style={{
                        position: 'absolute',
                        bottom: '-30%',
                        right: '-5%',
                        width: '600px',
                        height: '600px',
                        background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
                        borderRadius: '50%',
                        animation: 'float 25s infinite ease-in-out reverse',
                        pointerEvents: 'none'
                    }}></div>

                    {/* Header */}
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.95) 0%, rgba(118, 75, 162, 0.95) 100%)',
                        backdropFilter: 'blur(20px) saturate(180%)',
                        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                        borderBottom: '1px solid rgba(255,255,255,0.3)',
                        padding: '20px 40px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        right: 0,
                        zIndex: 1000,
                        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                            <div style={{
                                width: '50px',
                                height: '50px',
                                background: 'linear-gradient(135deg, #ffffff 0%, rgba(255,255,255,0.8) 100%)',
                                borderRadius: '15px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '24px',
                                boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
                                transition: 'transform 0.3s ease',
                                cursor: 'pointer'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05) rotate(5deg)'}
                            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1) rotate(0deg)'}
                            >📋</div>
                            <div>
                                <h1 style={{
                                    margin: 0,
                                    fontSize: '28px',
                                    fontWeight: '800',
                                    color: 'white',
                                    textShadow: '0 2px 10px rgba(0,0,0,0.1)',
                                    letterSpacing: '-0.5px'
                                }}>LandIt</h1>
                                <p style={{ margin: 0, fontSize: '13px', color: 'rgba(255,255,255,0.85)', fontWeight: '500' }}>
                                    Smart Document Parser & Job Matcher
                                </p>
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                            {/* Navigation Tabs */}
                            <div style={{ display: 'flex', gap: '8px' }}>
                                {/* ... your tab buttons remain the same ... */}
                                <button
                                    onClick={() => setActiveTab('resume')}
                                    style={{
                                        padding: '10px 20px',
                                        background: activeTab === 'resume'
                                            ? 'rgba(255, 255, 255, 0.25)'
                                            : 'rgba(255, 255, 255, 0.08)',
                                        color: 'white',
                                        border: activeTab === 'resume'
                                            ? '1px solid rgba(255, 255, 255, 0.3)'
                                            : '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        backdropFilter: 'blur(10px)',
                                        boxShadow: activeTab === 'resume'
                                            ? '0 4px 15px rgba(0,0,0,0.1)'
                                            : 'none',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                    onMouseOver={(e) => {
                                        if (activeTab !== 'resume') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                            e.target.style.transform = 'translateY(-2px)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (activeTab !== 'resume') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                            e.target.style.transform = 'translateY(0)';
                                        }
                                    }}
                                >
                                    📄 Resume
                                </button>

                                <button
                                    onClick={() => setActiveTab('jobs')}
                                    style={{
                                        padding: '10px 20px',
                                        background: activeTab === 'jobs'
                                            ? 'rgba(255, 255, 255, 0.25)'
                                            : 'rgba(255, 255, 255, 0.08)',
                                        color: 'white',
                                        border: activeTab === 'jobs'
                                            ? '1px solid rgba(255, 255, 255, 0.3)'
                                            : '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        backdropFilter: 'blur(10px)',
                                        boxShadow: activeTab === 'jobs'
                                            ? '0 4px 15px rgba(0,0,0,0.1)'
                                            : 'none',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                    onMouseOver={(e) => {
                                        if (activeTab !== 'jobs') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                            e.target.style.transform = 'translateY(-2px)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (activeTab !== 'jobs') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                            e.target.style.transform = 'translateY(0)';
                                        }
                                    }}
                                >
                                    🎯 Jobs
                                </button>

                                <button
                                    onClick={() => setActiveTab('saved')}
                                    style={{
                                        padding: '10px 20px',
                                        background: activeTab === 'saved'
                                            ? 'rgba(255, 255, 255, 0.25)'
                                            : 'rgba(255, 255, 255, 0.08)',
                                        color: 'white',
                                        border: activeTab === 'saved'
                                            ? '1px solid rgba(255, 255, 255, 0.3)'
                                            : '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        backdropFilter: 'blur(10px)',
                                        boxShadow: activeTab === 'saved'
                                            ? '0 4px 15px rgba(0,0,0,0.1)'
                                            : 'none',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                    onMouseOver={(e) => {
                                        if (activeTab !== 'saved') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                            e.target.style.transform = 'translateY(-2px)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (activeTab !== 'saved') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                            e.target.style.transform = 'translateY(0)';
                                        }
                                    }}
                                >
                                    💾 Saved
                                </button>

                                <button
                                    onClick={() => setActiveTab('learning')}
                                    style={{
                                        padding: '10px 20px',
                                        background: activeTab === 'learning'
                                            ? 'rgba(255, 255, 255, 0.25)'
                                            : 'rgba(255, 255, 255, 0.08)',
                                        color: 'white',
                                        border: activeTab === 'learning'
                                            ? '1px solid rgba(255, 255, 255, 0.3)'
                                            : '1px solid rgba(255, 255, 255, 0.1)',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                        backdropFilter: 'blur(10px)',
                                        boxShadow: activeTab === 'learning'
                                            ? '0 4px 15px rgba(0,0,0,0.1)'
                                            : 'none',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                    onMouseOver={(e) => {
                                        if (activeTab !== 'learning') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                            e.target.style.transform = 'translateY(-2px)';
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (activeTab !== 'learning') {
                                            e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                            e.target.style.transform = 'translateY(0)';
                                        }
                                    }}
                                >
                                    🧠 Learning
                                </button>

                                {isAdmin && (
                                    <button
                                        onClick={() => setActiveTab('admin')}
                                        style={{
                                            padding: '10px 20px',
                                            background: activeTab === 'admin'
                                                ? 'rgba(255, 255, 255, 0.25)'
                                                : 'rgba(255, 255, 255, 0.08)',
                                            color: 'white',
                                            border: activeTab === 'admin'
                                                ? '1px solid rgba(255, 255, 255, 0.3)'
                                                : '1px solid rgba(255, 255, 255, 0.1)',
                                            borderRadius: '12px',
                                            fontSize: '14px',
                                            fontWeight: '600',
                                            cursor: 'pointer',
                                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                            backdropFilter: 'blur(10px)',
                                            boxShadow: activeTab === 'admin'
                                                ? '0 4px 15px rgba(0,0,0,0.1)'
                                                : 'none',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '6px'
                                        }}
                                        onMouseOver={(e) => {
                                            if (activeTab !== 'admin') {
                                                e.target.style.background = 'rgba(255, 255, 255, 0.15)';
                                                e.target.style.transform = 'translateY(-2px)';
                                            }
                                        }}
                                        onMouseOut={(e) => {
                                            if (activeTab !== 'admin') {
                                                e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                                                e.target.style.transform = 'translateY(0)';
                                            }
                                        }}
                                    >
                                        ⚙️ Admin
                                    </button>
                                )}
                            </div>

                            {parsedData.length > 0 && !showUploader && activeTab === 'resume' && (
                                <button
                                    onClick={handleUploadNew}
                                    style={{
                                        padding: '10px 20px',
                                        background: 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0.2) 100%)',
                                        color: 'white',
                                        border: '1px solid rgba(255,255,255,0.3)',
                                        borderRadius: '12px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '8px',
                                        backdropFilter: 'blur(10px)',
                                        boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
                                    }}
                                    onMouseOver={(e) => {
                                        e.target.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.3) 100%)';
                                        e.target.style.transform = 'translateY(-2px)';
                                        e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.15)';
                                    }}
                                    onMouseOut={(e) => {
                                        e.target.style.background = 'linear-gradient(135deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0.2) 100%)';
                                        e.target.style.transform = 'translateY(0)';
                                        e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
                                    }}
                                >
                                    📤 Upload New Resume
                                </button>
                            )}

                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                background: 'rgba(255,255,255,0.15)',
                                borderRadius: '12px',
                                backdropFilter: 'blur(10px)',
                                border: '1px solid rgba(255,255,255,0.2)'
                            }}>
                                <span style={{ fontSize: '20px' }}>👋</span>
                                <span style={{ fontSize: '14px', color: 'white', fontWeight: '500' }}>
                                    {userEmail}
                                </span>
                            </div>

                            <button
                                onClick={handleLogout}
                                style={{
                                    padding: '10px 20px',
                                    background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)',
                                    color: 'white',
                                    border: '1px solid rgba(255,255,255,0.2)',
                                    borderRadius: '12px',
                                    fontSize: '14px',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease',
                                    backdropFilter: 'blur(10px)',
                                    boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
                                }}
                                onMouseOver={(e) => {
                                    e.target.style.transform = 'translateY(-2px)';
                                    e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
                                }}
                                onMouseOut={(e) => {
                                    e.target.style.transform = 'translateY(0)';
                                    e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
                                }}
                            >
                                Sign Out
                            </button>
                        </div>
                    </div>

                    <div style={{
                        padding: '30px 40px',
                        paddingTop: '130px',
                        width: '100%',
                        boxSizing: 'border-box',
                        animation: 'fadeIn 0.6s ease-out',
                        minHeight: 'calc(100vh - 130px)'
                    }}>
                        {/* Profile Section */}
                        <Profile userInfo={userInfo} setUserInfo={setUserInfo} />

                        {/* Job Description Text Area */}
                        {activeTab === 'resume' && (
                            <div style={{
                                marginBottom: '30px',
                                animation: 'scaleIn 0.5s ease-out'
                            }}>
                                <div style={{
                                    background: 'rgba(255, 255, 255, 0.15)',
                                    backdropFilter: 'blur(20px) saturate(180%)',
                                    WebkitBackdropFilter: 'blur(20px) saturate(180%)',
                                    borderRadius: '20px',
                                    padding: '30px',
                                    border: '1px solid rgba(255,255,255,0.18)',
                                    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.2)',
                                    transition: 'all 0.3s ease'
                                }}>
                                    <h3 style={{
                                        color: 'white',
                                        marginTop: 0,
                                        fontSize: '20px',
                                        fontWeight: '700',
                                        marginBottom: '15px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px'
                                    }}>
                                        <span style={{ fontSize: '24px' }}>📝</span>
                                        Optional: Job Description Analysis
                                    </h3>
                                    <textarea
                                        value={jobDescription}
                                        onChange={(e) => setJobDescription(e.target.value)}
                                        placeholder="Paste the job description here to analyze skill gaps and get personalized recommendations..."
                                        style={{
                                            width: '100%',
                                            minHeight: '150px',
                                            padding: '20px',
                                            borderRadius: '15px',
                                            border: '1px solid rgba(255,255,255,0.2)',
                                            fontSize: '15px',
                                            fontFamily: 'inherit',
                                            boxSizing: 'border-box',
                                            background: 'rgba(255, 255, 255, 0.9)',
                                            color: '#1f2937',
                                            resize: 'vertical',
                                            transition: 'all 0.3s ease',
                                            boxShadow: '0 4px 15px rgba(0,0,0,0.05)'
                                        }}
                                        onFocus={(e) => {
                                            e.target.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
                                            e.target.style.transform = 'scale(1.01)';
                                        }}
                                        onBlur={(e) => {
                                            e.target.style.boxShadow = '0 4px 15px rgba(0,0,0,0.05)';
                                            e.target.style.transform = 'scale(1)';
                                        }}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Main Content Area */}
                        {activeTab === 'resume' && (
                            <>
                                {/* Resume Upload/Results Section */}
                                {parsedData.length === 0 || showUploader ? (
                                    <ResumeUploader
                                        onUploadSuccess={handleUploadSuccess}
                                        userEmail={userEmail}
                                        jobDescriptionText={jobDescription}
                                    />
                                ) : (
                                    <>
                                        {/* Display missing skills if they exist */}
                                      {missingSkills.length > 0 && (
                                        <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '12px', padding: '20px', marginBottom: '20px' }}>
                                          <h3 style={{ color: '#c2410c' }}>Skills to Add</h3>
                                          <p style={{color: '#9a3412'}}>Based on the job description, you might want to highlight these skills on your resume:</p>
                                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
                                            {missingSkills.map(skill => (
                                              <span key={skill} style={{ background: '#fed7aa', color: '#7c2d12', padding: '4px 10px', borderRadius: '12px', fontSize: '14px' }}>
                                                {skill}
                                              </span>
                                            ))}
                                          </div>
                                        </div>
                                      )}
                                    </>
                                )}
                            </>
                        )}

                        {activeTab === 'jobs' && (
                            <JobRecommendations
                                userEmail={userEmail}
                                onNavigateToLearning={handleNavigateToLearning}
                                recommendations={jobRecommendations}
                                loading={jobsLoading}
                                error={jobsError}
                                hasMore={hasMoreJobs}
                                onFetchRecommendations={fetchJobRecommendations}
                                onLoadMore={() => fetchJobRecommendations(false)}
                                onFeedback={handleJobFeedback}
                                onSaveJob={handleSaveJob}
                                onQuickApply={handleQuickApply}
                                savedJobs={savedJobs}
                                appliedJobs={appliedJobs}
                                jobToConfirm={jobToConfirm}
                                onConfirmApply={handleConfirmApply}
                                onCancelApply={handleCancelApply}
                            />
                        )}

                        {/* Render SavedJobs component */}
                        {activeTab === 'saved' && (
                            <SavedJobs userEmail={userEmail} />
                        )}

                        {/* RENDER ADMINPANEL COMPONENT */}
                        {activeTab === 'admin' && (
                            <AdminPanel />
                        )}

                        {/*Leaning component*/}
                        {activeTab === 'learning' && (
                            <Learning
                                userEmail={userEmail}
                                jobContext={learningJobContext}
                                onClearJobContext={() => setLearningJobContext(null)}
                            />
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;