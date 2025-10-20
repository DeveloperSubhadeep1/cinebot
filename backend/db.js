const { MongoClient } = require('mongodb');

let db;

async function connectDB() {
  if (db) return db;
  const client = new MongoClient(process.env.MONGO_URI);
  try {
    await client.connect();
    db = client.db();
    console.log('Connected to MongoDB');
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