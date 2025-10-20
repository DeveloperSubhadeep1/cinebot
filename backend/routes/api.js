const express = require('express');
const { getDB } = require('../db');
const { ObjectId } = require('mongodb');
const rateLimit = require('express-rate-limit');
const fs = require('fs');
const path = require('path');
const { GoogleGenAI, Type } = require('@google/genai');

const router = express.Router();

// Initialize Gemini AI Client
// IMPORTANT: Ensure API_KEY is set in your .env file for the backend.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const metadataSchema = {
    type: Type.OBJECT,
    properties: {
        title: { type: Type.STRING, description: 'The official movie title.' },
        year: { type: Type.STRING, description: 'The release year of the movie.' },
        summary: { type: Type.STRING, description: 'A concise, one-sentence plot summary.' },
        posterUrl: { type: Type.STRING, description: 'A publicly accessible HTTPS URL for the movie poster image.' },
    },
    required: ['title', 'year', 'summary', 'posterUrl'],
};

// Helper to escape regex special characters
function escapeRegex(string) {
    return string.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
}

// Rate limiter for download/stream endpoints
const downloadLimiter = rateLimit({
	windowMs: 15 * 60 * 1000, // 15 minutes
	max: 20, // Limit each IP to 20 requests per windowMs
	standardHeaders: true,
	legacyHeaders: false,
    message: 'Too many requests from this IP, please try again after 15 minutes',
});

// Rate limiter for metadata generation to protect API quota
const metadataLimiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 30, // Limit each IP to 30 requests per minute
    standardHeaders: true,
    legacyHeaders: false,
    message: 'Too many metadata requests, please slow down.',
});

router.get('/ping', (req, res) => {
    res.status(200).send('pong');
});

router.get('/about', async (req, res) => {
    try {
        const db = getDB();
        const totalFiles = await db.collection('files').countDocuments();
        res.json({
            totalFiles,
            version: '1.0.0',
            description: 'CineBot API Service'
        });
    } catch (error) {
        res.status(500).json({ message: 'Error fetching about info', error: error.message });
    }
});

router.get('/search', async (req, res) => {
    const { query, page = 1, limit = 20 } = req.query;
    
    try {
        const db = getDB();
        const collection = db.collection('files');
        const skip = (parseInt(page) - 1) * parseInt(limit);
        const limitNum = parseInt(limit);
        
        let findQuery = {};
        const trimmedQuery = query ? query.trim() : '';

        if (trimmedQuery) {
            const keywords = trimmedQuery.split(/\s+/);
            
            const keywordConditions = keywords.map(keyword => {
                const regex = new RegExp(escapeRegex(keyword), 'i');
                const condition = {
                    $or: [
                        { file_name: regex },
                        { title: regex },
                    ]
                };

                // If a keyword is a 4-digit number, assume it's a year and search the year field
                if (/^\d{4}$/.test(keyword)) {
                    condition.$or.push({ year: keyword });
                }

                return condition;
            });

            findQuery = { $and: keywordConditions };
        }
        
        const total = await collection.countDocuments(findQuery);
        const results = await collection.find(findQuery)
            .sort({ _id: -1 })
            .skip(skip)
            .limit(limitNum)
            .toArray();

        res.json({
            total,
            page: parseInt(page),
            limit: limitNum,
            results
        });
    } catch (error) {
         res.status(500).json({ message: 'Error performing search', error: error.message });
    }
});

router.get('/metadata/:id', metadataLimiter, async (req, res) => {
    const { id } = req.params;
    if (!ObjectId.isValid(id)) {
        return res.status(400).json({ message: 'Invalid file ID' });
    }
    
    const db = getDB();
    const filesCollection = db.collection('files');
    const fileId = new ObjectId(id);

    try {
        const file = await filesCollection.findOne({ _id: fileId });

        if (!file) {
            return res.status(404).json({ message: 'File not found' });
        }

        // Return cached metadata if it exists
        if (file.posterUrl) {
            return res.json({
                title: file.title,
                year: file.year,
                summary: file.summary,
                posterUrl: file.posterUrl,
            });
        }
        
        // If we already checked and found nothing, don't ask again.
        if (file.metadata_checked) {
            return res.status(404).json({ message: 'No metadata available for this file.' });
        }
        
        // --- Gemini API Call ---
        const prompt = `From the filename "${file.file_name}", identify the movie it represents. Extract the official title, the release year, a concise one-sentence plot summary, and find a publicly available URL for its poster image. Provide the response as a JSON object matching this schema. If you cannot identify a movie from the filename, all values in the JSON object should be null.`;

        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
              responseMimeType: "application/json",
              responseSchema: metadataSchema,
            },
        });
        
        const metadataText = response.text.trim();
        const metadata = JSON.parse(metadataText);

        if (metadata && metadata.posterUrl) {
            await filesCollection.updateOne({ _id: fileId }, { $set: { ...metadata, metadata_checked: true } });
            res.json(metadata);
        } else {
            // Mark as checked so we don't try again
            await filesCollection.updateOne({ _id: fileId }, { $set: { metadata_checked: true } });
            res.status(404).json({ message: 'Could not retrieve metadata from AI.' });
        }
    } catch (error) {
        console.error('Metadata generation error:', error);
        // Mark as checked even on error to prevent repeated failures
        await filesCollection.updateOne({ _id: fileId }, { $set: { metadata_checked: true } });
        res.status(500).json({ message: 'Error generating metadata', error: error.message });
    }
});

router.get('/file/:id', async (req, res) => {
    const { id } = req.params;
    if (!ObjectId.isValid(id)) {
        return res.status(400).json({ message: 'Invalid file ID' });
    }

    try {
        const db = getDB();
        const file = await db.collection('files').findOne({ _id: new ObjectId(id) });

        if (!file) {
            return res.status(404).json({ message: 'File not found' });
        }

        res.json({
            ...file,
            links: {
                download: `/api/download/${file._id}`,
                stream: `/api/stream/${file._id}`
            }
        });
    } catch (error) {
        res.status(500).json({ message: 'Error fetching file details', error: error.message });
    }
});

const serveFile = async (req, res, dispositionType) => {
    const { id } = req.params;
    if (!ObjectId.isValid(id)) {
        return res.status(400).json({ message: 'Invalid file ID' });
    }

    try {
        const db = getDB();
        const fileDoc = await db.collection('files').findOne({ _id: new ObjectId(id) });

        if (!fileDoc) {
            return res.status(404).json({ message: 'File not found' });
        }
        
        const filePath = path.join(__dirname, '..', 'uploads', id.toString());

        if (!fs.existsSync(filePath)) {
            console.error(`File not found on disk: ${filePath}. Please place file in backend/uploads/${id}`);
            return res.status(404).json({ message: 'File not found on server disk.' });
        }

        const stat = fs.statSync(filePath);
        const fileSize = stat.size;
        const range = req.headers.range;
        
        const headers = {
            'Content-Type': fileDoc.mime_type || 'application/octet-stream',
            'Accept-Ranges': 'bytes',
        };

        const sanitizedFileName = encodeURIComponent(fileDoc.file_name).replace(/['()]/g, escape).replace(/\*/g, '%2A');
        headers['Content-Disposition'] = `${dispositionType}; filename*=UTF-8''${sanitizedFileName}`;

        if (range) {
            const parts = range.replace(/bytes=/, "").split("-");
            const start = parseInt(parts[0], 10);
            const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;

            if (start >= fileSize) {
              res.status(416).send('Requested range not satisfiable\\n'+start+' >= '+fileSize);
              return;
            }
            
            const chunksize = (end - start) + 1;
            
            headers['Content-Range'] = `bytes ${start}-${end}/${fileSize}`;
            headers['Content-Length'] = chunksize;

            res.writeHead(206, headers);
            const fileStream = fs.createReadStream(filePath, { start, end });
            fileStream.pipe(res);
        } else {
            headers['Content-Length'] = fileSize;
            res.writeHead(200, headers);
            fs.createReadStream(filePath).pipe(res);
        }
    } catch (error) {
        console.error('File serving error:', error);
        res.status(500).json({ message: 'Error serving file', error: error.message });
    }
};

router.get('/download/:id', downloadLimiter, (req, res) => serveFile(req, res, 'attachment'));
router.get('/stream/:id', downloadLimiter, (req, res) => serveFile(req, res, 'inline'));


module.exports = router;