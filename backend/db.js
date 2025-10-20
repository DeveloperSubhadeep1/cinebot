const { MongoClient } = require('mongodb');

let db;

async function connectDB() {
  if (db) return db;
  const client = new MongoClient(process.env.MONGO_URI);
  try {
    await client.connect();
    db = client.db();
    console.log('Connected to MongoDB');
    // It's crucial to create indexes for performance
    await db.collection('files').createIndex({ file_name: 'text', caption: 'text' });
    console.log('Text indexes ensured on "files" collection.');
    return db;
  } catch (err) {
    console.error('Failed to connect to MongoDB', err);
    process.exit(1);
  }
}

function getDB() {
  if (!db) {
    throw new Error('Database not connected!');
  }
  return db;
}

module.exports = { connectDB, getDB };
