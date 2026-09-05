import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export const metadata = {
  title: "Log in",
  description: "Log in to Runbait with GitHub.",
};

interface Props {
  searchParams: Promise<{ error?: string }>;
}

const ERROR_MESSAGES: Record<string, string> = {
  oauth_failed: "GitHub authentication failed. Please try again.",
  github_api_failed: "Could not fetch your GitHub profile. Please try again.",
  db_error: "A database error occurred. Please try again.",
  missing_token: "Authentication error. Please try again.",
};

export default async function SignInPage({ searchParams }: Props) {
  const session = await getSession();
  if (session) redirect("/dashboard");

  const { error } = await searchParams;
  const errorMessage = error ? (ERROR_MESSAGES[error] ?? "An error occurred.") : null;

  return (
    <main className="grid min-h-screen grid-rows-[auto_1fr] bg-black">
      <header className="flex h-12 items-center border-b border-[#1a1a1a] px-4 sm:px-6">
        <Link href="/">
          <Image src="/logo.png" alt="Runbait" width={120} height={28} className="h-5 w-auto object-contain" />
        </Link>
      </header>

      <div className="flex items-center justify-center px-4">
        <div className="w-full max-w-[320px]">
          <h1 className="text-center text-[22px] font-semibold tracking-[-0.03em] text-white">
            Log in to Runbait
          </h1>
          <p className="mt-2 text-center text-[13px] text-[#888]">
            Continue with your GitHub account.
          </p>

          {errorMessage && (
            <p className="mt-6 rounded-md border border-[#333] bg-[#0a0a0a] px-3 py-2 text-[13px] text-[#f87171]">
              {errorMessage}
            </p>
          )}

          <a
            id="github-signin-btn"
            href={`${BACKEND_URL}/api/auth/github/login`}
            className="btn btn-primary mt-8 h-10 w-full text-sm"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            Continue with GitHub
          </a>

          <p className="mt-8 text-center text-[12px] leading-relaxed text-[#555]">
            By continuing, you allow Runbait to access your GitHub account.
          </p>
        </div>
      </div>
    </main>
  );
}
