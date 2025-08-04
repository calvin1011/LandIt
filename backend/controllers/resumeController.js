const fs = require('fs');
const path = require('path');
const axios = require('axios');
const pdf = require('pdf-parse');
const mammoth = require('mammoth');

// spaCy API configuration
const SPACY_API_URL = 'http://127.0.0.1:8000/parse-resume';

/**
 * Extract text from PDF files
 */
async function extractTextFromPDF(filePath) {
    try {
        const dataBuffer = fs.readFileSync(filePath);
        const pdfData = await pdf(dataBuffer);
        return pdfData.text;
    } catch (error) {
        throw new Error(`PDF text extraction failed: ${error.message}`);
    }
}

/**
 * Extract text from DOCX files
 */
async function extractTextFromDOCX(filePath) {
    try {
        const result = await mammoth.extractRawText({ path: filePath });
        return result.value;
    } catch (error) {
        throw new Error(`DOCX text extraction failed: ${error.message}`);
    }
}

/**
 * Extract text from TXT files
 */
async function extractTextFromTXT(filePath) {
    try {
        return fs.readFileSync(filePath, 'utf-8');
    } catch (error) {
        throw new Error(`TXT file reading failed: ${error.message}`);
    }
}

/**
 * Extract text based on file type
 */
async function extractTextFromFile(filePath, mimeType) {
    console.log(`📄 Extracting text from: ${path.basename(filePath)} (${mimeType})`);

    let text = '';

    if (mimeType === 'application/pdf') {
        text = await extractTextFromPDF(filePath);
    } else if (mimeType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
        text = await extractTextFromDOCX(filePath);
    } else if (mimeType === 'application/msword') {
        throw new Error('Legacy .doc files are not supported. Please convert to .docx format.');
    } else if (mimeType === 'text/plain') {
        text = await extractTextFromTXT(filePath);
    } else {
        throw new Error(`Unsupported file type: ${mimeType}`);
    }

    if (!text || text.trim().length === 0) {
        throw new Error('No text could be extracted from the file');
    }

    console.log(`✅ Extracted ${text.length} characters`);
    return text.trim();
}

/**
 * Call the spaCy API to parse resume text
 */
async function callSpacyAPI(text) {
    try {
        console.log('🔍 Calling spaCy API for entity extraction...');

        const response = await axios.post(SPACY_API_URL, {
            text: text
        }, {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 30000 // 30 second timeout
        });

        console.log(`✅ spaCy API responded with ${response.data.entities?.length || 0} entities`);
        return response.data;

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            throw new Error('spaCy API is not running. Please start your FastAPI server on port 8000.');
        } else if (error.response) {
            throw new Error(`spaCy API error: ${error.response.status} - ${error.response.data?.detail || 'Unknown error'}`);
        } else if (error.code === 'ECONNABORTED') {
            throw new Error('spaCy API request timed out. The file might be too large.');
        } else {
            throw new Error(`Failed to call spaCy API: ${error.message}`);
        }
    }
}

/**
 * Format spaCy response to match expected frontend format
 */
function formatSpacyResponse(spacyResponse) {
    if (!spacyResponse.entities || !Array.isArray(spacyResponse.entities)) {
        return [];
    }

    // Convert from spaCy format: {text: "value", label: "TYPE"}
    // To expected format: {type: "TYPE", value: "value"}
    return spacyResponse.entities.map(entity => ({
        type: entity.label,
        value: entity.text
    }));
}

/**
 * Main resume parsing controller
 */
exports.parseResume = async (req, res) => {
    console.log('📄 Resume parsing request received');

    try {
        // Check if file was uploaded
        if (!req.file) {
            console.log('❌ No file uploaded');
            return res.status(400).json({
                error: 'No file uploaded',
                details: 'Please upload a resume file (PDF, DOCX, or TXT)'
            });
        }

        console.log('📁 File received:', {
            filename: req.file.filename,
            originalName: req.file.originalname,
            size: req.file.size,
            mimetype: req.file.mimetype,
            path: req.file.path
        });

        // Check if file exists
        if (!fs.existsSync(req.file.path)) {
            console.log('❌ Uploaded file not found:', req.file.path);
            return res.status(500).json({
                error: 'File processing error',
                details: 'Uploaded file could not be found'
            });
        }

        let extractedText;
        try {
            // Extract text from the uploaded file
            extractedText = await extractTextFromFile(req.file.path, req.file.mimetype);
        } catch (textError) {
            console.error('❌ Text extraction failed:', textError.message);
            return res.status(400).json({
                error: 'Text extraction failed',
                details: textError.message
            });
        }

        let spacyResponse;
        try {
            // Call spaCy API for entity extraction
            spacyResponse = await callSpacyAPI(extractedText);
        } catch (spacyError) {
            console.error('❌ spaCy API call failed:', spacyError.message);
            return res.status(500).json({
                error: 'Entity extraction failed',
                details: spacyError.message,
                troubleshooting: {
                    step1: 'Make sure your spaCy FastAPI server is running on port 8000',
                    step2: 'Check if the spaCy model is properly loaded',
                    step3: 'Verify the API endpoint is accessible at http://localhost:8000/parse-resume'
                }
            });
        }

        // Format the response
        const formattedEntities = formatSpacyResponse(spacyResponse);

        console.log(`✅ Successfully processed resume: ${formattedEntities.length} entities extracted`);

        // Clean up the uploaded file
        try {
            fs.unlinkSync(req.file.path);
            console.log('🗑️ Temporary file cleaned up');
        } catch (cleanupError) {
            console.warn('⚠️ Failed to clean up temporary file:', cleanupError.message);
        }

        // Send response in the format expected by your frontend
        res.json({
            success: true,
            extracted: formattedEntities,
            metadata: {
                totalEntities: formattedEntities.length,
                fileSize: req.file.size,
                fileName: req.file.originalname,
                textLength: extractedText.length,
                processingEngine: 'custom_spacy_model'
            }
        });

    } catch (error) {
        console.error('❌ Resume processing error:', error);

        // Clean up file if it exists
        if (req.file && req.file.path && fs.existsSync(req.file.path)) {
            try {
                fs.unlinkSync(req.file.path);
                console.log('🗑️ Temporary file cleaned up after error');
            } catch (cleanupError) {
                console.warn('⚠️ Failed to clean up temporary file after error:', cleanupError.message);
            }
        }

        res.status(500).json({
            error: 'Resume processing failed',
            details: error.message,
            timestamp: new Date().toISOString()
        });
    }
};