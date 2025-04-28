import React, { useState } from 'react';
import axios from 'axios';
import { auth, googleProvider } from '../firebase';
import { createUserWithEmailAndPassword, signInWithEmailAndPassword, signInWithPopup } from 'firebase/auth';

const Login = ({ onLoginSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLogin, setIsLogin] = useState(true);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const endpoint = isLogin
                ? 'http://localhost:5000/api/auth/login'
                : 'http://localhost:5000/api/auth/signup';

            const response = await axios.post(endpoint, { email, password });

            // Save token if you are returning one
            if (response.data.token) {
                localStorage.setItem('token', response.data.token);
            }

            onLoginSuccess();
        } catch (err) {
            console.error(err);
            alert('Login/signup failed.');
        }
    };

    const handleGoogleLogin = async () => {
        try {
            await signInWithPopup(auth, googleProvider);
            onLoginSuccess();
        } catch (error) {
            console.error(error);
            alert('Google Sign-in failed.');
        }
    };

    return (
        <div>
            <h2>{isLogin ? 'Login' : 'Sign Up'}</h2>
            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                />
                <br />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />
                <br />
                <button type="submit">{isLogin ? 'Login' : 'Sign Up'}</button>
            </form>

            {/* Insert Google Sign In Button */}
            <div style={{ marginTop: '1rem' }}>
                <button onClick={handleGoogleLogin}>
                    Sign in with Google
                </button>
            </div>

            <button onClick={() => setIsLogin(!isLogin)} style={{ marginTop: '1rem' }}>
                {isLogin ? 'Create an Account' : 'Already have an account? Log In'}
            </button>
        </div>
    );
};

export default Login;
