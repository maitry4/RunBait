const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function CTA() {
  return (
    <section className="border-t border-[#1a1a1a] py-24">
      <div className="mx-auto max-w-[1200px] px-4 text-center sm:px-6">
        <h2 className="text-[28px] font-semibold tracking-[-0.03em] text-white sm:text-[40px]">
          Stop guessing. Start shipping.
        </h2>
        <p className="mx-auto mt-3 max-w-md text-[15px] text-[#888]">
          Connect GitHub and run your first analysis on a real pull request.
        </p>
        <a
          href={`${BACKEND_URL}/api/auth/github/login`}
          className="btn btn-primary mt-8 h-10 px-4 text-sm"
        >
          Connect GitHub
        </a>
      </div>
    </section>
  );
}
