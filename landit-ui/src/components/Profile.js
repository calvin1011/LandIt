import React, { useState } from 'react';

const Profile = ({ userInfo, setUserInfo }) => {
    const [editing, setEditing] = useState(false);

    const handleChange = (e) => {
        setUserInfo({
            ...userInfo,
            [e.target.name]: e.target.value
        });
    };

    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: '20px',
            padding: '30px',
            marginBottom: '30px',
            border: '1px solid rgba(255,255,255,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '600', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    👤 Your Profile
                </h2>
                <button
                    onClick={() => setEditing(!editing)}
                    style={{
                        padding: '8px 16px',
                        background: editing ? '#10b981' : '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        e.target.style.background = editing ? '#059669' : '#4f46e5';
                    }}
                    onMouseOut={(e) => {
                        e.target.style.background = editing ? '#10b981' : '#6366f1';
                    }}
                >
                    {editing ? 'Save Profile' : 'Edit Profile'}
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
                {[
                    { key: 'fullName', label: 'Full Name', icon: '👤' },
                    { key: 'age', label: 'Age', icon: '📅' },
                    { key: 'profession', label: 'Profession', icon: '💼' },
                    { key: 'country', label: 'Country', icon: '🌍' }
                ].map(field => (
                    <div key={field.key} style={{
                        padding: '15px',
                        background: '#f8fafc',
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        transition: 'all 0.2s'
                    }}>
                        <label style={{
                            display: 'block',
                            fontSize: '12px',
                            fontWeight: '600',
                            color: '#6b7280',
                            marginBottom: '8px',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                        }}>
                            {field.icon} {field.label}
                        </label>
                        {editing ? (
                            <input
                                type="text"
                                name={field.key}
                                value={userInfo[field.key]}
                                onChange={handleChange}
                                style={{
                                    width: '100%',
                                    padding: '8px 12px',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '6px',
                                    fontSize: '14px',
                                    background: 'white',
                                    outline: 'none',
                                    boxSizing: 'border-box',
                                    transition: 'border-color 0.2s'
                                }}
                                placeholder={`Enter your ${field.label.toLowerCase()}`}
                                onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                                onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
                            />
                        ) : (
                            <div style={{
                                fontSize: '14px',
                                fontWeight: '500',
                                color: userInfo[field.key] ? '#1f2937' : '#9ca3af',
                                minHeight: '20px'
                            }}>
                                {userInfo[field.key] || `No ${field.label.toLowerCase()} set`}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Profile;