export default function TrustedBy() {
  return (
    <section className="py-20 border-t border-white/5">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-sm font-medium text-zinc-500 mb-8 tracking-widest uppercase">
          Trusted by developers
        </p>
        <div className="flex flex-wrap justify-center items-center gap-12 lg:gap-20 opacity-50 grayscale hover:grayscale-0 transition-all duration-500">
          <div className="flex items-center gap-2 text-xl font-bold text-white">
             {/* Fake tailwind logo */}
             <svg className="w-8 h-8 text-[#38bdf8]" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5C7.5 2.5 4.5 5.5 3 10c1.5-3 4-4.5 6-4.5 2 0 3.5.5 4.5 1.5.5.5 1 1 1.5 2 .5 1.5 1.5 2.5 3 2.5 4.5 0 7.5-3 9-7.5-1.5 3-4 4.5-6 4.5-2 0-3.5-.5-4.5-1.5-.5-.5-1-1-1.5-2C16.5 3.5 14.5 2.5 12 2.5z"/></svg>
             tailwindcss
          </div>
          <div className="flex items-center gap-2 text-xl font-bold text-white">
            <svg className="w-8 h-8 text-[#3ecf8e]" viewBox="0 0 24 24" fill="currentColor"><path d="M21.362 9.354H12V.396a.396.396 0 0 0-.716-.233L2.203 12.836A.396.396 0 0 0 2.52 13.5h9.48v8.957a.396.396 0 0 0 .717.233l9.082-12.673a.396.396 0 0 0-.437-.663z"/></svg>
            supabase
          </div>
          <div className="flex items-center gap-2 text-xl font-bold text-white">
            <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor"><path d="M24 22.525H0l12-21.05 12 21.05z"/></svg>
            vercel
          </div>
          <div className="flex items-center gap-2 text-xl font-bold text-white">
            <svg className="w-8 h-8 text-[#8e75ff]" viewBox="0 0 24 24" fill="currentColor"><path d="M12 24c6.627 0 12-5.373 12-12S18.627 0 12 0 0 5.373 0 12s5.373 12 12 12zM6.5 10.5h11v3h-11v-3z"/></svg>
            strapi
          </div>
          <div className="flex items-center gap-2 text-xl font-bold text-white">
             <div className="w-6 h-6 border-[4px] border-zinc-400 rounded-full flex items-center justify-center">
                <div className="w-2 h-2 bg-zinc-400 rounded-full"></div>
             </div>
             open-source
          </div>
        </div>
      </div>
    </section>
  );
}
