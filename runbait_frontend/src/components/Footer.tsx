import { MessageSquare } from "lucide-react";
import { GithubIcon, TwitterIcon } from "@/components/Icons";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-16">
          <div className="col-span-2 lg:col-span-2">
            <Link href="/" className="text-xl font-bold tracking-tight text-white mb-4 block">
              runbait
            </Link>
            <p className="text-zinc-400 font-mono text-sm mb-6 max-w-xs">
              AI QA for pull requests.<br />
              Catch what tests miss.
            </p>
            <div className="flex gap-4 text-zinc-500">
              <a href="#" className="hover:text-white transition-colors"><GithubIcon className="w-5 h-5" /></a>
              <a href="#" className="hover:text-white transition-colors"><TwitterIcon className="w-5 h-5" /></a>
              <a href="#" className="hover:text-white transition-colors"><MessageSquare className="w-5 h-5" /></a>
            </div>
          </div>

          <div>
            <h4 className="text-white font-medium mb-4 text-sm">Product</h4>
            <ul className="space-y-3 text-sm text-zinc-400">
              <li><Link href="#" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Changelog</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-medium mb-4 text-sm">Resources</h4>
            <ul className="space-y-3 text-sm text-zinc-400">
              <li><Link href="#" className="hover:text-white transition-colors">Docs</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Blog</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Help center</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-medium mb-4 text-sm">Company</h4>
            <ul className="space-y-3 text-sm text-zinc-400">
              <li><Link href="#" className="hover:text-white transition-colors">About</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Careers</Link></li>
              <li><Link href="#" className="hover:text-white transition-colors">Contact</Link></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-zinc-500">
          <p>© 2025 Runbait Inc.</p>
          <div className="flex gap-6">
            <Link href="#" className="hover:text-white transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-white transition-colors">Terms</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
