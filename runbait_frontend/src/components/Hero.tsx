import { CheckCircle2, LayoutDashboard, Database, Activity, Settings, AlertCircle } from "lucide-react";
import { GithubIcon } from "@/components/Icons";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function Hero() {
  return (
    <section className="pt-40 pb-20 px-6 max-w-7xl mx-auto grid lg:grid-cols-2 gap-16 items-center">
      {/* Left Content */}
      <div className="flex flex-col gap-8">

        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white leading-[1.1]">
          Every change <br /> deserves a real run.
        </h1>

        <p className="text-xl text-zinc-400 max-w-xl font-mono text-sm leading-relaxed">
          Runbait automatically tests the user journeys affected by your pull request on a real environment and tells you what breaks.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
          <a
            href={`${BACKEND_URL}/api/auth/github/login`}
            className="flex w-full sm:w-auto items-center justify-center gap-2 rounded-md bg-white px-6 py-3 text-black font-medium hover:bg-zinc-200 transition-colors"
          >
            Connect GitHub
          </a>
        </div>

        <div className="flex flex-wrap items-center gap-x-8 gap-y-4 pt-8 text-sm text-zinc-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-zinc-500" />
            Real browser tests
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-zinc-500" />
            Visual & behavioral analysis
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-zinc-500" />
            PR comments with evidence
          </div>
        </div>
      </div>

      {/* Right Content - Mock UI */}
      <div className="relative rounded-xl border border-white/10 bg-[#0c0c0c] overflow-hidden shadow-2xl flex h-[600px]">
        {/* Mock Sidebar */}
        <div className="w-48 border-r border-white/10 bg-[#0c0c0c] p-4 flex flex-col gap-6">
          <div className="text-white font-bold tracking-tight flex items-center gap-2 px-2">runbait</div>
          <div className="flex flex-col gap-1 text-sm text-zinc-400">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-white/5 text-white">
              <LayoutDashboard className="w-4 h-4" /> Overview
            </div>
            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded transition-colors">
              <Database className="w-4 h-4" /> Repositories
            </div>
            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded transition-colors">
              <Activity className="w-4 h-4" /> Analyses
            </div>
            <div className="flex items-center gap-2 px-2 py-1.5 hover:bg-white/5 rounded transition-colors">
              <Settings className="w-4 h-4" /> Settings
            </div>
          </div>
        </div>

        {/* Mock Main Area */}
        <div className="flex-1 p-6 flex flex-col gap-6 bg-[#0c0c0c]">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h3 className="text-white font-medium text-lg">Analysis #142</h3>
                <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">Completed</span>
              </div>
              <div className="text-zinc-500 text-sm flex items-center gap-2 mt-1">
                <GithubIcon className="w-3.5 h-3.5" /> maitry4/opensource.razorpay.com
              </div>
              <div className="text-zinc-400 text-sm mt-2 font-mono bg-white/5 px-2 py-1 rounded inline-block">
                #142 Refactor search filters
              </div>
            </div>
            <button className="flex items-center gap-2 text-xs border border-white/10 rounded px-3 py-1.5 text-zinc-300 hover:bg-white/5 transition-colors">
              <GithubIcon className="w-3.5 h-3.5" /> View on GitHub
            </button>
          </div>

          <div className="space-y-4">
            <h4 className="text-zinc-300 text-sm font-medium">Issues found</h4>
            <div className="flex gap-3">
              <div className="flex items-center gap-1.5 bg-red-500/10 border border-red-500/20 text-red-400 px-2.5 py-1 rounded text-xs font-medium">
                <AlertCircle className="w-3 h-3" /> 1 High
              </div>
              <div className="flex items-center gap-1.5 bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 px-2.5 py-1 rounded text-xs font-medium">
                <AlertCircle className="w-3 h-3" /> 1 Medium
              </div>
            </div>

            <div className="border border-white/10 rounded-lg p-4 bg-white/5 flex gap-4">
              <div className="flex-1">
                <div className="bg-red-500/20 text-red-400 text-[10px] font-bold px-1.5 py-0.5 rounded inline-block mb-2 uppercase tracking-wider">High</div>
                <h5 className="text-white font-medium mb-2">Search broken</h5>
                <p className="text-zinc-400 text-xs leading-relaxed mb-4">When search box used the filter tags don't work. Users are unable to filter results.</p>
                <div className="text-zinc-500 text-xs">Confidence: 94%</div>
                <div className="text-zinc-500 text-xs mt-1">Step 7 / 9</div>
              </div>
              <div className="w-48 bg-white rounded-md overflow-hidden p-2 flex flex-col">
                <div className="border-b pb-1 mb-2">
                  <div className="h-2 w-16 bg-gray-200 rounded"></div>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1 space-y-2">
                    <div className="h-1.5 w-full bg-gray-200 rounded"></div>
                    <div className="h-1.5 w-3/4 bg-gray-200 rounded"></div>
                    <div className="h-1.5 w-full bg-gray-200 rounded"></div>
                  </div>
                </div>
                <div className="mt-auto h-4 w-full bg-blue-100 rounded flex items-center justify-center border border-blue-200">
                  <div className="h-1 w-8 bg-blue-300 rounded"></div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-2">
            <h4 className="text-zinc-400 text-xs mb-2">Flows tested</h4>
            <div className="flex gap-2">
              <span className="text-xs border border-white/10 px-2 py-1 rounded bg-white/5 text-zinc-300">Search</span>
              <span className="text-xs border border-white/10 px-2 py-1 rounded bg-white/5 text-zinc-300">Filters</span>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
