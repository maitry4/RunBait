import { ArrowRight } from "lucide-react";

export default function CTA() {
  return (
    <section className="py-32 border-t border-white/5">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-10 leading-tight">
          Stop guessing. <br /> Start shipping with confidence.
        </h2>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="flex w-full sm:w-auto items-center justify-center gap-2 rounded-md bg-white px-8 py-3 text-black font-medium hover:bg-zinc-200 transition-colors">
            Connect GitHub
          </button>

        </div>
      </div>
    </section>
  );
}
