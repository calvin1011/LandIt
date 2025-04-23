const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const resumeController = require('../controllers/resumeController');

// Multer setup for file uploads
const upload = multer({ dest: 'uploads/' });

router.post('/parse-resume', upload.single('resume'), resumeController.parseResume);

module.exports = router;
