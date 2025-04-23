require('dotenv').config();
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const PROJECT_ID = process.env.PROJECT_ID;
const LOCATION = 'us';
const PROCESSOR_ID = process.env.PROCESSOR_ID;
const API_KEY = process.env.GOOGLE_DOC_AI_KEY;

exports.parseResume = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        const filePath = req.file.path;
        const fileData = fs.readFileSync(filePath);
        const encodedFile = Buffer.from(fileData).toString('base64');

        const endpoint = `https://us-documentai.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/processors/${PROCESSOR_ID}:process?key=${API_KEY}`;

        const response = await axios.post(endpoint, {
            rawDocument: {
                content: encodedFile,
                mimeType: 'application/pdf'
            }
        }, {
            headers: { 'Content-Type': 'application/json' }
        });

        const entities = response.data.document.entities || [];
        const parsed = entities.map(e => ({
            type: e.type,
            value: e.mentionText
        }));

        res.status(200).json({ extracted: parsed });
    } catch (err) {
        console.error(err.message);
        res.status(500).json({ error: 'Failed to parse resume', details: err.message });
    }
};
