"use client";

import { useState, useEffect } from "react";
import { Database, GitPullRequest, Zap, Play, Activity, CheckCircle, XCircle, Loader2 } from "lucide-react";
import api from "@/lib/api";

type RunStatus = "pending" | "phase1-3" | "github-actions" | "phase6" | "completed" | "failed";

interface RunData {
  id: string;
  repo: string;
  pr_number: number;
  status: RunStatus;
  is_demo: boolean;
  error?: string;
}

export default function DashboardClient({ user }: { user: any }) {
  const [activeTab, setActiveTab] = useState<"demo" | "beta">("demo");
  const [demoPR, setDemoPR] = useState("42"); // default dummy PR
  const [betaRepo, setBetaRepo] = useState("");
  const [betaPR, setBetaPR] = useState("");
  const [startCmd, setStartCmd] = useState("npm run dev");
  const [installCmd, setInstallCmd] = useState("npm install");
  const [isLoading, setIsLoading] = useState(false);
  const [currentRun, setCurrentRun] = useState<RunData | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentRun && ["pending", "phase1-3", "github-actions", "phase6"].includes(currentRun.status)) {
      interval = setInterval(async () => {
        try {
          const res = await api.get(`/api/runs/${currentRun.id}`);
          setCurrentRun(res.data);
        } catch (e) {
          console.error("Failed to poll status", e);
        }
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [currentRun]);

  const handleRun = async () => {
    setIsLoading(true);
    try {
      const payload = activeTab === "demo" ? {
        repo: "maitry4/opensource.razorpay.com",
        pr_number: parseInt(demoPR),
        is_demo: true,
        start_command: "npm run dev",
        install_command: "npm install"
      } : {
        repo: betaRepo,
        pr_number: parseInt(betaPR),
        is_demo: false,
        start_command: startCmd,
        install_command: installCmd
      };

      const res = await api.post("/api/runs", payload);
      setCurrentRun({ id: res.data.run_id, status: "pending", ...payload });
    } catch (e) {
      console.error(e);
      alert("Failed to start run.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Overview</h1>
        <p className="text-sm text-zinc-500 mt-1">Welcome back, {user.name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Analyses run" value={currentRun ? "1" : "0"} icon={<Activity className="w-4 h-4 text-zinc-500" />} />
        <StatCard label="Repositories" value="1" icon={<Database className="w-4 h-4 text-zinc-500" />} />
        <StatCard label="Issues found" value="0" icon={<Zap className="w-4 h-4 text-zinc-500" />} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Launcher panel */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
          <div className="flex border-b border-white/5">
            <button
              onClick={() => setActiveTab("demo")}
              className={`flex-1 py-3 text-sm font-medium ${activeTab === "demo" ? "bg-white/5 text-white" : "text-zinc-500 hover:text-white"}`}
            >
              Demo Repository
            </button>
            <button
              onClick={() => setActiveTab("beta")}
              className={`flex-1 py-3 text-sm font-medium ${activeTab === "beta" ? "bg-white/5 text-white" : "text-zinc-500 hover:text-white"}`}
            >
              [BETA] Any Repository
            </button>
          </div>

          <div className="p-6 space-y-4">
            {activeTab === "demo" ? (
              <>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Target Repository</label>
                  <input type="text" value="maitry4/opensource.razorpay.com" disabled className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-zinc-300" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Pull Request Number</label>
                  <input type="number" value={demoPR} onChange={e => setDemoPR(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20" />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Repository (owner/repo)</label>
                  <input type="text" placeholder="e.g. facebook/react" value={betaRepo} onChange={e => setBetaRepo(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Pull Request Number</label>
                  <input type="number" placeholder="e.g. 123" value={betaPR} onChange={e => setBetaPR(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Install Command</label>
                  <input type="text" value={installCmd} onChange={e => setInstallCmd(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-400 mb-1">Start Command</label>
                  <input type="text" value={startCmd} onChange={e => setStartCmd(e.target.value)} className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-white/20" />
                </div>
              </>
            )}

            <button
              onClick={handleRun}
              disabled={
                isLoading ||
                (!!currentRun &&
                  !["completed", "failed"].includes(currentRun.status))
              }
              className="w-full mt-4 flex items-center justify-center gap-2 rounded bg-white text-black font-semibold py-2 px-4 hover:bg-zinc-200 disabled:opacity-50 transition"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Run Analysis
            </button>
          </div>
        </div>

        {/* Status panel */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" /> Current Run
          </h2>
          {!currentRun ? (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 p-8">
              <GitPullRequest className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm text-center">No analysis running.<br />Start one from the left panel.</p>
            </div>
          ) : (
            <div className="space-y-4 flex-1">
              <p className="text-sm font-medium text-white mb-4">
                Analyzing PR #{currentRun.pr_number} on {currentRun.repo}
              </p>

              <StatusStep label="Context & Flow Discovery" active={currentRun.status === "phase1-3"} done={["github-actions", "phase6", "completed"].includes(currentRun.status)} />
              <StatusStep label="Playwright Test Execution (GitHub Actions)" active={currentRun.status === "github-actions"} done={["phase6", "completed"].includes(currentRun.status)} />
              <StatusStep label="AI Regression Analysis" active={currentRun.status === "phase6"} done={["completed"].includes(currentRun.status)} />

              {currentRun.status === "completed" && (
                <div className="mt-6 p-4 rounded bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" /> Analysis Completed Successfully!
                </div>
              )}
              {currentRun.status === "failed" && (
                <div className="mt-6 p-4 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
                  <XCircle className="w-4 h-4 shrink-0" /> Failed: {currentRun.error || "Unknown error occurred"}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusStep({ label, active, done }: { label: string, active: boolean, done: boolean }) {
  return (
    <div className={`flex items-center gap-3 text-sm ${done ? "text-zinc-300" : active ? "text-white" : "text-zinc-600"}`}>
      {done ? (
        <CheckCircle className="w-4 h-4 text-green-500" />
      ) : active ? (
        <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
      ) : (
        <div className="w-4 h-4 rounded-full border-2 border-zinc-700" />
      )}
      <span className={active ? "font-semibold" : ""}>{label}</span>
    </div>
  );
}

function StatCard({ label, value, icon }: { label: string, value: string, icon: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-zinc-500 uppercase tracking-wider">{label}</span>
        {icon}
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
