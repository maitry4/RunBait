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

export default function DashboardClient({ user, currentTab = "overview" }: { user: any; currentTab?: string }) {
  const [activeTab, setActiveTab] = useState<"demo" | "beta">("demo");
  const [demoPR, setDemoPR] = useState("1");
  const [betaRepo, setBetaRepo] = useState("");
  const [betaPR, setBetaPR] = useState("");
  const [startCmd, setStartCmd] = useState("npm run dev");
  const [installCmd, setInstallCmd] = useState("npm install");
  const [isLoading, setIsLoading] = useState(false);
  const [currentRun, setCurrentRun] = useState<RunData | null>(null);
  const [allRuns, setAllRuns] = useState<any[]>([]);

  const fetchAllRuns = async () => {
    try {
      const res = await api.get("/api/runs");
      setAllRuns(res.data);
      // If no currentRun is set, maybe set the most recent one as currentRun to show something?
      if (!currentRun && res.data.length > 0) {
        const latestRun = res.data[0];
        if (["pending", "phase1-3", "github-actions", "phase6"].includes(latestRun.status)) {
          setCurrentRun(latestRun);
        }
      }
    } catch (e) {
      console.error("Failed to fetch runs", e);
    }
  };

  useEffect(() => {
    fetchAllRuns();
  }, [currentTab]); // re-fetch when tab changes

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentRun && ["pending", "phase1-3", "github-actions", "phase6"].includes(currentRun.status)) {
      interval = setInterval(async () => {
        try {
          const res = await api.get(`/api/runs/${currentRun.id}`);
          setCurrentRun(res.data);
          fetchAllRuns(); // keep list updated
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
      fetchAllRuns();
    } catch (e) {
      console.error(e);
      alert("Failed to start run.");
    } finally {
      setIsLoading(false);
    }
  };

  const uniqueRepos = Array.from(new Set(allRuns.map(r => r.repo)));

  if (currentTab === "repositories") {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Repositories</h1>
          <p className="text-sm text-zinc-500 mt-1">Repositories you have analyzed.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {uniqueRepos.length === 0 ? (
            <p className="text-zinc-500 text-sm">No repositories analyzed yet.</p>
          ) : (
            uniqueRepos.map(repo => (
              <div key={repo} className="rounded-xl border border-white/5 bg-white/[0.02] p-5 flex items-center gap-3">
                <Database className="w-6 h-6 text-cyan-400" />
                <span className="font-medium text-white truncate">{repo}</span>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  if (currentTab === "analyses") {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Analyses</h1>
          <p className="text-sm text-zinc-500 mt-1">History of all PR analyses.</p>
        </div>
        <div className="space-y-4">
          {allRuns.length === 0 ? (
            <p className="text-zinc-500 text-sm">No analyses found.</p>
          ) : (
            allRuns.map(run => (
              <div key={run.id} className="rounded-xl border border-white/5 bg-white/[0.02] p-6 flex flex-col gap-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-cyan-400" />
                    <span className="font-medium text-white">{run.repo} (PR #{run.pr_number})</span>
                  </div>
                  {run.status === "completed" && <span className="px-2 py-1 text-xs rounded bg-green-500/10 text-green-400 border border-green-500/20">Success</span>}
                  {run.status === "failed" && <span className="px-2 py-1 text-xs rounded bg-red-500/10 text-red-400 border border-red-500/20">Failed</span>}
                  {["pending", "phase1-3", "github-actions", "phase6"].includes(run.status) && <span className="px-2 py-1 text-xs rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">In Progress ({run.status})</span>}
                </div>
                {run.status === "failed" && (
                  <div className="text-sm text-red-400 bg-red-500/5 p-3 rounded border border-red-500/10">
                    {run.error || "Unknown error"}
                  </div>
                )}
                {run.status === "completed" && run.results?.report && (
                  <div className="text-sm text-zinc-300 bg-black/30 p-4 rounded border border-white/5">
                    <div className="font-semibold text-white mb-2 flex items-center gap-2">
                      {run.results.report.overall_status === "PASS" ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />}
                      Overall Status: {run.results.report.overall_status}
                    </div>
                    <p className="mb-4 whitespace-pre-wrap">{run.results.report.summary}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Overview</h1>
        <p className="text-sm text-zinc-500 mt-1">Welcome back, {user.name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Analyses run" value={allRuns.length.toString()} icon={<Activity className="w-4 h-4 text-zinc-500" />} />
        <StatCard label="Repositories" value={uniqueRepos.length.toString()} icon={<Database className="w-4 h-4 text-zinc-500" />} />
        <StatCard label="Issues found" value={allRuns.filter(r => r.status === 'failed' || (r.results?.report?.overall_status && r.results.report.overall_status !== 'PASS')).length.toString()} icon={<Zap className="w-4 h-4 text-zinc-500" />} />
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
                <div className="mt-6 p-4 rounded bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex flex-col gap-2">
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle className="w-4 h-4" /> Analysis Completed Successfully!
                  </div>
                  {/* @ts-ignore */}
                  {currentRun.results?.report?.summary && (
                    <div className="mt-2 text-zinc-300 text-xs whitespace-pre-wrap">
                      {/* @ts-ignore */}
                      {currentRun.results.report.summary.substring(0, 200)}...
                      <br/>
                      <a href="/dashboard?tab=analyses" className="text-cyan-400 underline mt-2 block">View full report in Analyses tab</a>
                    </div>
                  )}
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
