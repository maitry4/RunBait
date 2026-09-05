export default function Features() {
  return (
    <section id="features" className="border-t border-[#1a1a1a] py-24">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6 space-y-24">
        <div className="grid items-start gap-12 lg:grid-cols-2">
          <div>
            <p className="text-[13px] text-[#888]">Why Runbait</p>
            <h2 className="mt-2 text-[28px] font-semibold tracking-[-0.03em] text-white sm:text-[36px]">
              Real tests. Real bugs. Real confidence.
            </h2>
            <ul className="mt-8 space-y-4 text-[14px] leading-relaxed text-[#888]">
              <li className="flex gap-3">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-[#555]" />
                AI maps the diff to the journeys a user would actually take.
              </li>
              <li className="flex gap-3">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-[#555]" />
                Playwright runs against the live app — not mocks.
              </li>
              <li className="flex gap-3">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-[#555]" />
                Screenshots and step logs are judged for visual and behavioral regressions.
              </li>
              <li className="flex gap-3">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-[#555]" />
                Results land in the dashboard while the analysis runs in the background.
              </li>
            </ul>
          </div>

          <div className="panel overflow-hidden">
            <div className="border-b border-[#1a1a1a] px-4 py-3 text-[13px] text-[#888]">Captured issue</div>
            <div className="p-4 font-mono text-[12px] leading-6">
              <p className="text-[#666]">Journey · Search &amp; Filter</p>
              <p className="mt-3 text-[#888]">1. Navigate to search</p>
              <p className="text-[#888]">2. Enter “S”, click SDKs filter</p>
              <p className="mt-3 rounded-md border border-[#333] bg-[#111] px-3 py-2 text-[#ededed]">
                Filter does not update results while a query is active.
              </p>
            </div>
            <div className="flex items-center justify-between border-t border-[#1a1a1a] px-4 py-3">
              <span className="text-[13px] text-white">Behavioral regression</span>
              <span className="badge">
                <span className="dot text-[#eab308]" />
                Medium
              </span>
            </div>
          </div>
        </div>

        <div className="grid gap-px overflow-hidden rounded-xl border border-[#333] bg-[#333] sm:grid-cols-3">
          <Fact title="Async by design" body="Analyses run in the background. Close the tab — we’ll keep going." />
          <Fact title="No suite to maintain" body="Flows are generated from the repo and ranked against the PR diff." />
          <Fact title="Minimal setup" body="Install and start commands if you need them. Otherwise, defaults." />
        </div>
      </div>
    </section>
  );
}

function Fact({ title, body }: { title: string; body: string }) {
  return (
    <div className="bg-black p-6">
      <h3 className="text-sm font-medium text-white">{title}</h3>
      <p className="mt-2 text-[13px] leading-relaxed text-[#888]">{body}</p>
    </div>
  );
}
