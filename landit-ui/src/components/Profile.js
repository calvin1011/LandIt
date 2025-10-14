import React, { useState } from 'react';

const Profile = ({ userInfo, setUserInfo }) => {
    const [editing, setEditing] = useState(false);

    const handleChange = (e) => {
        setUserInfo({
            ...userInfo,
            [e.target.name]: e.target.value
        });
    };

    const handleSave = () => {
        setEditing(false);
        // You can add validation or save logic here
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
            {/* Header */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '30px',
                paddingBottom: '20px',
                borderBottom: '2px solid #f1f5f9'
            }}>
                <div>
                    <h2 style={{
                        margin: 0,
                        fontSize: '24px',
                        fontWeight: '700',
                        color: '#1f2937',
                        marginBottom: '4px'
                    }}>
                        👤 Your Profile
                    </h2>
                    <p style={{
                        margin: 0,
                        fontSize: '14px',
                        color: '#6b7280'
                    }}>
                        {editing ? 'Update your information' : 'Your professional information'}
                    </p>
                </div>
                <button
                    onClick={() => editing ? handleSave() : setEditing(true)}
                    style={{
                        padding: '10px 24px',
                        background: editing ? '#10b981' : '#6366f1',
                        color: 'white',
                        border: 'none',
                        borderRadius: '10px',
                        fontSize: '14px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                    }}
                    onMouseOver={(e) => {
                        e.target.style.background = editing ? '#059669' : '#4f46e5';
                        e.target.style.transform = 'translateY(-1px)';
                        e.target.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                    }}
                    onMouseOut={(e) => {
                        e.target.style.background = editing ? '#10b981' : '#6366f1';
                        e.target.style.transform = 'translateY(0)';
                        e.target.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                    }}
                >
                    {editing ? (
                        <>
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            Save Changes
                        </>
                    ) : (
                        <>
                            <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Edit Profile
                        </>
                    )}
                </button>
            </div>

            {/* Profile Grid */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '20px'
            }}>
                {/* Personal Information Section */}
                <div style={{
                    gridColumn: 'span 2',
                    background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)',
                    padding: '20px',
                    borderRadius: '12px',
                    border: '1px solid #bae6fd'
                }}>
                    <h3 style={{
                        margin: '0 0 16px 0',
                        fontSize: '16px',
                        fontWeight: '600',
                        color: '#0c4a6e',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <span style={{ fontSize: '18px' }}>📋</span>
                        Personal Information
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                        {[
                            { key: 'fullName', label: 'Full Name', icon: '👤', placeholder: 'John Doe' },
                            { key: 'age', label: 'Age', icon: '📅', placeholder: '25' },
                            { key: 'profession', label: 'Profession', icon: '💼', placeholder: 'Software Engineer' }
                        ].map(field => (
                            <div key={field.key}>
                                <label style={{
                                    display: 'block',
                                    fontSize: '13px',
                                    fontWeight: '600',
                                    color: '#475569',
                                    marginBottom: '6px'
                                }}>
                                    {field.icon} {field.label}
                                </label>
                                {editing ? (
                                    <input
                                        type="text"
                                        name={field.key}
                                        value={userInfo[field.key]}
                                        onChange={handleChange}
                                        placeholder={field.placeholder}
                                        style={{
                                            width: '100%',
                                            padding: '10px 12px',
                                            border: '2px solid #cbd5e1',
                                            borderRadius: '8px',
                                            fontSize: '14px',
                                            background: 'white',
                                            outline: 'none',
                                            boxSizing: 'border-box',
                                            transition: 'all 0.2s'
                                        }}
                                        onFocus={(e) => {
                                            e.target.style.borderColor = '#3b82f6';
                                            e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                                        }}
                                        onBlur={(e) => {
                                            e.target.style.borderColor = '#cbd5e1';
                                            e.target.style.boxShadow = 'none';
                                        }}
                                    />
                                ) : (
                                    <div style={{
                                        padding: '10px 12px',
                                        background: 'white',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        color: userInfo[field.key] ? '#1f2937' : '#94a3b8',
                                        minHeight: '20px',
                                        border: '2px solid transparent'
                                    }}>
                                        {userInfo[field.key] || `Not set`}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Location Section */}
                <div style={{
                    gridColumn: 'span 2',
                    background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                    padding: '20px',
                    borderRadius: '12px',
                    border: '1px solid #fcd34d'
                }}>
                    <h3 style={{
                        margin: '0 0 16px 0',
                        fontSize: '16px',
                        fontWeight: '600',
                        color: '#78350f',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <span style={{ fontSize: '18px' }}>📍</span>
                        Location
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                        {[
                            { key: 'city', label: 'City', icon: '🏙️', placeholder: 'Dallas', required: true },
                            { key: 'state', label: 'State', icon: '📍', placeholder: 'TX', required: true },
                            { key: 'country', label: 'Country', icon: '🌍', placeholder: 'US' }
                        ].map(field => (
                            <div key={field.key}>
                                <label style={{
                                    display: 'block',
                                    fontSize: '13px',
                                    fontWeight: '600',
                                    color: '#475569',
                                    marginBottom: '6px'
                                }}>
                                    {field.icon} {field.label}
                                    {field.required && <span style={{ color: '#ef4444', marginLeft: '4px' }}>*</span>}
                                </label>
                                {editing ? (
                                    <input
                                        type="text"
                                        name={field.key}
                                        value={userInfo[field.key]}
                                        onChange={handleChange}
                                        placeholder={field.placeholder}
                                        style={{
                                            width: '100%',
                                            padding: '10px 12px',
                                            border: '2px solid #cbd5e1',
                                            borderRadius: '8px',
                                            fontSize: '14px',
                                            background: 'white',
                                            outline: 'none',
                                            boxSizing: 'border-box',
                                            transition: 'all 0.2s'
                                        }}
                                        onFocus={(e) => {
                                            e.target.style.borderColor = '#f59e0b';
                                            e.target.style.boxShadow = '0 0 0 3px rgba(245, 158, 11, 0.1)';
                                        }}
                                        onBlur={(e) => {
                                            e.target.style.borderColor = '#cbd5e1';
                                            e.target.style.boxShadow = 'none';
                                        }}
                                    />
                                ) : (
                                    <div style={{
                                        padding: '10px 12px',
                                        background: 'white',
                                        borderRadius: '8px',
                                        fontSize: '14px',
                                        fontWeight: '500',
                                        color: userInfo[field.key] ? '#1f2937' : '#94a3b8',
                                        minHeight: '20px',
                                        border: '2px solid transparent'
                                    }}>
                                        {userInfo[field.key] || `Not set`}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Info Banner */}
            {!editing && (!userInfo.city || !userInfo.state) && (
                <div style={{
                    marginTop: '20px',
                    padding: '12px 16px',
                    background: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '10px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    fontSize: '14px',
                    color: '#991b1b'
                }}>
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span>
                        <strong>Important:</strong> City and State are required for better job matching
                    </span>
                </div>
            )}
        </div>
    );
};

export default Profile;