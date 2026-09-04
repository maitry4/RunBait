/**
 * Server-side auth helpers.
 *
 * getSession()  — reads the access_token cookie and fetches /api/users/me
 * logout()      — server action: clears cookie, redirects to home
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const COOKIE_NAME = "access_token";

export interface User {
  id: string;
  github_id: number;
  github_login: string;
  name: string;
  email: string;
  avatar_url: string;
}

/**
 * Returns the currently authenticated user, or null if not logged in.
 * Safe to call in any Server Component or Server Action.
 */
export async function getSession(): Promise<User | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_NAME)?.value;
  if (!token) return null;

  try {
    const res = await fetch(`${BACKEND_URL}/api/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
      // Don't cache — always get fresh data
      cache: "no-store",
    });

    if (!res.ok) return null;
    return (await res.json()) as User;
  } catch {
    return null;
  }
}

/**
 * Server Action: clears the auth cookie and redirects to home page.
 * Usage: <form action={logout}><button type="submit">Sign out</button></form>
 */
export async function logout() {
  "use server";
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
  redirect("/");
}
