# Spam Detection System - Frontend & API Gateway

Author: Landon Shumake  
Components: Frontend (React) + API Gateway (Node.js/Express) + Spam Detection(Implemented by my partners)

## Prerequisites:

Before starting, ensure you have:

- Node.js 18+ installed (https://nodejs.org/)
- Docker Desktop installed and running (https://www.docker.com/products/docker-desktop/)

Verify installations:

node --version: Should show v18.0.0 or higher
npm --version: Should show 9.0.0 or higher
docker --version: Should show Docker version

Quick Start (3 Steps):

    Step 1: Start the ML Backend (Docker)

    cd spam-detection-backend
    docker-compose up


    Wait for these messages:

    Model loaded successfully!
    Running on http://0.0.0.0:5000

**Keep this terminal running!**

    Step 2: Start the API Gateway

    Open a new terminal

    Go to proper directory:
    cd api-gateway

    Install dependencies (first time only):
    npm install


    Start the server:
    npm start

    Expected output:

    Connected to MongoDB
    API Gateway running on port 3001
    Circuit breaker initialized: CLOSED
    ML Service URL: http://localhost:5000
    Using ML Service authentication (tokens forwarded)

**Keep this terminal running!**

    Step 3: Start the Frontend

    Open a new terminal

    Go to proper directory:
    cd frontend

    Install dependencies (first time only):
    npm install

    Start the app:
    npm start

    Browser automatically opens to: http://localhost:3000

    If not, manually open: http://localhost:3000

## Testing the System

1. Login Screen should appear

   - Username: "admin"
   - Password: "spam-detection-2025"
     NOTE: (These should be auto-filled)

2. Click "Login"

3. Test Spam Detection:

   - Click "Try Spam Sample" button
   - Click "Classify Email" button
   - Should see "SPAM DETECTED" in red with ~85% confidence

4. Test Ham Detection:

   - Click "Try Ham Sample" button
   - Click "Classify Email" button
   - Should see "LEGITIMATE EMAIL" in green with ~85% confidence

5. Check Statistics:

   - Right panel should show:
     - Total Emails Processed (increments)
     - Spam Count (increments when spam detected)
     - Ham Count (increments when ham detected)

6. Upon completion of tasks:

   - Don't forget to shut down each terminal after you are done using the system, to do this use ctrl+C in each terminal.
