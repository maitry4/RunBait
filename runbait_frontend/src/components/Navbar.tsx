import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-sm border-b border-white/5">
      <div className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/logo.png" alt="Runbait logo" width={160} height={44} className="h-11 w-auto object-contain" />
          </Link>
        <div className="hidden md:flex items-center gap-6 text-sm text-zinc-400">
          <Link href="#how-it-works" className="hover:text-white transition-colors">How it works</Link>
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
        </div>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <Link href="/signin" className="text-zinc-400 hover:text-white transition-colors hidden md:block">
          Sign in
        </Link>
        <Link href="/start" className="px-4 py-2 rounded-md border border-white/20 text-white hover:bg-white/10 transition-colors">
          Get started
        </Link>
        </div>
      </div>
    </nav>
  );
}
