import React, { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';
import ResumeUploader from './components/ResumeUploader';
import OutputViewer from './components/OutputViewer';
import Login from "./components/Login";
import Profile from './components/Profile';
import './App.css';

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
    const [loading, setLoading] = useState(true); // Loading state for auth check
    const [firebaseUser, setFirebaseUser] = useState(null);

    // Firebase Auth State Listener - This is the key fix!
    useEffect(() => {
        console.log('🔥 Setting up Firebase auth listener...');

        const unsubscribe = onAuthStateChanged(auth, (user) => {
            console.log('🔥 Firebase auth state changed:', user ? user.email : 'No user');

            if (user) {
                // User is signed in
                const email = user.email;
                setFirebaseUser(user);
                setLoggedIn(true);
                setUserEmail(email);

                // Load user-specific profile data
                const savedUserProfile = localStorage.getItem(`userInfo_${email}`);
                if (savedUserProfile) {
                    console.log('📱 Loading saved profile for:', email);
                    setUserInfo(JSON.parse(savedUserProfile));
                } else {
                    console.log('📱 No saved profile, using initial state for:', email);
                    setUserInfo(initialUserInfo);
                }

                // Store current user for manual reference
                localStorage.setItem('currentUser', email);

            } else {
                // User is signed out
                console.log('🚪 User signed out, clearing state');
                setFirebaseUser(null);
                setLoggedIn(false);
                setUserEmail('');
                setUserInfo(initialUserInfo);
                setParsedData([]);
                localStorage.removeItem('currentUser');
            }

            setLoading(false); // Auth check complete
        });

        // Cleanup subscription on unmount
        return () => {
            console.log('🧹 Cleaning up Firebase auth listener');
            unsubscribe();
        };
    }, []);

    const handleLoginSuccess = (email, user = null) => {
        console.log('✅ Login successful for:', email);

        // Firebase auth state will be handled by the listener above
        // Just clear any previous parsed data
        setParsedData([]);

        // The auth listener will handle setting user state and loading profile
    };

    const handleLogout = async () => {
        console.log('🚪 Logging out...');

        try {
            // Sign out from Firebase (this will trigger the auth state listener)
            await auth.signOut();

            // Additional cleanup (the auth listener will handle most of this)
            setParsedData([]);

        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    const handleAccountSwitch = (newEmail) => {
        console.log('🔄 Account switch detected:', userEmail, '→', newEmail);

        // Save current user's data before switching
        if (userEmail && userEmail !== newEmail) {
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }

        // Clear parsed data when switching accounts
        setParsedData([]);

        // Load new user's data
        const newUserProfile = localStorage.getItem(`userInfo_${newEmail}`);
        if (newUserProfile) {
            setUserInfo(JSON.parse(newUserProfile));
        } else {
            setUserInfo(initialUserInfo);
        }
    };

    // Save userInfo whenever it changes (but only if logged in)
    useEffect(() => {
        if (loggedIn && userEmail && !loading) {
            console.log('💾 Saving profile data for:', userEmail);
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }
    }, [userInfo, loggedIn, userEmail, loading]);

    // Check for account switches
    useEffect(() => {
        const lastUser = localStorage.getItem('currentUser');
        if (lastUser && userEmail && lastUser !== userEmail) {
            handleAccountSwitch(userEmail);
        }
    }, [userEmail]);

    // Show loading spinner while checking auth state
    if (loading) {
        return (
            <div className="App">
                <h1 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>
                    LandIt — Smart Document Parser
                </h1>
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '200px',
                    fontSize: '1.2rem',
                    color: '#6b7280'
                }}>
                    🔄 Checking authentication...
                </div>
            </div>
        );
    }

    return (
        <div className="App">
            <h1 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>
                LandIt — Smart Document Parser
            </h1>

            {!loggedIn ? (
                <>
                    <h2>Login to Continue</h2>
                    <Login onLoginSuccess={handleLoginSuccess} />
                </>
            ) : (
                <>
                    <div style={{
                        position: 'absolute',
                        top: '20px',
                        right: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px'
                    }}>
                        <span style={{
                            fontSize: '0.9rem',
                            color: '#6b7280',
                            marginRight: '10px'
                        }}>
                            👋 {userEmail}
                        </span>
                        <button
                            onClick={handleLogout}
                            style={{
                                padding: '0.5rem 1rem',
                                backgroundColor: '#ef4444',
                                color: 'white',
                                border: 'none',
                                borderRadius: '0.375rem',
                                cursor: 'pointer'
                            }}
                        >
                            Sign Out
                        </button>
                    </div>

                    <Profile userInfo={userInfo} setUserInfo={setUserInfo} />
                    <ResumeUploader onUploadSuccess={setParsedData} />
                    <OutputViewer data={parsedData} />
                </>
            )}
        </div>
    );
}

export default App;