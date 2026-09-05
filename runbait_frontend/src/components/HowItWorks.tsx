export default function HowItWorks() {
  const steps = [
    { num: "01", title: "Connect GitHub", body: "Sign in and pick a repository. No config files." },
    { num: "02", title: "Choose a PR", body: "Select the pull request you want verified." },
    { num: "03", title: "Map the change", body: "Runbait reads the diff and finds the journeys at risk." },
    { num: "04", title: "Run the app", body: "We boot the PR head and drive a real browser." },
    { num: "05", title: "Get the report", body: "Issues, screenshots, and confidence — in the dashboard." },
  ];

  return (
    <section id="how-it-works" className="border-t border-[#1a1a1a] py-24">
      <div className="mx-auto max-w-[1200px] px-4 sm:px-6">
        <p className="text-[13px] text-[#888]">How it works</p>
        <h2 className="mt-2 max-w-xl text-[28px] font-semibold tracking-[-0.03em] text-white sm:text-[36px]">
          From pull request to evidence in a few clicks.
        </h2>

        <div className="mt-12 grid gap-px overflow-hidden rounded-xl border border-[#333] bg-[#333] sm:grid-cols-5">
          {steps.map((step) => (
            <div key={step.num} className="bg-black p-5">
              <p className="font-mono text-[11px] text-[#555]">{step.num}</p>
              <h3 className="mt-3 text-sm font-medium text-white">{step.title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-[#888]">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
