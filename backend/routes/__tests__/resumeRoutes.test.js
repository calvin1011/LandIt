const request = require('supertest');
const express = require('express');
const resumeRoutes = require('backend/routes/resumeRoutes.js');
const resumeController = require('backend/controllers/resumeController.js');

// --- Mocking Dependencies ---

// 1. Mock the controller
// We replace the actual controller functions with Jest mock functions.
jest.mock('backend/controllers/resumeController.js', () => ({
    parseResume: jest.fn((req, res, next) => {
        // Default mock implementation: Simulate success
        res.status(200).json({ message: 'Mock success: Resume parsed' });
    }),
}));

// 2. Mock the multer middleware
// We mock multer().single() to return a simple middleware
// that just calls next(), bypassing the actual file upload logic for this test.
// This focuses the test on the routing logic itself.
jest.mock('multer', () => {
    const multer = () => ({
        single: jest.fn().mockReturnValue((req, res, next) => {
            // You could optionally add a dummy req.file here if your
            // controller mock needed it:
            // req.file = { originalname: 'test.pdf', buffer: Buffer.from('test') };
            next();
        }),
        // Mock other multer functions if you were using them (e.g., diskStorage)
        diskStorage: jest.fn(),
        memoryStorage: jest.fn(),
    });
    return multer;
});

// --- Test Setup ---

// Create a basic Express app instance for testing
const app = express();
// Mount the router onto the test app. You might use a base path like in your main app.
app.use('/api/resumes', resumeRoutes); // Example base path

// basic error handler for tests simulating controller errors calling next(err)
app.use((err, req, res, next) => {
    // console.error("Test Error Handler Caught:", err); // Optional: log errors during tests
    res.status(err.status || 500).json({ message: err.message || 'Internal Server Error' });
});

// --- Test Suite ---

describe('Resume Routes', () => {

    // Clear mocks after each test to ensure clean state
    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('POST /api/resumes/parse-resume', () => {
        it('should successfully call the parseResume controller and return 200', async () => {
            // Arrange: (Mock implementation is set up above)

            // Act: Make a request to the endpoint
            const response = await request(app)
                .post('/api/resumes/parse-resume')
                // We don't need to attach a real file because multer is mocked
                // .attach('resume', 'path/to/fake/resume.pdf') // Not needed here
                .send(); // Send the request

            // Assert:
            // 1. Check if the controller method was called
            expect(resumeController.parseResume).toHaveBeenCalledTimes(1);

            // 2. Check the response status and body (based on the mock implementation)
            expect(response.statusCode).toBe(200);
            expect(response.body).toEqual({ message: 'Mock success: Resume parsed' });

            // 3. Optional: Check if multer middleware was invoked (if needed)
            // This requires inspecting the mock created for multer().single()
            // const multer = require('multer'); // Get the mocked multer
            // expect(multer().single).toHaveBeenCalledWith('resume');
        });

        it('should handle errors thrown by the parseResume controller', async () => {
            // Arrange: Override the mock implementation for this specific test
            const errorMessage = 'Mock Error: Parsing failed';
            resumeController.parseResume.mockImplementationOnce((req, res, next) => {
                // Simulate the controller throwing an error
                throw new Error(errorMessage);
                // Or calling next(error)
                // const error = new Error(errorMessage);
                // error.status = 400; // Example status
                // next(error);
            });

            // Act: Make a request to the endpoint
            const response = await request(app)
                .post('/api/resumes/parse-resume')
                .send();

            // Assert:
            // 1. Check if the controller method was called
            expect(resumeController.parseResume).toHaveBeenCalledTimes(1);

            // 2. Check the response status and body (based on the error handler)
            // Note: The exact status code might depend on how your actual error handling middleware works.
            // Here we assume a generic 500 if the controller throws directly,
            // or the status set if using next(error).
            expect(response.statusCode).toBe(500); // Or 400 if next(error) was used with status
            expect(response.body).toEqual({ message: errorMessage }); // Or 'Internal Server Error' if error wasn't passed correctly
        });

        it('should handle errors passed via next() by the parseResume controller', async () => {
            // Arrange: Override the mock implementation for this specific test
            const errorMessage = 'Mock Error: Invalid file type';
            const errorStatus = 415; // Unsupported Media Type
            resumeController.parseResume.mockImplementationOnce((req, res, next) => {
                const error = new Error(errorMessage);
                error.status = errorStatus;
                next(error); // Simulate controller passing error to Express error handler
            });

            // Act: Make a request to the endpoint
            const response = await request(app)
                .post('/api/resumes/parse-resume')
                .send();

            // Assert:
            // 1. Check if the controller method was called
            expect(resumeController.parseResume).toHaveBeenCalledTimes(1);

            // 2. Check the response status and body (based on the test error handler)
            expect(response.statusCode).toBe(errorStatus);
            expect(response.body).toEqual({ message: errorMessage });
        });
    });

});