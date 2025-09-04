const fs = require('fs');
const path = require('path');
const axios = require('axios');
const pdf = require('pdf-parse');
const mammoth = require('mammoth');

// spaCy API configuration
const SPACY_API_URL = 'http://127.0.0.1:8000/parse-resume';

/**
 * Advanced text preprocessing to clean up messy resume text
 * This is where most of the extraction problems come from
 */
function preprocessResumeText(rawText) {
    console.log(`🧹 Preprocessing text (${rawText.length} chars)`);

    let text = rawText;

    // 1. Fix encoding issues and normalize whitespace
    text = text
        .replace(/\r\n/g, '\n')           // Normalize line endings
        .replace(/\r/g, '\n')             // Handle old Mac line endings
        .replace(/\u00A0/g, ' ')          // Replace non-breaking spaces
        .replace(/[^\x20-\x7E\n]/g, '')   // Remove non-printable chars (except newlines)
        .replace(/\s+/g, ' ')             // Normalize multiple spaces
        .replace(/\n\s*\n/g, '\n');       // Remove empty lines

    // 2. Fix common OCR errors that break entity recognition
    text = text
        .replace(/([a-z])([A-Z])/g, '$1 $2')  // Add space between camelCase
        .replace(/(\d)([A-Za-z])/g, '$1 $2')  // Space between numbers and letters
        .replace(/([A-Za-z])(\d)/g, '$1 $2')  // Space between letters and numbers
        .replace(/([.!?])([A-Z])/g, '$1 $2')  // Space after punctuation
        .replace(/([,;:])([A-Za-z])/g, '$1 $2'); // Space after punctuation

    // 3. Normalize contact information (critical for entity recognition)
    // Fix phone numbers
    text = text.replace(/(\d{3})[\s.-]*(\d{3})[\s.-]*(\d{4})/g, '($1) $2-$3');

    // Fix email addresses (remove spaces around @ and .)
    text = text.replace(/\s*@\s*/g, '@');
    text = text.replace(/\s*\.\s*(com|org|net|edu|gov)/gi, '.$1');

    // 4. Fix common resume formatting issues
    // Add proper spacing around section headers
    const sectionHeaders = [
        'EXPERIENCE', 'EDUCATION', 'SKILLS', 'SUMMARY', 'OBJECTIVE',
        'PROJECTS', 'CERTIFICATIONS', 'AWARDS', 'LANGUAGES'
    ];

    sectionHeaders.forEach(header => {
        const regex = new RegExp(`\\b${header}\\b`, 'gi');
        text = text.replace(regex, `\n${header}\n`);
    });

    // 5. Improve sentence boundaries for better entity extraction
    text = text
        .replace(/\n+/g, '. ')            // Convert line breaks to sentence breaks
        .replace(/\.\s*\./g, '.')         // Remove duplicate periods
        .replace(/\s+/g, ' ')             // Final whitespace cleanup
        .trim();

    console.log(`✅ Preprocessed to ${text.length} chars`);
    return text;
}

/**
 * Split long text into smaller chunks that spaCy can handle better
 */
function chunkText(text, maxChunkSize = 2000) {
    if (text.length <= maxChunkSize) {
        return [text];
    }

    const chunks = [];
    const sentences = text.split(/[.!?]+\s+/);
    let currentChunk = '';

    for (const sentence of sentences) {
        if (currentChunk.length + sentence.length > maxChunkSize) {
            if (currentChunk) {
                chunks.push(currentChunk.trim());
                currentChunk = sentence;
            } else {
                // Sentence is too long, split it further
                chunks.push(sentence.substring(0, maxChunkSize));
            }
        } else {
            currentChunk += (currentChunk ? '. ' : '') + sentence;
        }
    }

    if (currentChunk) {
        chunks.push(currentChunk.trim());
    }

    return chunks;
}

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
 * Call the spaCy API with improved error handling and chunking
 */
async function callSpacyAPI(text) {
    try {
        console.log('🔍 Calling spaCy API for entity extraction...');

        // Preprocess the text first
        const cleanText = preprocessResumeText(text);

        // Split into chunks if too long
        const chunks = chunkText(cleanText);
        console.log(`📊 Split into ${chunks.length} chunks for processing`);

        let allEntities = [];
        let totalOffset = 0;

        // Process each chunk
        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            console.log(`🔄 Processing chunk ${i + 1}/${chunks.length} (${chunk.length} chars)`);

            try {
                const response = await axios.post(SPACY_API_URL, {
                    text: chunk
                }, {
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    timeout: 30000 // 30 second timeout
                });

                if (response.data.entities && Array.isArray(response.data.entities)) {
                    // Adjust entity positions for chunk offset
                    const chunkEntities = response.data.entities.map(entity => ({
                        ...entity,
                        start: (entity.start || 0) + totalOffset,
                        end: (entity.end || entity.start || 0) + totalOffset
                    }));

                    allEntities.push(...chunkEntities);
                    console.log(`✅ Found ${chunkEntities.length} entities in chunk ${i + 1}`);
                }
            } catch (chunkError) {
                console.warn(`⚠️ Chunk ${i + 1} failed: ${chunkError.message}`);
                // Continue with other chunks
            }

            totalOffset += chunk.length + 2; // +2 for ". " separator
        }

        console.log(`✅ spaCy API completed: ${allEntities.length} total entities`);

        // Post-process entities to remove duplicates and clean up
        const cleanedEntities = postProcessEntities(allEntities, cleanText);

        return {
            entities: cleanedEntities,
            text: cleanText,
            originalText: text,
            chunksProcessed: chunks.length
        };

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
 * Post-process entities to remove duplicates and improve quality
 */
function postProcessEntities(entities, text) {
    console.log(`🧹 Post-processing ${entities.length} entities`);

    // Remove duplicates and invalid entities
    const seen = new Set();
    const cleanedEntities = [];

    for (const entity of entities) {
        // Skip empty or whitespace-only entities
        if (!entity.text || !entity.text.trim()) {
            continue;
        }

        // Create a unique key for deduplication
        const key = `${entity.text.trim().toLowerCase()}_${entity.label}`;
        if (seen.has(key)) {
            continue;
        }
        seen.add(key);

        // Clean up entity text
        const cleanText = entity.text.trim();

        // Skip obviously bad entities
        if (cleanText.length > 100 || cleanText.length < 2) {
            continue;
        }

        // Skip entities that are just punctuation or numbers
        if (/^[^\w\s]*$/.test(cleanText) || /^\d+$/.test(cleanText)) {
            continue;
        }

        cleanedEntities.push({
            ...entity,
            text: cleanText
        });
    }

    console.log(`✅ Cleaned to ${cleanedEntities.length} entities`);
    return cleanedEntities;
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
        value: entity.text,
        confidence: entity.confidence || 0.8 // Add confidence if available
    }));
}

/**
 * Main resume parsing controller with improved error handling
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
            // Call spaCy API for entity extraction (now with preprocessing)
            spacyResponse = await callSpacyAPI(extractedText);
        } catch (spacyError) {
            console.error('❌ spaCy API call failed:', spacyError.message);
            return res.status(500).json({
                error: 'Entity extraction failed',
                details: spacyError.message,
                troubleshooting: {
                    step1: 'Make sure your spaCy FastAPI server is running on port 8000',
                    step2: 'Check if the spaCy model is properly loaded',
                    step3: 'Verify the API endpoint is accessible at http://localhost:8000/parse-resume',
                    step4: 'Check the server logs for preprocessing errors'
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

        // Send enhanced response
        res.json({
            success: true,
            extracted: formattedEntities,
            metadata: {
                totalEntities: formattedEntities.length,
                fileSize: req.file.size,
                fileName: req.file.originalname,
                originalTextLength: extractedText.length,
                processedTextLength: spacyResponse.text?.length || 0,
                chunksProcessed: spacyResponse.chunksProcessed || 1,
                processingEngine: 'custom_spacy_model_v2'
            },
            debug: {
                // Include some debug info to help troubleshoot
                textSample: spacyResponse.text?.substring(0, 200) + '...',
                entityTypes: [...new Set(formattedEntities.map(e => e.type))],
                processingSteps: [
                    'Text extraction',
                    'Text preprocessing',
                    'Text chunking',
                    'Entity extraction',
                    'Post-processing'
                ]
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