import { CheckCircle2, Clock, Layers, Zap } from "lucide-react";

export default function Features() {
  return (
    <section id="features" className="py-24 border-t border-white/5">
      <div className="max-w-7xl mx-auto px-6 flex flex-col gap-32">

        {/* Feature 1 */}
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-4xl font-bold tracking-tight text-white mb-8">
              Real tests. Real bugs. <br /> Real confidence.
            </h2>
            <div className="flex flex-col gap-6">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-zinc-500 shrink-0 mt-0.5" />
                <p className="text-zinc-300 font-mono text-sm leading-relaxed">AI understands your code and maps what matters.</p>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-zinc-500 shrink-0 mt-0.5" />
                <p className="text-zinc-300 font-mono text-sm leading-relaxed">Real browser execution, not mocked tests.</p>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-zinc-500 shrink-0 mt-0.5" />
                <p className="text-zinc-300 font-mono text-sm leading-relaxed">Visual & behavioral analysis with screenshots.</p>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-zinc-500 shrink-0 mt-0.5" />
                <p className="text-zinc-300 font-mono text-sm leading-relaxed">Detailed PR comments so nothing slips through.</p>
              </div>
            </div>
          </div>

          <div className="bg-[#0c0c0c] border border-white/10 rounded-xl p-6 shadow-2xl relative overflow-hidden">
            <div className="text-zinc-400 text-sm font-mono mb-4 border-b border-white/10 pb-4">Captured Issue</div>
            <div className="font-mono text-xs leading-loose">
              <div className="text-zinc-400 mb-2 border-b border-white/5 pb-2">Journey: Search & Filter</div>
              <div className="text-zinc-500 pl-4">1. User navigated to search bar</div>
              <div className="text-zinc-500 pl-4">2. User entered "S" in search bar and clicked SDK Filter</div>
              <div className="text-zinc-500 pl-4">3. Application displayed Non-SDK results too having S to begin with</div>
              <div className="text-red-400 bg-red-500/10 px-4 -mx-4 py-1 my-1 flex items-start gap-2">
                <span className="font-bold shrink-0">✕</span>
                <span>Behavioral Regression: After searching for "S", selecting the "SDKs" filter does not update the results. The filter doesn't works correctly when the search query is active.</span>
              </div>
            </div>

            <div className="mt-8 border-t border-white/10 pt-4 flex gap-4">
              <div className="flex-1">
                <div className="text-zinc-300 text-sm mb-2 font-medium">Runbait found an issue</div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-bold bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded uppercase">Medium</span>
                  <span className="text-white text-sm font-medium">Filter interactions silently failing</span>
                </div>
                <p className="text-zinc-400 text-xs leading-relaxed">Clicking filter tags does not trigger a re-fetch or UI update. The application fails silently without throwing console errors.</p>
              </div>
              <div className="w-32 bg-white rounded overflow-hidden p-1 opacity-80">
                <div className="h-16 bg-gray-100 rounded border flex items-center justify-center text-gray-300 text-[8px]">Mock</div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature 2 */}
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-4xl font-bold tracking-tight text-white mb-6">
              Built for speed and scale
            </h2>
            <p className="text-zinc-400 font-mono text-sm leading-relaxed max-w-md">
              Get results as fast as possible depending on project size.
            </p>
          </div>

          <div className="flex flex-col gap-8">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center shrink-0">
                <Clock className="w-5 h-5 text-zinc-300" />
              </div>
              <div>
                <h4 className="text-white font-medium mb-1">Async by design</h4>
                <p className="text-zinc-400 text-sm leading-relaxed font-mono">Run analyses in the background. We'll handle the heavy lifting.</p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center shrink-0">
                <Layers className="w-5 h-5 text-zinc-300" />
              </div>
              <div>
                <h4 className="text-white font-medium mb-1">Scales with your codebase</h4>
                <p className="text-zinc-400 text-sm leading-relaxed font-mono">From small apps to large monorepos.</p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg border border-white/10 bg-white/5 flex items-center justify-center shrink-0">
                <Zap className="w-5 h-5 text-zinc-300" />
              </div>
              <div>
                <h4 className="text-white font-medium mb-1">Minimal setup</h4>
                <p className="text-zinc-400 text-sm leading-relaxed font-mono">No config files. Runbait figures it out.</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
