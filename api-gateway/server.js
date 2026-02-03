// api-gateway/server.js

const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const { MongoClient } = require('mongodb');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// MongoDB connection
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME || 'spamDetection';
let db;

// ML Service URL
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5000';

// Circuit Breaker Configuration
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000, monitorInterval = 10000) {
    this.state = 'CLOSED';
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.nextAttempt = Date.now();
    this.successCount = 0;
    this.monitorInterval = monitorInterval;
  }

  async call(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
      this.successCount = 0;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= 2) {
        this.state = 'CLOSED';
        console.log('Circuit breaker: HALF_OPEN -> CLOSED');
      }
    }
  }

  onFailure() {
    this.failureCount++;
    console.log(`🔴 Circuit breaker FAILURE: ${this.failureCount}/${this.threshold}`);

    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
      console.log(`Circuit breaker: OPEN (retry after ${this.timeout}ms)`);
    }
  }

  getState() {
    return this.state;
  }

  reset() {
    this.state = 'CLOSED';
    this.failureCount = 0;
    this.successCount = 0;
  }
}

const circuitBreaker = new CircuitBreaker(
  parseInt(process.env.CIRCUIT_FAILURE_THRESHOLD) || 5,
  parseInt(process.env.CIRCUIT_TIMEOUT_MS) || 60000
);

// DEBUG: Log circuit breaker configuration **DELEtE IN FINAL**
console.log('=== CIRCUIT BREAKER DEBUG ===');
console.log('CIRCUIT_FAILURE_THRESHOLD env:', process.env.CIRCUIT_FAILURE_THRESHOLD);
console.log('Parsed threshold:', parseInt(process.env.CIRCUIT_FAILURE_THRESHOLD));
console.log('Actual threshold:', circuitBreaker.threshold);
console.log('Timeout:', circuitBreaker.timeout);
console.log('Initial state:', circuitBreaker.state);
console.log('Initial failure count:', circuitBreaker.failureCount);
console.log('============================');

// Middleware
app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  const requestId = uuidv4();
  req.requestId = requestId;
  req.startTime = Date.now();
  
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - Request ID: ${requestId}`);
  
  res.on('finish', () => {
    const duration = Date.now() - req.startTime;
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - Status: ${res.statusCode} - Duration: ${duration}ms`);
  });
  
  next();
});

// Rate limiting middleware
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000,
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: { error: 'Too many requests, please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', limiter);

// Authentication Middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ 
      error: 'Access token required',
      details: 'Please login first to get an access token'
    });
  }

  // Store token for forwarding to ML service
  req.mlToken = token;
  next();
};

// Input validation middleware
const validateEmailInput = (req, res, next) => {
  const { text } = req.body;

  if (!text) {
    return res.status(400).json({ 
      error: 'Email text is required',
      details: 'Request body must contain a "text" field'
    });
  }

  if (typeof text !== 'string') {
    return res.status(400).json({ 
      error: 'Invalid input type',
      details: 'Email text must be a string'
    });
  }

  if (text.trim().length === 0) {
    return res.status(400).json({ 
      error: 'Email text cannot be empty',
      details: 'Please provide email content to analyze'
    });
  }

  if (text.length > 10000) {
    return res.status(400).json({ 
      error: 'Email text too long',
      details: 'Maximum length is 10000 characters'
    });
  }

  next();
};

// MongoDB connection
async function connectDB() {
  try {
    const client = await MongoClient.connect(MONGO_URI);
    db = client.db(DB_NAME);
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('MongoDB connection error:', error.message);
  }
}

// Health check
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    circuitBreaker: circuitBreaker.getState(),
    services: {
      database: db ? 'connected' : 'disconnected',
      mlService: 'unknown'
    }
  };

  // Check ML service health
  try {
    await axios.get(`${ML_SERVICE_URL}/health`, { timeout: 2000 });
    health.services.mlService = 'connected';
  } catch (error) {
    health.services.mlService = 'disconnected';
  }

  res.json(health);
});

// Proxy authentication to ML Service
app.post('/api/auth/login', async (req, res) => {
  const { username, password } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ 
      error: 'Username and password required' 
    });
  }

  try {
    // Forward login request to ML Service
    const response = await axios.post(
      `${ML_SERVICE_URL}/auth/login`,
      { username, password },
      { 
        timeout: 5000,
        headers: { 'Content-Type': 'application/json' }
      }
    );

    // Return token to the frontend
    res.json(response.data);
  } catch (error) {
    console.error('Login error:', error.message);
    
    if (error.response?.status === 401) {
      return res.status(401).json({ 
        error: 'Invalid credentials',
        details: 'Username or password is incorrect'
      });
    }

    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      return res.status(503).json({ 
        error: 'Authentication service unavailable',
        details: 'Could not connect to authentication service'
      });
    }

    res.status(500).json({ 
      error: 'Login failed',
      details: 'An error occurred during login'
    });
  }
});

// Main spam detection endpoint
app.post('/api/detect', authenticateToken, validateEmailInput, async (req, res) => {
  const { text } = req.body;
  const startTime = Date.now();

  try {
    // Call ML service through circuit breaker, forwarding the user's token
    const mlResponse = await circuitBreaker.call(async () => {
      const response = await axios.post(
        `${ML_SERVICE_URL}/api/ml/predict`,
        { email_text: text },
        { 
          timeout: 5000,
          headers: { 
            'Authorization': `Bearer ${req.mlToken}`,
            'Content-Type': 'application/json',
            'X-Request-ID': req.requestId
          }
        }
      );
      return response.data;
    });

    const processingTime = Date.now() - startTime;
    const detectionId = uuidv4();

    const result = {
      detectionId,
      classification: mlResponse.classification,
      confidence: mlResponse.confidence,
      timestamp: new Date().toISOString(),
      processingTime,
      requestId: req.requestId,
      user: mlResponse.user // Include user from ML service response
    };

    // Store in MongoDB
    if (db) {
      try {
        await db.collection('detections').insertOne({
          ...result,
          text,
          createdAt: new Date()
        });
      } catch (dbError) {
        console.error('Failed to store detection in DB:', dbError);
      }
    }

    res.json(result);

  } catch (error) {
    console.error('Detection error:', error.message);

    // Handle circuit breaker open
    if (error.message === 'Circuit breaker is OPEN') {
      return res.status(503).json({ 
        error: 'Service temporarily unavailable',
        details: 'The ML service is currently experiencing issues. Please try again later.',
        circuitBreaker: 'OPEN',
        retryAfter: Math.ceil((circuitBreaker.nextAttempt - Date.now()) / 1000)
      });
    }

    // Handle authentication errors (token expired or invalid)
    if (error.response?.status === 401) {
      return res.status(401).json({ 
        error: 'Authentication failed',
        details: 'Your session has expired. Please login again.',
        requiresLogin: true
      });
    }

    // Handle ML service unavailable
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      return res.status(503).json({ 
        error: 'ML service unavailable',
        details: 'Could not connect to the spam detection service. Make sure it is running on port 5000.'
      });
    }

    // Handle ML service overload (503)
    if (error.response?.status === 503) {
      return res.status(503).json({ 
        error: 'ML service busy',
        details: error.response.data?.error || 'Service is temporarily overloaded',
        retryAfter: 60
      });
    }

    res.status(500).json({ 
      error: 'Internal server error',
      details: 'An error occurred while processing your request',
      requestId: req.requestId
    });
  }
});

// Get statistics
app.get('/api/stats', authenticateToken, async (req, res) => {
  try {
    let stats = {
      totalProcessed: 0,
      spamCount: 0,
      hamCount: 0,
      dailyReports: 0
    };

    if (db) {
      const detections = await db.collection('detections').find({}).toArray();
      stats.totalProcessed = detections.length;
      stats.spamCount = detections.filter(d => d.classification === 'spam').length;
      stats.hamCount = detections.filter(d => d.classification === 'ham').length;

      const today = new Date();
      today.setHours(0, 0, 0, 0);
      stats.dailyReports = await db.collection('reports').countDocuments({
        createdAt: { $gte: today }
      });
    }

    res.json(stats);
  } catch (error) {
    console.error('Stats error:', error);
    res.status(500).json({ error: 'Failed to retrieve statistics' });
  }
});

// Circuit breaker status
app.get('/api/circuit/status', (req, res) => {
  res.json({
    status: circuitBreaker.getState(),
    failureCount: circuitBreaker.failureCount,
    threshold: circuitBreaker.threshold
  });
});

// Manual circuit breaker reset (for testing) - requires auth
app.post('/api/circuit/reset', authenticateToken, (req, res) => {
  circuitBreaker.reset();
  res.json({ 
    message: 'Circuit breaker reset',
    status: circuitBreaker.getState()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    requestId: req.requestId
  });
});

// Start server
async function startServer() {
  await connectDB();
  
  app.listen(PORT, () => {
    console.log(`API Gateway running on port ${PORT}`);
    console.log(`Circuit breaker initialized: ${circuitBreaker.getState()}`);
    console.log(`ML Service URL: ${ML_SERVICE_URL}`);
    console.log(`Using ML Service authentication (tokens forwarded)`);
  });
}

startServer();

module.exports = app;