import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';
import ResumeUploader from './components/ResumeUploader';
import JobRecommendations from './components/JobRecommendations';
import OutputViewer from './components/OutputViewer';
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

        // Set parsed resume data
        setParsedData(data.entities || []);

        // Set the missing skills to state
        setMissingSkills(data.missing_skills || []);

        // Set recommended jobs to state
        setRecommendedJobs(data.recommended_jobs || []);

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
                    minHeight: '100vh',
                    background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                }}>
                    {/* Header */}
                    <div style={{
                        background: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(10px)',
                        borderBottom: '1px solid rgba(0,0,0,0.1)',
                        padding: '20px 40px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        position: 'sticky',
                        top: 0,
                        zIndex: 100
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                borderRadius: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '18px'
                            }}>📋</div>
                            <div>
                                <h1 style={{
                                    margin: 0,
                                    fontSize: '24px',
                                    fontWeight: '700',
                                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    backgroundClip: 'text'
                                }}>LandIt</h1>
                                <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>Smart Document Parser & Job Matcher</p>
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                            {/* Navigation Tabs */}
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    onClick={() => setActiveTab('resume')}
                                    style={{
                                        padding: '8px 16px',
                                        background: activeTab === 'resume' ? '#6366f1' : 'transparent',
                                        color: activeTab === 'resume' ? 'white' : '#6b7280',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    📄 Resume
                                </button>

                                <button
                                    onClick={() => setActiveTab('jobs')}
                                    style={{
                                        padding: '8px 16px',
                                        background: activeTab === 'jobs' ? '#6366f1' : 'transparent',
                                        color: activeTab === 'jobs' ? 'white' : '#6b7280',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    🎯 Jobs
                                </button>

                                {/* Saved Jobs Button */}
                                <button
                                    onClick={() => setActiveTab('saved')}
                                    style={{
                                        padding: '8px 16px',
                                        background: activeTab === 'saved' ? '#6366f1' : 'transparent',
                                        color: activeTab === 'saved' ? 'white' : '#6b7280',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    💾 Saved
                                </button>

                                {/*Leaning tab*/}
                                <button
                                    onClick={() => setActiveTab('learning')}
                                    style={{
                                        padding: '8px 16px',
                                        background: activeTab === 'learning' ? '#6366f1' : 'transparent',
                                        color: activeTab === 'learning' ? 'white' : '#6b7280',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    🧠 Learning
                                </button>

                                {/* ADMIN PANEL BUTTON */}
                                {isAdmin && (
                                    <button
                                        onClick={() => setActiveTab('admin')}
                                        style={{
                                            padding: '8px 16px',
                                            background: activeTab === 'admin' ? '#6366f1' : 'transparent',
                                            color: activeTab === 'admin' ? 'white' : '#6b7280',
                                            border: 'none',
                                            borderRadius: '8px',
                                            fontSize: '14px',
                                            fontWeight: '500',
                                            cursor: 'pointer',
                                            transition: 'all 0.2s'
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
                                        padding: '8px 16px',
                                        background: '#6366f1',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                    onMouseOver={(e) => e.target.style.background = '#4f46e5'}
                                    onMouseOut={(e) => e.target.style.background = '#6366f1'}
                                >
                                    📤 Upload New Resume
                                </button>
                            )}

                            <span style={{ fontSize: '14px', color: '#6b7280' }}>
                                👋 {userEmail}
                            </span>
                            <button
                                onClick={handleLogout}
                                style={{
                                    padding: '8px 16px',
                                    background: '#ef4444',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '8px',
                                    fontSize: '14px',
                                    fontWeight: '500',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s'
                                }}
                                onMouseOver={(e) => e.target.style.background = '#dc2626'}
                                onMouseOut={(e) => e.target.style.background = '#ef4444'}
                            >
                                Sign Out
                            </button>
                        </div>
                    </div>

                    <div style={{ padding: '30px 40px', maxWidth: '1400px', margin: '0 auto' }}>
                        {/* Profile Section */}
                        <Profile userInfo={userInfo} setUserInfo={setUserInfo} />

                        {/* Job Description Text Area */}
                        {activeTab === 'resume' && (
                            <div style={{ marginBottom: '30px' }}>
                                <h3 style={{ color: '#1f2937' }}>Optional: Job Description Analysis</h3>
                                <textarea
                                    value={jobDescription}
                                    onChange={(e) => setJobDescription(e.target.value)}
                                    placeholder="Paste the job description here to analyze skill gaps..."
                                    style={{
                                        width: '100%',
                                        minHeight: '150px',
                                        padding: '15px',
                                        borderRadius: '12px',
                                        border: '1px solid #d1d5db',
                                        fontSize: '14px',
                                        fontFamily: 'inherit',
                                        boxSizing: 'border-box'
                                    }}
                                />
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
                                      <OutputViewer data={parsedData} />
                                    </>
                                )}
                            </>
                        )}

                        {activeTab === 'jobs' && (
                            <JobRecommendations
                                userEmail={userEmail}
                                initialJobs={recommendedJobs}
                                onNavigateToLearning={handleNavigateToLearning}
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