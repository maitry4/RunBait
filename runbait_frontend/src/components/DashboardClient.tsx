"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import api from "@/lib/api";

type RunStatus = "pending" | "phase1-3" | "github-actions" | "phase6" | "completed" | "failed";

interface RunData {
  id: string;
  repo: string;
  pr_number: number;
  status: RunStatus;
  is_demo: boolean;
  error?: string;
  results?: {
    report?: {
      overall_status?: string;
      summary?: string;
      verdicts?: Array<{
        flow: string;
        bug_found: boolean;
        severity?: string;
        bug_type?: string;
        description: string;
        details: string;
        evidence_step?: number | null;
        confidence?: number;
      }>;
    };
  };
}

const IN_FLIGHT: RunStatus[] = ["pending", "phase1-3", "github-actions", "phase6"];

export default function DashboardClient({
  user,
  currentTab = "overview",
}: {
  user: { name: string };
  currentTab?: string;
}) {
  const [activeTab, setActiveTab] = useState<"demo" | "beta">("demo");
  const [demoPR, setDemoPR] = useState("1");
  const [betaRepo, setBetaRepo] = useState("");
  const [betaPR, setBetaPR] = useState("");
  const [startCmd, setStartCmd] = useState("npm run dev");
  const [installCmd, setInstallCmd] = useState("npm install");
  const [isLoading, setIsLoading] = useState(false);
  const [currentRun, setCurrentRun] = useState<RunData | null>(null);
  const [allRuns, setAllRuns] = useState<RunData[]>([]);
  const [runsFilter, setRunsFilter] = useState<"all" | "completed" | "succeeded" | "failed" | "in_progress">("all");

  const fetchAllRuns = async () => {
    try {
      const res = await api.get("/api/runs");
      setAllRuns(res.data);
      setCurrentRun((prev) => {
        if (prev) return prev;
        const latest = res.data[0];
        if (latest && IN_FLIGHT.includes(latest.status)) return latest;
        return null;
      });
    } catch (e) {
      console.error("Failed to fetch runs", e);
    }
  };

  useEffect(() => {
    fetchAllRuns();
  }, [currentTab]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (currentRun && IN_FLIGHT.includes(currentRun.status)) {
      interval = setInterval(async () => {
        try {
          const res = await api.get(`/api/runs/${currentRun.id}`);
          setCurrentRun(res.data);
          fetchAllRuns();
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
      const payload =
        activeTab === "demo"
          ? {
              repo: "maitry4/opensource.razorpay.com",
              pr_number: parseInt(demoPR),
              is_demo: true,
              start_command: "npm run dev",
              install_command: "npm install",
            }
          : {
              repo: betaRepo,
              pr_number: parseInt(betaPR),
              is_demo: false,
              start_command: startCmd,
              install_command: installCmd,
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

  const uniqueRepos = Array.from(new Set(allRuns.map((r) => r.repo)));
  const issuesFound = allRuns.filter(
    (r) => r.status === "failed" || (r.results?.report?.overall_status && r.results.report.overall_status !== "PASS")
  ).length;

  if (currentTab === "repositories") {
    return (
      <div className="mx-auto max-w-4xl">
        <PageHeader title="Repositories" description="Projects you have analyzed." />
        <div className="panel mt-6 overflow-hidden">
          {uniqueRepos.length === 0 ? (
            <Empty text="No repositories yet. Run an analysis from Overview." />
          ) : (
            <ul>
              {uniqueRepos.map((repo, i) => (
                <li
                  key={repo}
                  className={`flex items-center justify-between px-4 py-3 text-[13px] ${
                    i < uniqueRepos.length - 1 ? "border-b border-[#1a1a1a]" : ""
                  }`}
                >
                  <span className="font-medium text-white">{repo}</span>
                  <span className="text-[#666]">
                    {allRuns.filter((r) => r.repo === repo).length} analyses
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    );
  }

  if (currentTab === "analyses") {
    const filteredRuns = allRuns.filter((run) => {
      if (runsFilter === "all") return true;
      if (runsFilter === "completed") return run.status === "completed";
      if (runsFilter === "succeeded") return run.status === "completed" && run.results?.report?.overall_status === "PASS";
      if (runsFilter === "failed")
        return run.status === "failed" || (run.status === "completed" && run.results?.report?.overall_status !== "PASS");
      if (runsFilter === "in_progress") return IN_FLIGHT.includes(run.status);
      return true;
    });

    const filters: Array<[typeof runsFilter, string]> = [
      ["all", "All"],
      ["completed", "Completed"],
      ["succeeded", "Ready"],
      ["failed", "Error"],
      ["in_progress", "Building"],
    ];

    return (
      <div className="mx-auto max-w-4xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <PageHeader title="Analyses" description="History of pull request runs." />
          <div className="flex gap-1 overflow-x-auto">
            {filters.map(([id, label]) => (
              <button
                key={id}
                onClick={() => setRunsFilter(id)}
                className={`h-7 shrink-0 rounded-md px-2.5 text-[12px] ${
                  runsFilter === id ? "bg-[#111] text-white" : "text-[#888] hover:text-white"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {filteredRuns.length === 0 ? (
            <div className="panel">
              <Empty text="No analyses match this filter." />
            </div>
          ) : (
            filteredRuns.map((run) => (
              <article key={run.id} className="panel overflow-hidden">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1a1a1a] px-4 py-3">
                  <div>
                    <p className="text-[13px] font-medium text-white">
                      {run.repo}{" "}
                      <span className="font-normal text-[#888]">#{run.pr_number}</span>
                    </p>
                  </div>
                  <StatusBadge status={run.status} overall={run.results?.report?.overall_status} />
                </div>

                {run.status === "failed" && (
                  <p className="border-b border-[#1a1a1a] px-4 py-3 text-[13px] text-[#f87171]">
                    {run.error || "Unknown error"}
                  </p>
                )}

                {run.status === "completed" && run.results?.report && (
                  <div className="px-4 py-4">
                    <p className="text-[13px] leading-relaxed text-[#888]">{run.results.report.summary}</p>
                    {run.results.report.verdicts?.length ? (
                      <div className="mt-4 overflow-hidden rounded-lg border border-[#333]">
                        {run.results.report.verdicts.map((verdict, idx) => (
                          <div
                            key={idx}
                            className={`px-3 py-3 ${
                              idx < (run.results?.report?.verdicts?.length ?? 0) - 1
                                ? "border-b border-[#1a1a1a]"
                                : ""
                            }`}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <p className="text-[13px] text-white">{verdict.flow}</p>
                              <span className="badge">
                                <span className={`dot ${verdict.bug_found ? "text-[#ef4444]" : "text-[#22c55e]"}`} />
                                {verdict.bug_found ? verdict.severity || "Issue" : "Ready"}
                              </span>
                            </div>
                            <p className="mt-1 text-[13px] text-[#ededed]">{verdict.description}</p>
                            <p className="mt-1 text-[12px] leading-relaxed text-[#888]">{verdict.details}</p>
                            {verdict.evidence_step != null && (
                              <p className="mt-2 font-mono text-[11px] text-[#555]">Step {verdict.evidence_step}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                )}
              </article>
            ))
          )}
        </div>
      </div>
    );
  }

  const runBusy = !!currentRun && IN_FLIGHT.includes(currentRun.status);

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Overview" description={`Welcome back, ${user.name}`} />

      <div className="mt-6 grid grid-cols-3 gap-px overflow-hidden rounded-xl border border-[#333] bg-[#333]">
        <Stat label="Analyses" value={String(allRuns.length)} />
        <Stat label="Repositories" value={String(uniqueRepos.length)} />
        <Stat label="Issues" value={String(issuesFound)} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="panel overflow-hidden">
          <div className="flex border-b border-[#1a1a1a]">
            <button
              onClick={() => setActiveTab("demo")}
              className={`flex-1 py-2.5 text-[13px] ${
                activeTab === "demo" ? "bg-[#111] text-white" : "text-[#888] hover:text-white"
              }`}
            >
              Demo
            </button>
            <button
              onClick={() => setActiveTab("beta")}
              className={`flex-1 py-2.5 text-[13px] ${
                activeTab === "beta" ? "bg-[#111] text-white" : "text-[#888] hover:text-white"
              }`}
            >
              Repository
            </button>
          </div>
          <div className="space-y-3 p-4">
            {activeTab === "demo" ? (
              <>
                <Field label="Repository">
                  <input type="text" value="maitry4/opensource.razorpay.com" disabled className="input" />
                </Field>
                <Field label="Pull request">
                  <input type="number" value={demoPR} onChange={(e) => setDemoPR(e.target.value)} className="input" />
                </Field>
              </>
            ) : (
              <>
                <Field label="Repository">
                  <input
                    type="text"
                    placeholder="owner/repo"
                    value={betaRepo}
                    onChange={(e) => setBetaRepo(e.target.value)}
                    className="input"
                  />
                </Field>
                <Field label="Pull request">
                  <input
                    type="number"
                    placeholder="142"
                    value={betaPR}
                    onChange={(e) => setBetaPR(e.target.value)}
                    className="input"
                  />
                </Field>
                <Field label="Install">
                  <input type="text" value={installCmd} onChange={(e) => setInstallCmd(e.target.value)} className="input" />
                </Field>
                <Field label="Start">
                  <input type="text" value={startCmd} onChange={(e) => setStartCmd(e.target.value)} className="input" />
                </Field>
              </>
            )}
            <button onClick={handleRun} disabled={isLoading || runBusy} className="btn btn-primary mt-2 h-9 w-full">
              {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Run analysis
            </button>
          </div>
        </div>

        <div className="panel p-4">
          <p className="text-[13px] font-medium text-white">Current run</p>
          {!currentRun ? (
            <p className="mt-8 text-center text-[13px] text-[#666]">No analysis running.</p>
          ) : (
            <div className="mt-4 space-y-3">
              <p className="text-[13px] text-[#888]">
                {currentRun.repo} <span className="text-white">#{currentRun.pr_number}</span>
              </p>
              <StatusStep
                label="Context and flow discovery"
                active={currentRun.status === "phase1-3"}
                done={["github-actions", "phase6", "completed"].includes(currentRun.status)}
              />
              <StatusStep
                label="Browser execution"
                active={currentRun.status === "github-actions"}
                done={["phase6", "completed"].includes(currentRun.status)}
              />
              <StatusStep
                label="Regression analysis"
                active={currentRun.status === "phase6"}
                done={currentRun.status === "completed"}
              />
              {currentRun.status === "completed" && (
                <div className="mt-4 border-t border-[#1a1a1a] pt-3">
                  <p className="text-[13px] text-[#888]">
                    {currentRun.results?.report?.summary?.substring(0, 180) ?? "Analysis finished."}
                    {currentRun.results?.report?.summary && currentRun.results.report.summary.length > 180 ? "…" : ""}
                  </p>
                  <a href="/dashboard?tab=analyses" className="mt-2 inline-block text-[13px] text-white underline-offset-4 hover:underline">
                    View report
                  </a>
                </div>
              )}
              {currentRun.status === "failed" && (
                <p className="mt-3 text-[13px] text-[#f87171]">{currentRun.error || "Unknown error"}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PageHeader({ title, description }: { title: string; description: string }) {
  return (
    <div>
      <h1 className="text-[22px] font-semibold tracking-[-0.03em] text-white">{title}</h1>
      <p className="mt-1 text-[13px] text-[#888]">{description}</p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-black px-4 py-4">
      <p className="text-[12px] text-[#888]">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-white">{value}</p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] text-[#888]">{label}</span>
      {children}
    </label>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="px-4 py-10 text-center text-[13px] text-[#666]">{text}</p>;
}

function StatusBadge({ status, overall }: { status: RunStatus; overall?: string }) {
  if (status === "completed" && overall === "PASS") {
    return (
      <span className="badge">
        <span className="dot text-[#22c55e]" /> Ready
      </span>
    );
  }
  if (status === "failed" || (status === "completed" && overall !== "PASS")) {
    return (
      <span className="badge">
        <span className="dot text-[#ef4444]" /> Error
      </span>
    );
  }
  if (IN_FLIGHT.includes(status)) {
    return (
      <span className="badge">
        <span className="dot text-[#eab308]" /> Building
      </span>
    );
  }
  return (
    <span className="badge">
      <span className="dot text-[#666]" /> {status}
    </span>
  );
}

function StatusStep({ label, active, done }: { label: string; active: boolean; done: boolean }) {
  return (
    <div className={`flex items-center gap-2.5 text-[13px] ${done || active ? "text-[#ededed]" : "text-[#555]"}`}>
      <span
        className={`dot ${done ? "text-[#22c55e]" : active ? "text-[#eab308]" : "text-[#333]"}`}
      />
      <span>{label}</span>
      {active ? <Loader2 className="h-3 w-3 animate-spin text-[#888]" /> : null}
    </div>
  );
}
