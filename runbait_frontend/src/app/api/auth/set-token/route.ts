/**
 * Next.js API Route: /api/auth/set-token
 *
 * FastAPI redirects here after a successful GitHub OAuth callback,
 * passing `?access_token=...` as a query parameter.
 *
 * This route:
 *  1. Reads the token from query params
 *  2. Sets an HttpOnly cookie on the frontend domain
 *  3. Redirects the browser to /dashboard
 *
 * Why here instead of directly in FastAPI?
 * Cookies are domain-scoped. The Next.js app runs on the frontend domain,
 * so only a Next.js route can set a cookie that the browser will accept
 * for that domain — regardless of where the backend runs.
 */
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const COOKIE_NAME = "access_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7; // 7 days in seconds

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get("access_token");

  if (!token) {
    return NextResponse.redirect(new URL("/signin?error=missing_token", request.url));
  }

  // Set the HttpOnly cookie
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: COOKIE_MAX_AGE,
    path: "/",
  });

  // Redirect to the dashboard
  return NextResponse.redirect(new URL("/dashboard", request.url));
}
