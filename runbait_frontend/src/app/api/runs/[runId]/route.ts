/**
 * Next.js API proxy: /api/runs/[runId]
 *
 * GET /api/runs/[runId] → proxy to FastAPI GET /api/runs/{run_id}
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

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ runId: string }> }
) {
  const authHeaders = await getAuthHeaders();
  if (!authHeaders.Authorization) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const { runId } = await params;

  const resp = await fetch(`${BACKEND_URL}/api/runs/${runId}`, {
    headers: authHeaders,
    cache: "no-store",
  });

  const data = await resp.json();
  return NextResponse.json(data, { status: resp.status });
}
