const { DocumentProcessorServiceClient } = require('@google-cloud/documentai').v1;
const fs = require('fs');

const client = new DocumentProcessorServiceClient({
    keyFilename: './config/google-service-key.json',
});

const projectId = '884257115550';
const location = 'us';
const processorId = '7aa0060393f9f46';
const name = `projects/${projectId}/locations/${location}/processors/${processorId}`;

exports.parseResume = async (req, res) => {
    try {
        const fileBuffer = fs.readFileSync(req.file.path);
        const encodedImage = fileBuffer.toString('base64');

        const request = {
            name,
            rawDocument: {
                content: encodedImage,
                mimeType: 'application/pdf',
            },
        };

        const [result] = await client.processDocument(request);
        const document = result.document;

        const parsed = document.entities.map(entity => ({
            type: entity.type,
            value: entity.mentionText,
        }));

        res.json({ extracted: parsed });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Resume processing failed', details: err.message });
    }
};
