import { redirect } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { getSession, logout } from "@/lib/auth";
import DashboardClient from "@/components/DashboardClient";

export const metadata = {
  title: "Dashboard",
  description: "Runbait AI QA dashboard.",
};

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | undefined }>;
}) {
  const user = await getSession();
  if (!user) redirect("/signin");
  const params = await searchParams;
  const currentTab = params.tab || "overview";

  const nav = [
    { href: "/dashboard?tab=overview", tab: "overview", label: "Overview" },
    { href: "/dashboard?tab=repositories", tab: "repositories", label: "Repositories" },
    { href: "/dashboard?tab=analyses", tab: "analyses", label: "Analyses" },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-black md:flex-row">
      <aside className="flex shrink-0 flex-col border-b border-[#1a1a1a] md:w-[232px] md:border-b-0 md:border-r">
        <div className="flex h-12 items-center px-4">
          <Link href="/">
            <Image src="/logo.png" alt="Runbait" width={120} height={28} className="h-5 w-auto object-contain" />
          </Link>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible md:px-3 md:py-2">
          {nav.map((item) => {
            const active = currentTab === item.tab;
            return (
              <Link
                key={item.tab}
                href={item.href}
                className={`shrink-0 rounded-md px-2.5 py-1.5 text-[13px] transition-colors ${
                  active ? "bg-[#111] text-white" : "text-[#888] hover:bg-[#0a0a0a] hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto hidden border-t border-[#1a1a1a] p-3 md:block">
          <div className="flex items-center gap-2 px-1">
            {user.avatar_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.avatar_url}
                alt={user.name}
                width={22}
                height={22}
                className="rounded-full"
              />
            )}
            <div className="min-w-0">
              <p className="truncate text-[13px] text-white">{user.name}</p>
              <p className="truncate text-[11px] text-[#666]">@{user.github_login}</p>
            </div>
          </div>
          <form action={logout} className="mt-2">
            <button id="logout-btn" type="submit" className="btn btn-ghost h-8 w-full justify-start px-1 text-[13px]">
              Sign out
            </button>
          </form>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-12 items-center justify-between border-b border-[#1a1a1a] px-4 sm:px-6">
          <p className="text-[13px] text-[#888]">
            {nav.find((n) => n.tab === currentTab)?.label ?? "Overview"}
          </p>
          <form action={logout} className="md:hidden">
            <button type="submit" className="text-[13px] text-[#888] hover:text-white">
              Sign out
            </button>
          </form>
        </header>
        <main className="flex-1 overflow-auto p-4 sm:p-6">
          <DashboardClient user={user} currentTab={currentTab} />
        </main>
      </div>
    </div>
  );
}
