import React, { useState } from 'react';
import ResumeUploader from './components/ResumeUploader';
import OutputViewer from './components/OutputViewer';
import Login from "./components/Login";
import './App.css';

function App() {
    const [parsedData, setParsedData] = useState([]);
    const [loggedIn, setLoggedIn] = useState(false);

    const handleLogout = () => {
        setLoggedIn(false);
        setParsedData([]);
    };

    return (
        <div className="App">
            <h1 style={{ fontWeight: 'bold', marginBottom: '1rem' }}>LandIt — Smart Document Parser</h1>

            {/* If not logged in, show login screen */}
            {!loggedIn ? (
                <>
                    <h2>Login to continue</h2>
                    <Login onLoginSuccess={() => setLoggedIn(true)} />
                </>
            ) : (
                <>

                <button
                    onClick={handleLogout}
                    style={{ position: 'absolute', top: '20px', right: '20px', padding: '0.5rem 1rem' }}
                >
                    Sign Out
                </button>

                <ResumeUploader onUploadSuccess={setParsedData} />
                <OutputViewer data={parsedData} />
                </>
            )}
        </div>
    );
}

export default App;