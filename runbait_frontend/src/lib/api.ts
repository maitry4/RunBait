import axios from 'axios';

const RAW_BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000';
const BACKEND_URL = RAW_BACKEND_URL.endsWith('/') ? RAW_BACKEND_URL.slice(0, -1) : RAW_BACKEND_URL;

const api = axios.create({
  baseURL: BACKEND_URL,
  withCredentials: true, // Important for cookies
});

export default api;
