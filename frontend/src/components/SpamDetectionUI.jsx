import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Shield, Mail, TrendingUp, Activity, LogIn, LogOut } from 'lucide-react';

const SpamDetectionUI = () => {
  const [emailText, setEmailText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [circuitStatus, setCircuitStatus] = useState('CLOSED');
  
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('spam-detection-2025');
  const [loginError, setLoginError] = useState(null);
  const [loggingIn, setLoggingIn] = useState(false);

  const API_BASE = 'http://localhost:3001/api';

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsLoggedIn(true);
      fetchStats();
      checkCircuitStatus();
    }
  }, []);

  const handleLogin = async () => {
    setLoggingIn(true);
    setLoginError(null);

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Login failed');
      }

      localStorage.setItem('token', data.access_token);
      setIsLoggedIn(true);
      setLoginError(null);
      fetchStats();
      checkCircuitStatus();
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    setStats(null);
    setResult(null);
  };

  const fetchStats = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE}/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.status === 401) {
        handleLogout();
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const checkCircuitStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/circuit/status`);
      if (response.ok) {
        const data = await response.json();
        setCircuitStatus(data.status);
      }
    } catch (err) {
      console.error('Failed to check circuit status:', err);
    }
  };

  const handleSubmit = async () => {
  if (!emailText.trim()) {
    setError('Please enter email text');
    return;
  }

  const token = localStorage.getItem('token');
  if (!token) {
    setError('Please login first');
    return;
  }

  setLoading(true);
  setError(null);
  setResult(null);

  try {
    const response = await fetch(`${API_BASE}/detect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ text: emailText })
    });

    const data = await response.json();

    if (!response.ok) {
    
      await checkCircuitStatus();
      
      if (response.status === 401) {
        handleLogout();
        throw new Error('Session expired. Please login again.');
      } else if (response.status === 429) {
        throw new Error('Rate limit exceeded. Please try again later.');
      } else if (response.status === 503) {
        throw new Error(data.circuitBreaker === 'OPEN' 
          ? 'Service temporarily unavailable. Circuit breaker is open.'
          : 'ML service temporarily unavailable.');
      }
      throw new Error(data.error || 'Failed to classify email');
    }

    setResult(data);
    fetchStats();
    checkCircuitStatus();
  } catch (err) {
    setError(err.message);
    checkCircuitStatus();
  } finally {
    setLoading(false);
  }
};

  const sampleSpam = "CONGRATULATIONS! You've WON $1,000,000! Click here NOW to claim your prize! Limited time offer!!!";
  const sampleHam = "Hi team, just following up on our meeting yesterday. Could you please send me the project timeline when you get a chance? Thanks!";

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-8">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="flex items-center justify-center mb-6">
            <Shield className="w-12 h-12 text-indigo-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-800">Spam Detection</h1>
          </div>
          
          <p className="text-center text-gray-600 mb-6">
            Login to access the spam detection system
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter password"
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
              />
            </div>

            {loginError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start">
                <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                <p className="text-red-700 text-sm">{loginError}</p>
              </div>
            )}

            <button
              onClick={handleLogin}
              disabled={loggingIn || !username || !password}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {loggingIn ? 'Logging in...' : (
                <>
                  <LogIn className="w-5 h-5 mr-2" />
                  Login
                </>
              )}
            </button>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-900 font-semibold mb-1">Default Credentials:</p>
            <p className="text-sm text-blue-800">Username: admin</p>
            <p className="text-sm text-blue-800">Password: spam-detection-2025</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center flex-1 justify-center">
              <Shield className="w-12 h-12 text-indigo-600 mr-3" />
              <h1 className="text-4xl font-bold text-gray-800">Spam Detection System</h1>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors flex items-center"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
          <p className="text-gray-600">Distributed ML-powered email classification</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Activity className="w-5 h-5 text-gray-600 mr-2" />
              <span className="text-sm font-medium text-gray-700">Circuit Breaker Status:</span>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              circuitStatus === 'CLOSED' ? 'bg-green-100 text-green-800' :
              circuitStatus === 'HALF_OPEN' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {circuitStatus}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                <Mail className="w-6 h-6 text-indigo-600 mr-2" />
                <h2 className="text-2xl font-semibold text-gray-800">Email Classification</h2>
              </div>

              <div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter email content to analyze
                  </label>
                  <textarea
                    value={emailText}
                    onChange={(e) => setEmailText(e.target.value)}
                    className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    placeholder="Paste your email text here..."
                  />
                </div>

                <div className="flex gap-2 mb-4">
                  <button
                    onClick={() => setEmailText(sampleSpam)}
                    className="px-3 py-1 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100"
                  >
                    Try Spam Sample
                  </button>
                  <button
                    onClick={() => setEmailText(sampleHam)}
                    className="px-3 py-1 text-sm bg-green-50 text-green-700 rounded hover:bg-green-100"
                  >
                    Try Ham Sample
                  </button>
                  <button
                    onClick={() => setEmailText('')}
                    className="px-3 py-1 text-sm bg-gray-50 text-gray-700 rounded hover:bg-gray-100"
                  >
                    Clear
                  </button>
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={loading || !emailText.trim()}
                  className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Analyzing...' : 'Classify Email'}
                </button>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-red-800 font-semibold">Error</p>
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                </div>
              )}

              {result && (
                <div className={`mt-4 p-6 rounded-lg border-2 ${
                  result.classification === 'spam' 
                    ? 'bg-red-50 border-red-300' 
                    : 'bg-green-50 border-green-300'
                }`}>
                  <div className="flex items-center mb-3">
                    {result.classification === 'spam' ? (
                      <AlertCircle className="w-8 h-8 text-red-600 mr-3" />
                    ) : (
                      <CheckCircle className="w-8 h-8 text-green-600 mr-3" />
                    )}
                    <div>
                      <h3 className="text-xl font-bold">
                        {result.classification === 'spam' ? 'SPAM DETECTED' : 'LEGITIMATE EMAIL'}
                      </h3>
                      <p className="text-sm text-gray-600">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-sm text-gray-700">
                    <p><strong>Detection ID:</strong> {result.detectionId}</p>
                    <p><strong>Timestamp:</strong> {new Date(result.timestamp).toLocaleString()}</p>
                    <p><strong>Processing Time:</strong> {result.processingTime}ms</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center mb-4">
                <TrendingUp className="w-6 h-6 text-indigo-600 mr-2" />
                <h2 className="text-xl font-semibold text-gray-800">Statistics</h2>
              </div>

              {stats ? (
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Total Emails Processed</p>
                    <p className="text-3xl font-bold text-gray-800">{stats.totalProcessed}</p>
                  </div>

                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-gray-600">Spam Detected</p>
                    <p className="text-3xl font-bold text-red-600">{stats.spamCount}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {stats.totalProcessed > 0 
                        ? ((stats.spamCount / stats.totalProcessed) * 100).toFixed(1) 
                        : 0}% of total
                    </p>
                  </div>

                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600">Legitimate Emails</p>
                    <p className="text-3xl font-bold text-green-600">{stats.hamCount}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {stats.totalProcessed > 0 
                        ? ((stats.hamCount / stats.totalProcessed) * 100).toFixed(1) 
                        : 0}% of total
                    </p>
                  </div>

                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-600">Today's Reports</p>
                    <p className="text-3xl font-bold text-blue-600">{stats.dailyReports || 0}</p>
                  </div>

                  <button
                    onClick={fetchStats}
                    className="w-full py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    Refresh Stats
                  </button>
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  Loading statistics...
                </div>
              )}
            </div>

            <div className="mt-6 bg-indigo-50 rounded-lg p-4 text-sm">
              <h3 className="font-semibold text-indigo-900 mb-2">API Gateway Features</h3>
              <ul className="space-y-1 text-indigo-800">
                <li>ML Service Authentication</li>
                <li>Input Validation</li>
                <li>Rate Limiting (100/min)</li>
                <li>Circuit Breaker</li>
                <li>Request Logging</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpamDetectionUI;