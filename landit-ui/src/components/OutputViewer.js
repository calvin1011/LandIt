import React from 'react';

const OutputViewer = ({ data }) => {
    if (!data || !data.length) return null;

    // Group data by categories
    const groupedData = {
        personal: data.filter(item => ['NAME', 'EMAIL', 'PHONE', 'ADDRESS', 'LOCATION'].includes(item.type)),
        experience: data.filter(item => ['TITLE', 'COMPANY', 'EXPERIENCE', 'ACHIEVEMENT', 'LEADERSHIP'].includes(item.type)),
        education: data.filter(item => ['EDUCATION', 'DEGREE', 'FIELD', 'GRAD_YEAR', 'GPA'].includes(item.type)),
        skills: data.filter(item => ['SKILL', 'TECHNOLOGY', 'TOOL', 'CERTIFICATION', 'TECHNOLOGY_TYPE'].includes(item.type)),
        other: data.filter(item => !['NAME', 'EMAIL', 'PHONE', 'ADDRESS', 'LOCATION', 'TITLE', 'COMPANY', 'EXPERIENCE', 'ACHIEVEMENT', 'LEADERSHIP', 'EDUCATION', 'DEGREE', 'FIELD', 'GRAD_YEAR', 'GPA', 'SKILL', 'TECHNOLOGY', 'TOOL', 'CERTIFICATION', 'TECHNOLOGY_TYPE'].includes(item.type))
    };

    const categoryIcons = {
        personal: '👤',
        experience: '💼',
        education: '🎓',
        skills: '⚡',
        other: '📋'
    };

    const categoryColors = {
        personal: { bg: '#eff6ff', border: '#bfdbfe', text: '#1e40af', accent: '#3b82f6' },
        experience: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534', accent: '#22c55e' },
        education: { bg: '#faf5ff', border: '#d8b4fe', text: '#7c2d12', accent: '#a855f7' },
        skills: { bg: '#fff7ed', border: '#fed7aa', text: '#c2410c', accent: '#f97316' },
        other: { bg: '#f9fafb', border: '#d1d5db', text: '#374151', accent: '#6b7280' }
    };

    return (
        <>
            {/* Results Header */}
            <div style={{
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderRadius: '20px',
                padding: '30px',
                marginBottom: '30px',
                border: '1px solid rgba(255,255,255,0.2)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
            }}>
                <div style={{ marginBottom: '20px' }}>
                    <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        👁️ Extracted Information
                    </h2>
                    <p style={{ margin: 0, fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                        Found {data.length} data points including names, skills, experience, and more.
                    </p>
                </div>

                {/* Quick Stats */}
                <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                    {Object.entries(groupedData).map(([category, items]) => (
                        items.length > 0 && (
                            <div key={category} style={{
                                padding: '15px 20px',
                                background: categoryColors[category].bg,
                                border: `1px solid ${categoryColors[category].border}`,
                                borderRadius: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                minWidth: '120px',
                                transition: 'transform 0.2s',
                                cursor: 'default'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                            onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                            >
                                <span style={{ fontSize: '20px' }}>{categoryIcons[category]}</span>
                                <div>
                                    <div style={{ fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
                                        {items.length}
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#6b7280', textTransform: 'capitalize' }}>
                                        {category}
                                    </div>
                                </div>
                            </div>
                        )
                    ))}
                </div>
            </div>

            {/* Categorized Data Display */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '25px' }}>
                {Object.entries(groupedData).map(([category, items]) => (
                    items.length > 0 && (
                        <div key={category} style={{
                            background: 'rgba(255, 255, 255, 0.95)',
                            backdropFilter: 'blur(10px)',
                            borderRadius: '20px',
                            padding: '25px',
                            border: '1px solid rgba(255,255,255,0.2)',
                            boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                            transition: 'transform 0.2s'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                        >
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                marginBottom: '20px',
                                paddingBottom: '15px',
                                borderBottom: `2px solid ${categoryColors[category].border}`
                            }}>
                                <span style={{ fontSize: '24px' }}>{categoryIcons[category]}</span>
                                <h3 style={{
                                    margin: 0,
                                    fontSize: '18px',
                                    fontWeight: '600',
                                    color: '#1f2937',
                                    textTransform: 'capitalize'
                                }}>
                                    {category} Information
                                </h3>
                                <span style={{
                                    background: categoryColors[category].accent,
                                    color: 'white',
                                    padding: '2px 8px',
                                    borderRadius: '12px',
                                    fontSize: '12px',
                                    fontWeight: '500'
                                }}>
                                    {items.length}
                                </span>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                {items.map((item, index) => (
                                    <div key={index} style={{
                                        padding: '12px 15px',
                                        background: categoryColors[category].bg,
                                        border: `1px solid ${categoryColors[category].border}`,
                                        borderRadius: '10px',
                                        transition: 'all 0.2s',
                                        cursor: 'default'
                                    }}
                                    onMouseOver={(e) => {
                                        e.currentTarget.style.background = '#ffffff';
                                        e.currentTarget.style.transform = 'scale(1.02)';
                                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                    }}
                                    onMouseOut={(e) => {
                                        e.currentTarget.style.background = categoryColors[category].bg;
                                        e.currentTarget.style.transform = 'scale(1)';
                                        e.currentTarget.style.boxShadow = 'none';
                                    }}
                                    >
                                        <div style={{
                                            fontSize: '11px',
                                            fontWeight: '600',
                                            color: '#6b7280',
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.5px',
                                            marginBottom: '4px'
                                        }}>
                                            {(item.type || 'UNCATEGORIZED').replace(/_/g, ' ')}
                                        </div>
                                        <div style={{
                                            fontSize: '14px',
                                            fontWeight: '500',
                                            color: '#1f2937',
                                            lineHeight: '1.4'
                                        }}>
                                            {item.value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )
                ))}
            </div>
        </>
    );
};

export default OutputViewer;