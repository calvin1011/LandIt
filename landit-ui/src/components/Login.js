import React, { useState } from 'react';
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithPopup,
    setPersistence,
    browserSessionPersistence,
    browserLocalPersistence
} from 'firebase/auth';
import { auth, googleProvider } from '../firebase';

const Login = ({ onLoginSuccess, firebaseConfigured = true }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);
    const [rememberMe, setRememberMe] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleFirebaseAuth = async (authPromise, email) => {
        if (!auth) return;
        try {
            setLoading(true);
            setError('');

            const persistence = rememberMe ? browserLocalPersistence : browserSessionPersistence;
            await setPersistence(auth, persistence);

            console.log('Auth persistence set to:', rememberMe ? 'LOCAL' : 'SESSION');

            // Perform authentication
            const result = await authPromise;
            const user = result.user;

            console.log('Firebase auth successful:', user.email);

            // Call success handler
            onLoginSuccess(user.email, user);

        } catch (error) {
            console.error('Firebase auth error:', error);

            // User-friendly error messages
            let errorMessage = 'Authentication failed. Please try again.';

            if (error.code === 'auth/user-not-found') {
                errorMessage = 'No account found with this email address.';
            } else if (error.code === 'auth/wrong-password') {
                errorMessage = 'Incorrect password. Please try again.';
            } else if (error.code === 'auth/email-already-in-use') {
                errorMessage = 'An account with this email already exists.';
            } else if (error.code === 'auth/weak-password') {
                errorMessage = 'Password should be at least 6 characters.';
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = 'Please enter a valid email address.';
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleEmailPasswordAuth = async (e) => {
        e.preventDefault();

        if (!email || !password) {
            setError('Please fill in all fields.');
            return;
        }

        const authPromise = isLogin
            ? signInWithEmailAndPassword(auth, email, password)
            : createUserWithEmailAndPassword(auth, email, password);

        await handleFirebaseAuth(authPromise, email);
    };

    const handleGoogleLogin = async () => {
        if (!auth || !googleProvider) return;
        await handleFirebaseAuth(signInWithPopup(auth, googleProvider), 'google-user');
    };

    if (!firebaseConfigured) {
        return (
            <div style={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '20px'
            }}>
                <div style={{
                    background: 'white',
                    padding: '32px',
                    borderRadius: '12px',
                    maxWidth: '420px',
                    textAlign: 'center',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
                }}>
                    <p style={{ margin: 0, fontSize: '16px', color: '#333' }}>
                        Firebase is not configured. Add <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: '4px' }}>REACT_APP_FIREBASE_API_KEY</code> and other Firebase env vars to <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: '4px' }}>landit-ui/.env</code>, then restart the dev server.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
            {/* Floating elements */}
            <div style={{
                position: 'absolute',
                top: '15%',
                left: '10%',
                fontSize: '24px',
                animation: 'float 3s ease-in-out infinite',
                animationDelay: '0s'
            }}>📄</div>
            <div style={{
                position: 'absolute',
                top: '20%',
                right: '15%',
                fontSize: '20px',
                animation: 'float 3s ease-in-out infinite',
                animationDelay: '1s'
            }}>✏️</div>
            <div style={{
                position: 'absolute',
                bottom: '25%',
                left: '8%',
                fontSize: '22px',
                animation: 'float 3s ease-in-out infinite',
                animationDelay: '2s'
            }}>📋</div>
            <div style={{
                position: 'absolute',
                bottom: '30%',
                right: '12%',
                fontSize: '18px',
                animation: 'float 3s ease-in-out infinite',
                animationDelay: '0.5s'
            }}>🖊️</div>

            <style>
                {`
                    @keyframes float {
                        0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.7; }
                        50% { transform: translateY(-10px) rotate(5deg); opacity: 1; }
                    }
                    
                    .login-input {
                        width: 100%;
                        padding: 16px 16px 16px 45px;
                        border: 2px solid #e1e5e9;
                        border-radius: 12px;
                        font-size: 16px;
                        background: #f8f9fa;
                        transition: all 0.3s ease;
                        box-sizing: border-box;
                        outline: none;
                    }
                    
                    .login-input:focus {
                        border-color: #667eea;
                        background: white;
                        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                    }
                    
                    .login-input:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                    }
                    
                    .input-icon {
                        position: absolute;
                        left: 15px;
                        top: 50%;
                        transform: translateY(-50%);
                        font-size: 18px;
                        color: #6c757d;
                    }
                    
                    .btn-primary {
                        width: 100%;
                        padding: 16px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 8px;
                    }
                    
                    .btn-primary:hover:not(:disabled) {
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                    }
                    
                    .btn-primary:disabled {
                        opacity: 0.7;
                        cursor: not-allowed;
                        transform: none;
                    }
                    
                    .btn-google {
                        width: 100%;
                        padding: 16px;
                        background: white;
                        color: #5f6368;
                        border: 2px solid #dadce0;
                        border-radius: 12px;
                        font-size: 16px;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 10px;
                    }
                    
                    .btn-google:hover:not(:disabled) {
                        background: #f8f9fa;
                        border-color: #c4c7c5;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    
                    .btn-google:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                    }
                    
                    .spinner {
                        width: 20px;
                        height: 20px;
                        border: 2px solid transparent;
                        border-top: 2px solid currentColor;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    }
                    
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                `}
            </style>

            <div style={{
                width: '100%',
                maxWidth: '420px',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '24px',
                padding: '40px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
                border: '1px solid rgba(255,255,255,0.2)'
            }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '64px',
                        height: '64px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        borderRadius: '16px',
                        marginBottom: '16px',
                        fontSize: '24px'
                    }}>📋</div>

                    <h1 style={{
                        fontSize: '32px',
                        fontWeight: '700',
                        margin: '0 0 8px 0',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text'
                    }}>LandIt</h1>

                    <p style={{
                        fontSize: '18px',
                        color: '#6c757d',
                        margin: '0 0 4px 0',
                        fontWeight: '500'
                    }}>Smart Document Parser</p>

                    <p style={{
                        fontSize: '14px',
                        color: '#8e9297',
                        margin: '0'
                    }}>Login to Continue</p>
                </div>

                <h2 style={{
                    textAlign: 'center',
                    marginBottom: '1.5rem',
                    color: '#2d3748',
                    fontSize: '1.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                }}>
                    {isLogin ? '🔐 Login' : '📝 Sign Up'}
                </h2>

                {error && (
                    <div style={{
                        backgroundColor: '#fff2f2',
                        border: '1px solid #fdb2b2',
                        color: '#c53030',
                        padding: '0.75rem',
                        borderRadius: '12px',
                        marginBottom: '1rem',
                        fontSize: '0.875rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <span>⚠️</span>
                        <span>{error}</span>
                    </div>
                )}

                <form onSubmit={handleEmailPasswordAuth}>
                    <div style={{ marginBottom: '1rem', position: 'relative' }}>
                        <input
                            type="email"
                            placeholder="Email address"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            className="login-input"
                            required
                            disabled={loading}
                        />
                        <span className="input-icon">📧</span>
                    </div>

                    <div style={{ marginBottom: '1rem', position: 'relative' }}>
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            className="login-input"
                            required
                            disabled={loading}
                        />
                        <span className="input-icon">🔒</span>
                    </div>

                    {/* Remember Me Checkbox */}
                    <div style={{
                        marginBottom: '1.5rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}>
                        <input
                            type="checkbox"
                            id="rememberMe"
                            checked={rememberMe}
                            onChange={e => setRememberMe(e.target.checked)}
                            style={{
                                cursor: 'pointer',
                                width: '16px',
                                height: '16px',
                                accentColor: '#667eea'
                            }}
                            disabled={loading}
                        />
                        <label
                            htmlFor="rememberMe"
                            style={{
                                fontSize: '0.875rem',
                                color: '#374151',
                                cursor: 'pointer',
                                userSelect: 'none'
                            }}
                        >
                            🔒 Remember me for 30 days
                        </label>
                    </div>

                    <button
                        type="submit"
                        className="btn-primary"
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <div className="spinner"></div>
                                <span>Processing...</span>
                            </>
                        ) : (
                            <>
                                <span>{isLogin ? '🚀' : '📝'}</span>
                                <span>{isLogin ? 'Login' : 'Create Account'}</span>
                            </>
                        )}
                    </button>
                </form>

                {/* Divider */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    margin: '1.5rem 0',
                    color: '#6b7280',
                    fontSize: '0.875rem'
                }}>
                    <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }}></div>
                    <span style={{ padding: '0 1rem' }}>or</span>
                    <div style={{ flex: 1, height: '1px', backgroundColor: '#e5e7eb' }}></div>
                </div>

                {/* Google Sign In Button */}
                <button
                    onClick={handleGoogleLogin}
                    className="btn-google"
                    disabled={loading}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    <span>{loading ? 'Processing...' : 'Continue with Google'}</span>
                </button>

                {/* Toggle Login/Signup */}
                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                    <button
                        onClick={() => {
                            setIsLogin(!isLogin);
                            setError('');
                        }}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: '#667eea',
                            cursor: 'pointer',
                            fontSize: '0.875rem',
                            textDecoration: 'underline'
                        }}
                        disabled={loading}
                    >
                        {isLogin
                            ? "Don't have an account? Sign up here"
                            : 'Already have an account? Login here'
                        }
                    </button>
                </div>

                {/* Remember Me Explanation */}
                <div style={{
                    marginTop: '1.5rem',
                    padding: '0.75rem',
                    backgroundColor: 'rgba(102, 126, 234, 0.05)',
                    borderRadius: '12px',
                    fontSize: '0.75rem',
                    color: '#6366f1',
                    border: '1px solid rgba(102, 126, 234, 0.1)'
                }}>
                    <strong>🔒 Security Note:</strong>
                    {rememberMe
                        ? ' You\'ll stay logged in for 30 days even after closing your browser.'
                        : ' You\'ll be logged out when you close your browser.'
                    }
                </div>
            </div>
        </div>
    );
};

export default Login;