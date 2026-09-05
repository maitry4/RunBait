import Link from "next/link";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function Hero() {
  return (
    <section className="relative overflow-hidden pt-28 pb-16 sm:pt-36 sm:pb-24">
      <div className="pointer-events-none absolute inset-0 grid-bg" />
      <div className="relative mx-auto max-w-[1200px] px-4 sm:px-6">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-[40px] font-semibold leading-[1.08] tracking-[-0.04em] text-white sm:text-[64px]">
            Every change deserves a real run.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-[16px] leading-relaxed text-[#888] sm:text-[18px]">
            Runbait tests the user journeys your pull request actually affects — in a real browser — and tells you what breaks.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a href={`${BACKEND_URL}/api/auth/github/login`} className="btn btn-primary h-10 px-4 text-sm">
              Connect GitHub
            </a>
            <Link href="#how-it-works" className="btn btn-secondary h-10 px-4 text-sm">
              See how it works
            </Link>
          </div>
        </div>

        <div className="mx-auto mt-16 max-w-4xl">
          <div className="overflow-hidden rounded-xl border border-[#333] bg-[#0a0a0a] shadow-[0_0_0_1px_rgba(255,255,255,0.04)]">
            <div className="flex items-center justify-between border-b border-[#1a1a1a] px-4 py-2.5">
              <div className="flex items-center gap-2">
                <span className="size-2.5 rounded-full bg-[#333]" />
                <span className="size-2.5 rounded-full bg-[#333]" />
                <span className="size-2.5 rounded-full bg-[#333]" />
              </div>
              <span className="font-mono text-[11px] text-[#666]">runbait.app/dashboard</span>
              <span className="w-12" />
            </div>
            <div className="grid grid-cols-[200px_1fr] max-sm:grid-cols-1">
              <aside className="hidden border-r border-[#1a1a1a] p-3 sm:block">
                <p className="px-2 pb-2 text-[11px] font-medium uppercase tracking-wider text-[#555]">Menu</p>
                <div className="space-y-0.5 text-[13px]">
                  <div className="rounded-md bg-[#111] px-2 py-1.5 text-white">Overview</div>
                  <div className="px-2 py-1.5 text-[#888]">Repositories</div>
                  <div className="px-2 py-1.5 text-[#888]">Analyses</div>
                </div>
              </aside>
              <div className="p-4 sm:p-5">
                <div className="mb-4 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-white">Analyses</p>
                    <p className="mt-0.5 text-[13px] text-[#888]">maitry4/opensource.razorpay.com</p>
                  </div>
                  <span className="badge">
                    <span className="dot text-[#ef4444]" />
                    1 issue
                  </span>
                </div>
                <div className="overflow-hidden rounded-lg border border-[#333]">
                  <div className="grid grid-cols-[1fr_88px_72px] border-b border-[#1a1a1a] bg-[#111] px-3 py-2 text-[11px] text-[#666]">
                    <span>Flow</span>
                    <span>Status</span>
                    <span className="text-right">Conf.</span>
                  </div>
                  <Row name="Search" status="Error" confidence="94%" error />
                  <Row name="Filters" status="Ready" confidence="—" last />
                </div>
                <p className="mt-4 text-[13px] leading-relaxed text-[#888]">
                  After searching for “S”, the SDKs filter does not update results.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Row({
  name,
  status,
  confidence,
  error,
  last,
}: {
  name: string;
  status: string;
  confidence: string;
  error?: boolean;
  last?: boolean;
}) {
  return (
    <div
      className={`grid grid-cols-[1fr_88px_72px] px-3 py-2.5 text-[13px] ${last ? "" : "border-b border-[#1a1a1a]"}`}
    >
      <span className="text-[#ededed]">{name}</span>
      <span className="flex items-center gap-1.5 text-[#888]">
        <span className={`dot ${error ? "text-[#ef4444]" : "text-[#22c55e]"}`} />
        {status}
      </span>
      <span className="text-right font-mono text-[12px] text-[#888]">{confidence}</span>
    </div>
  );
}
