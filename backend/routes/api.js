const express = require('express');
const { getDB } = require('../db');
const { ObjectId } = require('mongodb');
const rateLimit = require('express-rate-limit');
const fs = require('fs');
const path = require('path');

const router = express.Router();

// Rate limiter for download/stream endpoints
const downloadLimiter = rateLimit({
	windowMs: 15 * 60 * 1000, // 15 minutes
	max: 20, // Limit each IP to 20 requests per windowMs
	standardHeaders: true,
	legacyHeaders: false,
    message: 'Too many requests from this IP, please try again after 15 minutes',
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
    if (!query) {
        return res.status(400).json({ message: 'Search query is required' });
    }

    try {
        const db = getDB();
        const collection = db.collection('files');
        const skip = (parseInt(page) - 1) * parseInt(limit);
        const limitNum = parseInt(limit);

        const findQuery = { $text: { $search: query } };
        
        const total = await collection.countDocuments(findQuery);
        const results = await collection.find(findQuery)
            .sort({ score: { $meta: "textScore" } })
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
        console.error('Search error (might need text index):', error.message);
        // Fallback for non-Atlas environments or if text index is missing
        try {
            const db = getDB();
            const collection = db.collection('files');
            const skip = (parseInt(page) - 1) * parseInt(limit);
            const limitNum = parseInt(limit);
            const regex = new RegExp(query, 'i');
            const findQuery = { $or: [{ file_name: regex }, { caption: regex }] };
            
            const total = await collection.countDocuments(findQuery);
            const results = await collection.find(findQuery)
                .skip(skip)
                .limit(limitNum)
                .toArray();
            
            res.json({
                total,
                page: parseInt(page),
                limit: limitNum,
                results
            });
        } catch (fallbackError) {
             res.status(500).json({ message: 'Error performing search', error: fallbackError.message });
        }
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

// Generic file serving function for download and stream
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
        
        // --- IMPORTANT ---
        // This is a placeholder for actual file retrieval logic.
        // In a real application, you would use fileDoc.file_ref or _id
        // to locate the file on a filesystem, cloud storage (S3), etc.
        // For this example, we assume a local 'uploads' directory where files are named by their ID.
        // YOU MUST IMPLEMENT YOUR OWN FILE STORAGE LOGIC HERE.
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

        // Sanitize filename for header
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
