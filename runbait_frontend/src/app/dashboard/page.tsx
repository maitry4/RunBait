import { redirect } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { getSession, logout } from "@/lib/auth";
import { Activity, Database, LayoutDashboard, Settings, LogOut, GitPullRequest, Zap } from "lucide-react";
import DashboardClient from "@/components/DashboardClient";

export const metadata = {
  title: "Dashboard — RunBait",
  description: "RunBait AI QA dashboard.",
};

export default async function DashboardPage() {
  const user = await getSession();
  if (!user) redirect("/signin");

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-white/5 bg-[#0a0a0a] flex flex-col p-4 gap-6 shrink-0">
        <div className="flex items-center gap-2 px-2 pt-2">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/logo.png" alt="Runbait logo" width={160} height={44} className="h-11 w-auto object-contain" />
          </Link>
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
        <DashboardClient user={user} />
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
      className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer transition-colors ${active
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
