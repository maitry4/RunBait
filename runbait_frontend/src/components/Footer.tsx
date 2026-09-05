import Link from "next/link";
import { GithubIcon } from "@/components/Icons";

export default function Footer() {
  return (
    <footer className="border-t border-[#1a1a1a]">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-4">
          <div className="col-span-2 md:col-span-1">
            <p className="text-sm font-medium tracking-tight text-white">Runbait</p>
            <p className="mt-3 max-w-[200px] text-[13px] leading-relaxed text-[#888]">
              AI QA for pull requests. Catch what tests miss.
            </p>
            <a
              href="https://github.com/maitry4/RunBait"
              className="mt-4 inline-flex text-[#666] hover:text-white"
              aria-label="GitHub"
            >
              <GithubIcon className="h-4 w-4" />
            </a>
          </div>
          <div>
            <p className="text-[13px] font-medium text-white">Product</p>
            <ul className="mt-3 space-y-2 text-[13px] text-[#888]">
              <li><Link href="#features" className="hover:text-white">Features</Link></li>
              <li><Link href="#how-it-works" className="hover:text-white">How it works</Link></li>
              <li><Link href="/signin" className="hover:text-white">Dashboard</Link></li>
            </ul>
          </div>
          <div>
            <p className="text-[13px] font-medium text-white">Resources</p>
            <ul className="mt-3 space-y-2 text-[13px] text-[#888]">
              <li><a href="https://github.com/maitry4/RunBait" className="hover:text-white">GitHub</a></li>
              <li><a href="https://github.com/maitry4/RunBait#readme" className="hover:text-white">Docs</a></li>
            </ul>
          </div>
          <div>
            <p className="text-[13px] font-medium text-white">Legal</p>
            <ul className="mt-3 space-y-2 text-[13px] text-[#888]">
              <li><span className="text-[#555]">Privacy</span></li>
              <li><span className="text-[#555]">Terms</span></li>
            </ul>
          </div>
        </div>
        <div className="mt-16 flex items-center justify-between border-t border-[#1a1a1a] pt-6 text-[12px] text-[#555]">
          <p>© {new Date().getFullYear()} Runbait</p>
        </div>
      </div>
    </footer>
  );
}
