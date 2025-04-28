import React, { useState, useEffect } from 'react';
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
    const [userInfo, setUserInfo] = useState(initialUserInfo); // Use initial state object

    // Check local storage for login status ONCE on initial mount
    useEffect(() => {
        const loggedInStatus = localStorage.getItem('loggedIn');
        const savedEmail = localStorage.getItem('userEmail');

        if (loggedInStatus === 'true' && savedEmail) {
            // If logged in status is persisted, load user-specific data
            const savedUserProfile = localStorage.getItem(`userInfo_${savedEmail}`);
            setLoggedIn(true);
            setUserEmail(savedEmail);
            if (savedUserProfile) {
                setUserInfo(JSON.parse(savedUserProfile)); // Load specific profile
            } else {
                setUserInfo(initialUserInfo); // Or reset to blank if none saved
            }
        } else {
            // Ensure clean state if not logged in according to localStorage
            setLoggedIn(false);
            setUserEmail('');
            setUserInfo(initialUserInfo);
        }
    }, []); // Empty dependency array means run only on mount

    const handleLoginSuccess = (email) => {
        // Set basic login state
        setLoggedIn(true);
        setUserEmail(email);
        localStorage.setItem('loggedIn', 'true');
        localStorage.setItem('userEmail', email);

        // Load user-specific profile or set to blank
        const savedUserProfile = localStorage.getItem(`userInfo_${email}`);
        if (savedUserProfile) {
            setUserInfo(JSON.parse(savedUserProfile));
        } else {
            setUserInfo(initialUserInfo); // Start with a blank profile for new/empty users
        }
        setParsedData([]); // Clear any previous parsed data
    };

    const handleLogout = () => {
        // Clear local storage
        localStorage.removeItem('loggedIn');
        localStorage.removeItem('userEmail');
        // Optionally remove the specific user's profile, or leave it for next login
        // localStorage.removeItem(`userInfo_${userEmail}`); // Uncomment if you want to clear saved profile on logout

        // Reset application state
        setLoggedIn(false);
        setUserEmail('');
        setUserInfo(initialUserInfo);
        setParsedData([]);
    };

    // Save userInfo whenever it changes WHILE logged in
    useEffect(() => {
        // Only save if logged in and email is known
        if (loggedIn && userEmail) {
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }
        // Dependency array: this effect runs when userInfo, loggedIn, or userEmail changes
    }, [userInfo, loggedIn, userEmail]);

    return (
        <div className="App">
            <h1 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>LandIt — Smart Document Parser</h1>

            {!loggedIn ? (
                <>
                    <h2>Login to Continue</h2>
                    {/* Pass the updated handler */}
                    <Login onLoginSuccess={handleLoginSuccess} />
                </>
            ) : (
                <>
                    <button
                        onClick={handleLogout} // Use the updated handler
                        style={{ position: 'absolute', top: '20px', right: '20px', padding: '0.5rem 1rem' }}
                    >
                        Sign Out
                    </button>

                    {/* Profile uses the current userInfo state */}
                    <Profile userInfo={userInfo} setUserInfo={setUserInfo} />

                    <ResumeUploader onUploadSuccess={setParsedData} />
                    <OutputViewer data={parsedData} />
                </>
            )}
        </div>
    );
}

export default App;