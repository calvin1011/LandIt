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

const Login = ({ onLoginSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);
    const [rememberMe, setRememberMe] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleFirebaseAuth = async (authPromise, email) => {
        try {
            setLoading(true);
            setError('');

            // Set persistence based on "Remember Me" checkbox
            const persistence = rememberMe ? browserLocalPersistence : browserSessionPersistence;
            await setPersistence(auth, persistence);

            console.log('Auth persistence set to:', rememberMe ? 'LOCAL' : 'SESSION');

            // Perform authentication
            const result = await authPromise;
            const user = result.user;

            console.log('✅ Firebase auth successful:', user.email);

            // Call success handler
            onLoginSuccess(user.email, user);

        } catch (error) {
            console.error('❌ Firebase auth error:', error);

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
        await handleFirebaseAuth(signInWithPopup(auth, googleProvider), 'google-user');
    };

    return (
        <div style={{ maxWidth: '400px', margin: '0 auto', padding: '2rem' }}>
            <div style={{
                backgroundColor: 'white',
                padding: '2rem',
                borderRadius: '0.5rem',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                border: '1px solid #e5e7eb'
            }}>
                <h2 style={{
                    textAlign: 'center',
                    marginBottom: '1.5rem',
                    color: '#111827',
                    fontSize: '1.5rem'
                }}>
                    {isLogin ? '🔐 Login' : '📝 Sign Up'}
                </h2>

                {error && (
                    <div style={{
                        backgroundColor: '#fef2f2',
                        border: '1px solid #fecaca',
                        color: '#dc2626',
                        padding: '0.75rem',
                        borderRadius: '0.375rem',
                        marginBottom: '1rem',
                        fontSize: '0.875rem'
                    }}>
                        ⚠️ {error}
                    </div>
                )}

                <form onSubmit={handleEmailPasswordAuth}>
                    <div style={{ marginBottom: '1rem' }}>
                        <input
                            type="email"
                            placeholder="Email address"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                border: '1px solid #d1d5db',
                                borderRadius: '0.375rem',
                                fontSize: '1rem',
                                outline: 'none'
                            }}
                            required
                            disabled={loading}
                        />
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '0.75rem',
                                border: '1px solid #d1d5db',
                                borderRadius: '0.375rem',
                                fontSize: '1rem',
                                outline: 'none'
                            }}
                            required
                            disabled={loading}
                        />
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
                            style={{ cursor: 'pointer' }}
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
                        style={{
                            width: '100%',
                            backgroundColor: loading ? '#9ca3af' : '#2563eb',
                            color: 'white',
                            padding: '0.75rem',
                            borderRadius: '0.375rem',
                            border: 'none',
                            fontSize: '1rem',
                            fontWeight: '500',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            marginBottom: '1rem'
                        }}
                        disabled={loading}
                    >
                        {loading ? '⏳ Processing...' : (isLogin ? '🚀 Login' : '📝 Create Account')}
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
                    style={{
                        width: '100%',
                        backgroundColor: loading ? '#f3f4f6' : 'white',
                        color: '#374151',
                        padding: '0.75rem',
                        borderRadius: '0.375rem',
                        border: '1px solid #d1d5db',
                        fontSize: '1rem',
                        fontWeight: '500',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        marginBottom: '1rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem'
                    }}
                    disabled={loading}
                >
                    <span style={{ fontSize: '1.2rem' }}>🌐</span>
                    {loading ? 'Processing...' : 'Continue with Google'}
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
                            color: '#2563eb',
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
                    backgroundColor: '#f0f9ff',
                    borderRadius: '0.375rem',
                    fontSize: '0.75rem',
                    color: '#0369a1'
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