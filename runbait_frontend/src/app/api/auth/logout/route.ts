/**
 * Next.js API Route: POST /api/auth/logout
 *
 * Clears the auth cookie. Called by the logout form in the Navbar.
 */
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete("access_token");
  return NextResponse.redirect(new URL("/", process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:3000"));
}
