import Link from "next/link";
import Image from "next/image";
import { getSession, logout } from "@/lib/auth";

export default async function Navbar() {
  const user = await getSession();

  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-[#1a1a1a] bg-black/80 backdrop-blur-md">
      <div className="mx-auto flex h-12 max-w-[1200px] items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center">
            <Image
              src="/logo.png"
              alt="Runbait"
              width={120}
              height={28}
              className="h-5 w-auto object-contain"
              priority
            />
          </Link>
          <nav className="hidden items-center gap-5 text-[13px] text-[#888] sm:flex">
            <Link href="#how-it-works" className="hover:text-white transition-colors">
              Product
            </Link>
            <Link href="#features" className="hover:text-white transition-colors">
              Features
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3 text-[13px]">
          {user ? (
            <>
              <Link href="/dashboard" className="text-[#888] hover:text-white transition-colors hidden sm:inline">
                Dashboard
              </Link>
              <form action={logout}>
                <button id="navbar-logout-btn" type="submit" className="btn btn-secondary">
                  Sign out
                </button>
              </form>
            </>
          ) : (
            <>
              <Link href="/signin" className="text-[#888] hover:text-white transition-colors hidden sm:inline">
                Log in
              </Link>
              <Link href="/signin" className="btn btn-primary">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
