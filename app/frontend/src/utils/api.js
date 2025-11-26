import axios from 'axios';

// Create axios instance with base URL from environment variable
// Default to empty string (relative paths) for production
// Use REACT_APP_API_URL env variable to override (set to http://localhost:8005 for local dev)
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

