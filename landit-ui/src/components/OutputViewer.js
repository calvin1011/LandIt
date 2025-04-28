import React from 'react';

const OutputViewer = ({ data }) => {
    if (!data.length) return null;

    return (
        <div>
            <h2>Parsed Resume Data</h2>
            <ul>
                {data.map((item, index) => (
                    <li key={index}><strong>{item.type}:</strong> {item.value}</li>
                ))}
            </ul>
        </div>
    );
};

export default OutputViewer;
