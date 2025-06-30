// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

print('Starting MongoDB initialization...');

// Switch to the ego_ai_db database
db = db.getSiblingDB('ego_ai_db');

// Create a user for the ego_ai_db database with read/write permissions
db.createUser({
  user: 'ego_mongo_user',
  pwd: 'ego_mongo_pass',
  roles: [
    {
      role: 'readWrite',
      db: 'ego_ai_db'
    }
  ]
});

// Create the chat_history collection (optional, but helps with initialization)
db.createCollection('chat_history');

print('MongoDB initialization completed successfully!');
