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
             <div className="text-zinc-400 text-sm font-mono mb-4 border-b border-white/10 pb-4">Captured Error</div>
             <div className="font-mono text-xs leading-loose">
               <div className="text-red-400 font-bold mb-2">Uncaught TypeError: Cannot read properties of null (reading 'id')</div>
               <div className="text-zinc-400 pl-4">at PaymentButton (<span className="text-blue-400">components/Payment.tsx:128:24</span>)</div>
               <div className="text-zinc-400 pl-4">at renderWithHooks (<span className="text-blue-400">react-dom.development.js:16305:18</span>)</div>
               <div className="text-zinc-400 pl-4">at mountIndeterminateComponent (<span className="text-blue-400">react-dom.development.js:20074:13</span>)</div>
               <div className="text-zinc-500 mt-2 border-t border-white/5 pt-2">
                 127 |   const session = useSession();<br/>
                 <span className="text-red-400 bg-red-500/10 block px-2 -mx-2">128 |   const userId = session.user.id; // Bug: session can be null</span>
                 129 |   return &lt;button disabled=&#123;loading&#125;&gt;Pay Now&lt;/button&gt;;
               </div>
             </div>
             
             <div className="mt-8 border-t border-white/10 pt-4 flex gap-4">
                <div className="flex-1">
                  <div className="text-zinc-300 text-sm mb-2 font-medium">Runbait found an issue</div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-bold bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded uppercase">High</span>
                    <span className="text-white text-sm font-medium">Checkout crashes on unauthenticated user</span>
                  </div>
                  <p className="text-zinc-400 text-xs leading-relaxed">Payment button throws TypeError when session is null. Users are unable to complete the order.</p>
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
              Queue multiple analyses. Get results in 30 mins to 2 hours depending on project size.
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
