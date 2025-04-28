import React, { useState } from 'react';
import axios from 'axios';

const ResumeUploader = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);

    const handleUpload = async () => {
        if (!file) return alert("Please select a file.");

        const formData = new FormData();
        formData.append('resume', file);

        try {
            const response = await axios.post('http://localhost:5000/api/parse-resume', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            onUploadSuccess(response.data.extracted);
        } catch (err) {
            console.error(err);
            alert("Failed to parse resume.");
        }
    };

    return (
        <div>
            <h2>Upload Resume</h2>
            <input type="file" accept="application/pdf" onChange={e => setFile(e.target.files[0])} />
            <button onClick={handleUpload}>Submit</button>
        </div>
    );
};

export default ResumeUploader;
