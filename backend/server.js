require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { connectDB } = require('./db');
const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors({ origin: process.env.FRONTEND_ORIGIN }));
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());

// Routes
app.use('/api', apiRoutes);

// Start server
async function startServer() {
  try {
    await connectDB();
    app.listen(PORT, () => {
      console.log(`Server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
  }
}

startServer();
