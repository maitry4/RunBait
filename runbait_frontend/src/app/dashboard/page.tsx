import { redirect } from "next/navigation";
import { getSession, logout } from "@/lib/auth";
import { Activity, Database, LayoutDashboard, Settings, LogOut, GitPullRequest, Zap } from "lucide-react";

export const metadata = {
  title: "Dashboard — RunBait",
  description: "RunBait AI QA dashboard.",
};

export default async function DashboardPage() {
  const user = await getSession();
  if (!user) redirect("/signin");

  return (
    <div className="min-h-screen bg-[#080808] text-white flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-white/5 bg-[#0a0a0a] flex flex-col p-4 gap-6 shrink-0">
        <div className="flex items-center gap-2 px-2 pt-2">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" className="text-white">
            <path d="M12 2C9.24 2 7 4.24 7 7c0 2.38 1.58 4.4 3.78 5.03L9 20h2l1-5h1l1 5h2l-1.78-7.97C17.42 11.4 19 9.38 19 7c0-2.76-2.24-5-7-5z" fill="currentColor" opacity="0.9"/>
            <circle cx="12" cy="7" r="2" fill="#0a0a0a"/>
          </svg>
          <span className="font-semibold tracking-tight text-sm">runbait</span>
        </div>

        <nav className="flex flex-col gap-1 text-sm text-zinc-400">
          <SidebarItem icon={<LayoutDashboard className="w-4 h-4" />} label="Overview" active />
          <SidebarItem icon={<Database className="w-4 h-4" />} label="Repositories" />
          <SidebarItem icon={<Activity className="w-4 h-4" />} label="Analyses" />
          <SidebarItem icon={<Settings className="w-4 h-4" />} label="Settings" />
        </nav>

        {/* User + logout at bottom */}
        <div className="mt-auto border-t border-white/5 pt-4">
          <div className="flex items-center gap-2 px-2 mb-3">
            {user.avatar_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.avatar_url}
                alt={user.name}
                width={28}
                height={28}
                className="rounded-full border border-white/10"
              />
            )}
            <div className="min-w-0">
              <p className="text-xs font-medium text-white truncate">{user.name}</p>
              <p className="text-[10px] text-zinc-500 truncate">@{user.github_login}</p>
            </div>
          </div>
          <form action={logout}>
            <button
              id="logout-btn"
              type="submit"
              className="flex w-full items-center gap-2 px-2 py-1.5 rounded text-zinc-500 hover:text-white hover:bg-white/5 transition-colors text-xs"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </form>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 p-8 overflow-auto">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-white">Overview</h1>
            <p className="text-sm text-zinc-500 mt-1">
              Welcome back, {user.name} 👋
            </p>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <StatCard label="Analyses run" value="0" icon={<Activity className="w-4 h-4 text-zinc-500" />} />
            <StatCard label="Repositories" value="0" icon={<Database className="w-4 h-4 text-zinc-500" />} />
            <StatCard label="Issues found" value="0" icon={<Zap className="w-4 h-4 text-zinc-500" />} />
          </div>

          {/* Empty state */}
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-12 text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-white/5 border border-white/10 mb-4">
              <GitPullRequest className="w-5 h-5 text-zinc-400" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">No analyses yet</h2>
            <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
              Connect a repository and open a pull request to trigger your first AI QA analysis.
            </p>
            <button
              id="connect-repo-btn"
              className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-black hover:bg-zinc-100 transition-colors"
            >
              <Database className="w-4 h-4" />
              Connect a repository
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

function SidebarItem({
  icon,
  label,
  active = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer transition-colors ${
        active
          ? "bg-white/5 text-white"
          : "hover:bg-white/5 hover:text-white"
      }`}
    >
      {icon}
      {label}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
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
