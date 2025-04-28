import React, { useState, useEffect } from 'react';
import ResumeUploader from './components/ResumeUploader';
import OutputViewer from './components/OutputViewer';
import Login from "./components/Login";
import Profile from './components/Profile';
import './App.css';

function App() {
    const [parsedData, setParsedData] = useState([]);
    const [loggedIn, setLoggedIn] = useState(false);
    const [userEmail, setUserEmail] = useState('');
    const [userInfo, setUserInfo] = useState({
        fullName: '',
        age: '',
        profession: '',
        country: ''
    });

    // Check local storage for login status
    useEffect(() => {
        const isLoggedIn = localStorage.getItem('loggedIn');
        const savedProfile = localStorage.getItem('userInfo');
        const savedEmail = localStorage.getItem('userEmail');

        if (isLoggedIn === 'true' && savedEmail) {
            setLoggedIn(true);
            setUserInfo(JSON.parse(savedProfile)); // when user loged in, we use their own profile
        }

        if (savedProfile) {
            setUserInfo(JSON.parse(savedProfile)); // Load saved profile
        }
    }, []);

    const handleLoginSuccess = () => {
        setLoggedIn(true);
        setUserEmail(email);
        localStorage.setItem('loggedIn', 'true');
        localStorage.setItem('userEmail', email);
    };

    const handleLogout = () => {
        setLoggedIn(false);
        localStorage.removeItem('loggedIn');
        localStorage.removeItem('userInfo');
        setParsedData([]);
    };

    // Save userInfo under the users profile
    useEffect(() => {
        if (loggedIn && userEmail) {
            localStorage.setItem(`userInfo_${userEmail}`, JSON.stringify(userInfo));
        }
    }, [userInfo, loggedIn, userEmail]);

    return (
        <div className="App">
            <h1 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>LandIt — Smart Document Parser</h1>

            {/* If not logged in, show login screen */}
            {!loggedIn ? (
                <>
                    <h2>Login to Continue</h2>
                    <Login onLoginSuccess={handleLoginSuccess} />
                </>
            ) : (
                <>
                    <button
                        onClick={handleLogout}
                        style={{ position: 'absolute', top: '20px', right: '20px', padding: '0.5rem 1rem' }}
                    >
                        Sign Out
                    </button>

                    {/* New Profile section */}
                    <Profile userInfo={userInfo} setUserInfo={setUserInfo} />

                    {/* Resume uploader and output viewer */}
                    <ResumeUploader onUploadSuccess={setParsedData} />
                    <OutputViewer data={parsedData} />
                </>
            )}
        </div>
    );
}

export default App;