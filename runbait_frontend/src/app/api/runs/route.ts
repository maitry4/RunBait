/**
 * Next.js API proxy: /api/runs
 *
 * Since the access_token is HttpOnly (not readable by JS), this route acts as
 * a server-side proxy. The browser hits this Next.js route, which reads the
 * HttpOnly cookie and forwards the request to FastAPI with the Bearer token.
 */
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const RAW_BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const BACKEND_URL = RAW_BACKEND_URL.endsWith("/") ? RAW_BACKEND_URL.slice(0, -1) : RAW_BACKEND_URL;

async function getAuthHeaders(): Promise<Record<string, string>> {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

// POST /api/runs → proxy to FastAPI POST /api/runs
export async function POST(request: NextRequest) {
  const authHeaders = await getAuthHeaders();
  if (!authHeaders.Authorization) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const body = await request.json();

  const resp = await fetch(`${BACKEND_URL}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}

// GET /api/runs → proxy to FastAPI GET /api/runs
export async function GET(request: NextRequest) {
  const authHeaders = await getAuthHeaders();
  if (!authHeaders.Authorization) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const resp = await fetch(`${BACKEND_URL}/api/runs`, {
    method: "GET",
    headers: { "Content-Type": "application/json", ...authHeaders },
    cache: "no-store",
  });

  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
