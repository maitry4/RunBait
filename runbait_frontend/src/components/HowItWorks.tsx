import { GitPullRequest, PlayCircle, TerminalSquare, FileText, ArrowRight, Plug } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      num: 1,
      title: "Connect GitHub",
      description: "Securely connect your account and select any repository.",
      icon: <Plug className="w-8 h-8 text-zinc-400 mt-6" />
    },
    {
      num: 2,
      title: "Choose a PR",
      description: "Pick any pull request you want to verify.",
      icon: <GitPullRequest className="w-8 h-8 text-zinc-400 mt-6" />
    },
    {
      num: 3,
      title: "Run analysis",
      description: "Runbait understands the changes and tests the affected journeys.",
      icon: <PlayCircle className="w-8 h-8 text-zinc-400 mt-6" />
    },
    {
      num: 4,
      title: "We run it",
      description: "We spin up your app, run real browser tests, and capture evidence.",
      icon: <TerminalSquare className="w-8 h-8 text-zinc-400 mt-6" />
    },
    {
      num: 5,
      title: "Get report",
      description: "You get a clear report with issues, screenshots, and a PR comment.",
      icon: <FileText className="w-8 h-8 text-zinc-400 mt-6" />
    }
  ];

  return (
    <section id="how-it-works" className="py-24 border-t border-white/5">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold tracking-tight text-white mb-4">How Runbait works</h2>
          <p className="text-zinc-400 font-mono text-sm">From pull request to bug report in a few clicks.</p>
        </div>
        
        <div className="flex flex-col lg:flex-row gap-6 relative">
          {steps.map((step, index) => (
            <div key={index} className="flex-1 relative">
              <div className="bg-[#0c0c0c] border border-white/10 rounded-xl p-6 h-full flex flex-col hover:border-white/20 transition-colors">
                <div className="w-6 h-6 border border-white/20 text-zinc-400 rounded flex items-center justify-center text-xs mb-4">
                  {step.num}
                </div>
                <h3 className="text-white font-medium mb-2">{step.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed flex-1">{step.description}</p>
                {step.icon}
              </div>
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-4 top-1/2 -translate-y-1/2 text-zinc-600 z-10">
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
