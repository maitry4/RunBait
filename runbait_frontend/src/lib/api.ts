/**
 * Client-side API helper.
 *
 * The dashboard client code calls these functions. Because the access_token
 * is stored in an HttpOnly cookie (not accessible to JS), we proxy through
 * Next.js API routes instead of calling FastAPI directly. The Next.js routes
 * run server-side, can read the cookie, and forward requests with a proper
 * Bearer token.
 */
import axios from "axios";

// All requests go to our own Next.js API routes (same origin → no CORS issues)
const api = axios.create({
  baseURL: "/",  // relative — always same origin
  withCredentials: true,
});

export default api;
